import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

class Database:
    client: AsyncIOMotorClient = None

async def connect_to_mongo():
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:adminpassword@localhost:27017/martillo_de_thor?authSource=admin")
    Database.client = AsyncIOMotorClient(mongodb_url)
    Database.db = Database.client.get_database()

async def close_mongo_connection():
    Database.client.close()

async def get_user(username: str):
    user = await Database.db.users.find_one({"username": username})
    if user:
        user['_id'] = str(user['_id'])
        user['role'] = user.get('role', 'Usuario')  # Valor predeterminado si no existe
    return user

async def create_user_db(user_data: dict):
    if 'role' not in user_data:
        user_data['role'] = 'Usuario'  # Rol predeterminado
    try:
        logging.info(f"Intentando crear usuario: {user_data['username']}")
        result = await Database.db.users.insert_one(user_data)
        logging.info(f"Usuario creado con ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logging.error(f"Error al crear usuario: {str(e)}")
        return None

async def delete_user(username: str):
    result = await Database.db.users.delete_one({"username": username})
    return result.deleted_count
