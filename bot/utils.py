import logging
from bson import ObjectId
from typing import Optional, Dict, Any
import requests
from telegram import Update, Bot
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database import get_collection

from config import COC_API_URL, COC_HEADERS, TELEGRAM_TOKEN, ALLOWED_GROUP_ID, ALERTAS_TOPIC_ID, MONGO_DB_BUILDERS_COLLECTION

logger = logging.getLogger(__name__)
TELEGRAM_BOT = Bot(token=TELEGRAM_TOKEN)

# API Helpers

async def fetch_data(url: str):
    try:
        logger.info(url)
        response = requests.get(url)
        return response
    except Exception as e:
        logger.error(f"Error consulta http: {e}")
        return None


async def fetch_coc_data(endpoint: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(
            f"{COC_API_URL}{endpoint}",
            headers=COC_HEADERS,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error API COC ({endpoint}): {e}")
        return None


# Builder Helpers
def load_constructores() -> dict:
    try:
        collection = get_collection(MONGO_DB_BUILDERS_COLLECTION)
        result = {}
        for doc in collection.find():
            result[str(doc["_id"])] = doc["data"]
        return result
    except Exception as e:
        logger.error(f"Error cargando constructores: {e}")
        return {}


def save_constructores(data: dict) -> bool:
    try:
        collection = get_collection(MONGO_DB_BUILDERS_COLLECTION)
        # Eliminamos todos los documentos existentes (simulamos el overwrite del JSON)
        collection.delete_many({})

        # Insertamos los nuevos datos
        for user_id, user_data in data.items():
            collection.insert_one({
                "_id": ObjectId(user_id) if len(user_id) == 24 else user_id,
                "data": user_data
            })
        return True
    except Exception as e:
        logger.error(f"Error guardando constructores: {e}")
        return False


# Format Helpers
def format_time_left(end_time: str) -> str:
    if not end_time:
        return "tiempo desconocido"

    end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    now = datetime.now(end.tzinfo)
    delta = end - now

    if delta.total_seconds() <= 0:
        return "¡AHORA MISMO!"

    hours, remainder = divmod(delta.total_seconds(), 3600)
    minutes = remainder // 60
    return f"{int(hours)}h {int(minutes)}m" if hours else f"{int(minutes)}m"


def parse_duration(duration_str: str) -> timedelta:
    days = hours = minutes = 0
    remaining = duration_str.lower()

    if 'd' in remaining:
        d_idx = remaining.index('d')
        days = int(remaining[:d_idx])
        remaining = remaining[d_idx + 1:]

    if 'h' in remaining:
        h_idx = remaining.index('h')
        hours = int(remaining[:h_idx])
        remaining = remaining[h_idx + 1:]

    if 'm' in remaining:
        m_idx = remaining.index('m')
        minutes = int(remaining[:m_idx])

    return timedelta(days=days, hours=hours, minutes=minutes)


# Telegram Helpers
async def send_to_topic(text: str, update: Optional[Update] = None):
    try:
        if update.effective_chat.id != ALLOWED_GROUP_ID:
            await update.message.reply_text("Usted no está autorizado para consumir información de Friends.")
            return

        await TELEGRAM_BOT.send_message(
            chat_id=ALLOWED_GROUP_ID,
            text=escape_markdown(text),
            message_thread_id=ALERTAS_TOPIC_ID,
            parse_mode="MarkdownV2"
        )
        return True
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        if update:
            await update.message.reply_text("⚠️ Error al enviar al tópico")
        return False


async def send_to_topic_html(text: str, update: Optional[Update] = None):
    """Envía mensaje al tópico designado"""
    try:
        chat_id = update.effective_chat.id if update else ALLOWED_GROUP_ID
        await TELEGRAM_BOT.send_message(
            chat_id=chat_id,
            text=text,
            message_thread_id=ALERTAS_TOPIC_ID,
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        if update:
            await update.message.reply_text("⚠️ Error al enviar al tópico")
        return False


def escape_markdown(text: str) -> str:
    escape_chars = '_*[]()~`>#+-=|{}.!'
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            result.append(f'\\{text[i + 1]}')
            i += 2
        elif text[i] in escape_chars:
            result.append(f'\\{text[i]}')
            i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


async def send_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = ""):
    """Envía/actualiza un mensaje de progreso animado"""
    try:
        if not hasattr(context, 'progress_message'):
            context.progress_message = await update.message.reply_text(f"🔄 {message} ▰▱▱▱▱ 0%")
        else:
            await context.progress_message.edit_text(f"🔄 {message} ▰▱▱▱▱ 0%")
    except Exception as e:
        logger.error(f"Error en progreso: {e}")


async def update_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, percentage: int, message: str = ""):
    """Actualiza la barra de progreso"""
    if not hasattr(context, 'progress_message'):
        return

    bars = "▰" * (percentage // 20) + "▱" * (5 - percentage // 20)
    try:
        await context.progress_message.edit_text(f"🔄 {message} {bars} {percentage}%")
    except Exception as e:
        logger.error(f"Error actualizando progreso: {e}")


async def delete_progress(context: ContextTypes.DEFAULT_TYPE):
    """Elimina el mensaje de progreso"""
    if hasattr(context, 'progress_message'):
        try:
            await context.progress_message.delete()
        except:
            pass
        del context.progress_message
