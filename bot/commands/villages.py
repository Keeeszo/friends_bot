from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from data.dao.villages_dao import VillagesDAO
from bot.utils import send_to_topic, send_to_topic_html
import logging

from config import BOT_OWNER_USERNAME

logger = logging.getLogger(__name__)

# Estados para la conversación de agregar aldea
CHOOSING_TH = 0
CHOOSING_TYPE = 1
ENTERING_URL = 2
ENTERING_DESCRIPTION = 3

# Tipos de aldeas disponibles
VILLAGE_TYPES = ["farming", "guerra", "todo"]

async def aldeas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de aldeas disponibles"""
    dao = VillagesDAO()
    villages = await dao.get_all_villages()
    
    if not villages:
        await send_to_topic("No hay aldeas registradas aún.", update)
        return
    
    # Agrupar aldeas por TH
    villages_by_th = {}
    for village in villages:
        if village.get("th_level") not in villages_by_th:
            villages_by_th[village["th_level"]] = []
        villages_by_th[village["th_level"]].append(village)
    
    # Construir mensaje
    message = f"Hola {update.effective_user.first_name}, te comparto las mejores aldeas actualizadas por el líder del clan:\n\n"
    
    for th_level in sorted(villages_by_th.keys()):
        message += f"TH{th_level}:\n"
        for village in villages_by_th[th_level]:
            message += f"<a href='{village['url']}'>{village['type'].capitalize()}</a> - {village['description']}\n"
        message += "\n"
    
    await send_to_topic_html(message, update)

async def agregar_aldea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de agregar una nueva aldea"""
    dao = VillagesDAO()
    
    # Obtener el username del usuario
    username = update.effective_user.username
    if not username:
        await send_to_topic("⚠️ Necesitas tener un nombre de usuario (@username) configurado en Telegram para usar este comando.", update)
        return ConversationHandler.END
    
    # Verificar si el usuario es el líder del clan
    if not username.lower() == BOT_OWNER_USERNAME.lower():
        await send_to_topic("⚠️ Solo el líder del clan puede agregar aldeas.", update)
        return ConversationHandler.END
    
    # Crear teclado para seleccionar TH
    keyboard = []
    for th in range(5, 16):  # TH5 hasta TH16
        keyboard.append([InlineKeyboardButton(f"TH{th}", callback_data=f"th_{th}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Selecciona el nivel de ayuntamiento:",
        reply_markup=reply_markup
    )
    
    return CHOOSING_TH

async def th_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección del TH"""
    query = update.callback_query
    await query.answer()
    
    th_level = int(query.data.split("_")[1])
    context.user_data["th_level"] = th_level
    
    # Crear teclado para seleccionar tipo
    keyboard = []
    for vtype in VILLAGE_TYPES:
        keyboard.append([InlineKeyboardButton(vtype.capitalize(), callback_data=f"type_{vtype}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Has seleccionado TH{th_level}. Ahora selecciona el tipo de aldea:",
        reply_markup=reply_markup
    )
    
    return CHOOSING_TYPE

async def type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección del tipo de aldea"""
    query = update.callback_query
    await query.answer()
    
    village_type = query.data.split("_")[1]
    context.user_data["village_type"] = village_type
    
    await query.edit_message_text(
        f"Has seleccionado aldea de tipo {village_type.capitalize()}.\n\n"
        "Por favor, envía la URL de la aldea (debe comenzar con http:// o https://):"
    )
    
    return ENTERING_URL

async def url_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la recepción de la URL"""
    url = update.message.text
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text(
            "⚠️ Por favor, envía una URL válida que comience con http:// o https://"
        )
        return ENTERING_URL
    
    context.user_data["url"] = url
    await update.message.reply_text(
        f"URL recibida: {url}\n\n"
        "Por favor, envía una descripción breve de la aldea:"
    )
    
    return ENTERING_DESCRIPTION

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la recepción de la descripción y guarda la aldea"""
    description = update.message.text
    dao = VillagesDAO()
    
    success = await dao.add_village(
        th_level=context.user_data["th_level"],
        village_type=context.user_data["village_type"],
        url=context.user_data["url"],
        description=description,
        added_by=update.effective_user.username
    )
    
    if success:
        await send_to_topic(
            f"✅ Nueva aldea agregada exitosamente:\n"
            f"TH{context.user_data['th_level']} - {context.user_data['village_type'].capitalize()}\n"
            f"Descripción: {description}",
            update
        )
    else:
        await send_to_topic("⚠️ Error al agregar la aldea. Por favor, intenta nuevamente.", update)
    
    # Limpiar datos de la conversación
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la conversación"""
    context.user_data.clear()
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END 