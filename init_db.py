import asyncio
import os
import argparse
from database import connect_to_mongo, close_mongo_connection, create_user, get_user, delete_user

async def init_db(force=False):
    await connect_to_mongo()
    
    # Verificar si el usuario "thor" ya existe
    existing_user = await get_user("thor")
    
    if existing_user and force:
        await delete_user("thor")
        print("Usuario 'thor' eliminado para su recreación.")
        existing_user = None

    if not existing_user:
        user_data = {
            "username": "thor",
            "full_name": "Thor Odinson",
            "email": "thor@asgard.com",
            "hashed_password": "mjolnir123",
            "disabled": False,
            "role": "Admin"  # Añade esta línea
        }
        user_id = await create_user(user_data)
        print(f"Usuario creado con ID: {user_id}")
    elif not force:
        print("El usuario 'thor' ya existe. No se creará un nuevo usuario.")
    
    await close_mongo_connection()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicializar la base de datos")
    parser.add_argument("--force", action="store_true", help="Forzar la actualización del usuario")
    args = parser.parse_args()

    asyncio.run(init_db(args.force))
