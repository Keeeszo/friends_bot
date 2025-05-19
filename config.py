import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID"))
ALERTAS_TOPIC_ID = int(os.getenv("ALERTAS_TOPIC_ID"))

# Clash of Clans
COC_API_URL = "https://api.clashofclans.com/v1"
COC_API_KEY = os.getenv("COC_API_KEY")
COC_HEADERS = {"Authorization": f"Bearer {COC_API_KEY}"}
CLAN_TAG = os.getenv("CLAN_TAG").replace("#", "%23")

# Rutas de archivos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

MONGO_DB_URI = os.getenv("MONGO_DB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_DB_BUILDERS_COLLECTION = os.getenv("MONGO_DB_BUILDERS_COLLECTION")
