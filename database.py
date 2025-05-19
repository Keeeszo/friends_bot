from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import MONGO_DB_URI, MONGO_DB_NAME
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = MongoClient(MONGO_DB_URI)
            cls._instance.db = cls._instance.client[MONGO_DB_NAME]
        return cls._instance

    def get_collection(self, name: str):
        return self.db[name]

    def close(self):
        self.client.close()


# Helper para acceder fácilmente a las colecciones
def get_db():
    return MongoDB().db


def get_collection(collection_name: str):
    return MongoDB().get_collection(collection_name)