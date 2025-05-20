from typing import Dict, List, Optional
from datetime import datetime
from database import get_collection
from pymongo.errors import PyMongoError
import logging
from config import MONGO_DB_BUILDERS_COLLECTION
import uuid

logger = logging.getLogger(__name__)


class BuildersDAO:
    def __init__(self):
        self.collection = get_collection(MONGO_DB_BUILDERS_COLLECTION)

    async def get_user_builders(self, user_id: str) -> Optional[Dict]:
        """Obtiene todos los constructores de un usuario"""
        try:
            result = self.collection.find_one({"_id": user_id})
            return result["data"] if result else None
        except PyMongoError as e:
            logger.error(f"Error obteniendo constructores: {e}")
            return None

    async def add_builder_account(
            self,
            user_id: str,
            username: str,
            player_tag: str,
            player_data: Dict,
            builder_count: int
    ) -> bool:
        """Añade una nueva cuenta de constructor a un usuario"""
        try:
            account_data = {
                "name": player_data["name"],
                "max_builders": builder_count,
                "active_builds": [],
                "registered_at": datetime.now().isoformat(),
                "th_level": player_data["townHallLevel"]
            }

            result = self.collection.update_one(
                {"_id": user_id},
                {"$set": {
                    f"data.accounts.{player_tag}": account_data,
                    "data.username": username
                }},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except PyMongoError as e:
            logger.error(f"Error añadiendo cuenta de constructor: {e}")
            return False

    async def add_builder_task(
            self,
            user_id: str,
            player_tag: str,
            task_data: Dict
    ) -> bool:
        """Añade una nueva tarea de construcción"""
        try:
            # Añadir ID único a la tarea
            task_data["task_id"] = str(uuid.uuid4())
            
            result = self.collection.update_one(
                {"_id": user_id, f"data.accounts.{player_tag}": {"$exists": True}},
                {"$push": {f"data.accounts.{player_tag}.active_builds": task_data}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error añadiendo tarea de construcción: {e}")
            return False

    async def cancel_builder_task(
            self,
            user_id: str,
            player_tag: str,
            task_id: str
    ) -> bool:
        """Cancela una tarea de construcción usando su ID único"""
        try:
            result = self.collection.update_one(
                {"_id": user_id},
                {"$pull": {
                    f"data.accounts.{player_tag}.active_builds": {
                        "task_id": task_id
                    }
                }}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error cancelando tarea de construcción: {e}")
            return False

    async def is_player_registered(self, player_tag: str) -> tuple:
        """Verifica si un jugador ya está registrado y devuelve (estado, dueño)"""
        try:
            result = self.collection.find_one(
                {f"data.accounts.{player_tag}": {"$exists": True}},
                {"_id": 1, "data.username": 1}
            )
            if result:
                return (True, result.get("data", {}).get("username", "usuario desconocido"))
            return (False, None)
        except PyMongoError as e:
            logger.error(f"Error verificando jugador registrado: {e}")
            return (False, None)