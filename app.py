# Aplicación web basada en FastAPI para crear una web para un clan del videojuego Throne & Liberty

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import uvicorn


app = FastAPI(title="Martillo de Thor - Clan de Throne & Liberty")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Simulación de base de datos de usuarios
fake_users_db = {
    "thor": {
        "username": "thor",
        "full_name": "Thor Odinson",
        "email": "thor@asgard.com",
        "hashed_password": "mjolnir123",
        "disabled": False,
    }
}

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Nombre de usuario incorrecto")
    user = UserInDB(**user_dict)
    if form_data.password != user.hashed_password:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/info-publica")
async def info_publica(request: Request):
    info = {
        "server": "---",
        "enfoque": "PvE (evolucionando a PvP)",
        "filosofia": "Diversión y apoyo mutuo",
        "objetivo": "Progresar juntos y alcanzar las metas del clan"
    }
    return templates.TemplateResponse("info_publica.html", {"request": request, "info": info})

@app.get("/area-miembros")
async def area_miembros(request: Request):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("bearer "):
        return RedirectResponse(url="/login")
    username = token.split()[1]
    user = fake_users_db.get(username)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("area_miembros.html", {"request": request, "user": user})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user_dict = fake_users_db.get(username)
    if not user_dict:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuario incorrecto"})
    user = UserInDB(**user_dict)
    if password != user.hashed_password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Contraseña incorrecta"})
    response = RedirectResponse(url="/area-miembros", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"bearer {user.username}", httponly=True)
    return response

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

templates = Jinja2Templates(directory="templates")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
