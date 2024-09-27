# Aplicación web basada en FastAPI para crear una web para un clan del videojuego Throne & Liberty

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import uvicorn
from database import connect_to_mongo, close_mongo_connection, get_user, create_user_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Martillo de Thor - Clan de Throne & Liberty", lifespan=lifespan)

# Añade esta línea para montar los archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str = 'Usuario'

class UserInDB(User):
    hashed_password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Reemplaza las llamadas a get_user con la versión de database.py
from database import get_user

def fake_decode_token(token):
    user = get_user(token + "fakedecoded")
    return User(
        username=user['username'],
        email=user['email'],
        full_name=user['full_name'],
        role=user['role']
    )

# Optimización 1: Usar dependencias para la autenticación
async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    username = token.split()[1]
    user = await get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return User(**user)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Nombre de usuario incorrecto")
    if form_data.password != user['hashed_password']:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    return {"access_token": user['username'], "token_type": "bearer"}

@app.get("/")
async def root(request: Request):
    info = {
        "Únete a la aventura": "Explora el vasto mundo de Throne & Liberty con compañeros leales.",
        "Crece con nosotros": "Mejora tus habilidades y equipo en un ambiente de apoyo mutuo.",
        "Conquista juntos": "Participa en emocionantes batallas PvE y PvP con estrategias de equipo."
    }
    return templates.TemplateResponse("index.html", {"request": request, "info": info})

@app.get("/info-publica")
async def info_publica(request: Request):
    info = {
        "server": "---",
        "enfoque": "PvE (evolucionando a PvP)",
        "filosofia": "Diversión y apoyo mutuo",
        "objetivo": "Progresar juntos y alcanzar las metas del clan"
    }
    return templates.TemplateResponse("info_publica.html", {"request": request, "info": info})

# Optimización 3: Usar la dependencia get_current_user en las rutas protegidas
@app.get("/area-miembros")
async def area_miembros(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("area_miembros.html", {"request": request, "user": current_user})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def authlogin(request: Request, username: str = Form(...), password: str = Form(...)):
    user = await get_user(username)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuario incorrecto"})
    if password != user['hashed_password']:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Contraseña incorrecta"})
    response = RedirectResponse(url="/area-miembros", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"bearer {user['username']}", httponly=True)
    return response

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

templates = Jinja2Templates(directory="templates")

# Optimización 2: Simplificar el manejo de roles
def role_required(allowed_roles: list):
    async def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esta página")
        return current_user
    return check_role

@app.get("/test")
async def test(request: Request):
    print("Hello World")
    return {"message": "Hello World"}

@app.get("/admin-area")
async def admin_area(request: Request, current_user: User = Depends(role_required(["Admin"]))):
    return templates.TemplateResponse("admin_area.html", {"request": request, "user": current_user})

@app.get("/admin/create-user")
async def create_user_page(request: Request, current_user: User = Depends(role_required(["Admin"]))):
    return templates.TemplateResponse("create_user.html", {"request": request, "user": current_user})

@app.get("/admin/edit-user")
async def edit_user_page(request: Request, current_user: User = Depends(role_required(["Admin"]))):
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": current_user})

@app.post("/admin/create-user")
async def create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user: User = Depends(role_required(["Admin"]))
):
    # Primero, verificamos si el usuario ya existe
    existing_user = await get_user(username)
    if existing_user:
        return templates.TemplateResponse("create_user.html", {
            "request": request,
            "user": current_user,
            "error": f"El usuario '{username}' ya existe."
        })

    user_data = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "hashed_password": password,  # Nota: En una aplicación real, deberías hashear la contraseña
        "role": role,
        "disabled": False
    }
    try:
        user_id = await create_user_db(user_data)
        if user_id:
            return templates.TemplateResponse("create_user.html", {
                "request": request,
                "user": current_user,
                "message": f"Usuario creado con éxito. ID: {user_id}"
            })
        else:
            raise Exception("No se pudo crear el usuario")
    except Exception as e:
        return templates.TemplateResponse("create_user.html", {
            "request": request,
            "user": current_user,
            "error": f"Error al crear el usuario: {str(e)}"
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
