import asyncio
import os
from database import connect_to_mongo, close_mongo_connection, create_user

async def init_db():
    await connect_to_mongo()
    user_data = {
        "username": "thor",
        "full_name": "Thor Odinson",
        "email": "thor@asgard.com",
        "hashed_password": "mjolnir123",
        "disabled": False
    }
    user_id = await create_user(user_data)
    print(f"Usuario creado con ID: {user_id}")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(init_db())
