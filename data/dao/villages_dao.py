from typing import Dict, List, Optional
from datetime import datetime
from database import get_collection
from pymongo.errors import PyMongoError
import logging
from config import BOT_OWNER_USERNAME

logger = logging.getLogger(__name__)

class VillagesDAO:
    def __init__(self):
        self.collection = get_collection("villages")

    async def get_all_villages(self) -> List[Dict]:
        """Obtiene todas las aldeas ordenadas por TH y tipo"""
        try:
            return list(self.collection.find().sort([
                ("th_level", 1),
                ("type", 1)
            ]))
        except PyMongoError as e:
            logger.error(f"Error obteniendo aldeas: {e}")
            return []

    async def add_village(
            self,
            th_level: int,
            village_type: str,
            url: str,
            description: str,
            added_by: str
    ) -> bool:
        """Añade una nueva aldea"""
        try:
            village_data = {
                "th_level": th_level,
                "type": village_type,
                "url": url,
                "description": description,
                "added_by": added_by,
                "added_at": datetime.now().isoformat()
            }
            
            result = self.collection.insert_one(village_data)
            return result.inserted_id is not None
        except PyMongoError as e:
            logger.error(f"Error añadiendo aldea: {e}")
            return False