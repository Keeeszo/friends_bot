from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from data.dao.builders_dao import BuildersDAO

logger = logging.getLogger(__name__)

from bot.utils import (
    parse_duration,
    format_time_left,
    fetch_coc_data
)
from config import CLAN_TAG

# Instancia global del DAO
builders_dao = BuildersDAO()

def get_main_menu_keyboard():
    """Retorna el teclado principal de constructores"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Añadir Cuenta", callback_data="builders_add"),
            InlineKeyboardButton("🏗️ Nueva Construcción", callback_data="builders_build")
        ],
        [
            InlineKeyboardButton("📋 Listar Cuentas agregadas", callback_data="builders_list"),
            InlineKeyboardButton("❌ Cancelar Construcción", callback_data="builders_cancel")
        ],
        [
            InlineKeyboardButton("🚪 Salir", callback_data="builders_exit")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def constructores_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador principal para comandos de constructores"""
    # Verificar si el comando se ejecuta en un chat directo
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "Este comando solo está disponible por chat directo, escríbeme 😊"
        )
        return

    # Verificar si ya hay un menú activo
    if context.user_data.get('active_menu'):
        await update.message.reply_text(
            "⚠️ Ya tienes un menú de constructores activo.\n"
            "Usa el botón 'Salir' para cerrar el menú actual.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Marcar el menú como activo
    context.user_data['active_menu'] = True
    
    # Enviar el mensaje y guardar su ID para poder eliminarlo después
    message = await update.message.reply_text(
        "🔨 *Gestión de Constructores* 🔨\n\n"
        "Selecciona una opción del menú:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    # Guardar el ID del mensaje para poder eliminarlo después
    context.user_data['menu_message_id'] = message.message_id
    
    # Eliminar el mensaje del comando
    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Error al eliminar mensaje del comando: {e}")

async def handle_builder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de callbacks de los botones de constructores"""
    query = update.callback_query
    await query.answer()
    
    # Verificar que el usuario que presionó el botón es el mismo que abrió el menú
    if not context.user_data.get('active_menu'):
        await query.message.edit_text(
            "⚠️ Este menú ya no está activo.\n"
            "Usa el comando /constructores para abrir un nuevo menú.",
            reply_markup=None
        )
        return
    
    if query.data == "builders_menu":
        # Volver al menú principal
        await query.message.edit_text(
            "🔨 *Gestión de Constructores* 🔨\n\n"
            "Selecciona una opción del menú:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    if query.data == "builders_exit":
        # Cerrar el menú
        await query.message.edit_text(
            "👋 *Menú de constructores cerrado*\n\n"
            "Usa /constructores para abrir el menú nuevamente.",
            reply_markup=None,
            parse_mode="Markdown"
        )
        context.user_data.clear()
        return
    
    action = query.data.split('_')[1]
    
    if action == "add":
        await constructores_add(update, context)
    elif action == "build":
        await constructores_build(update, context)
    elif action == "list":
        await constructores_list(update, context)
    elif action == "cancel":
        await constructores_cancel(update, context)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de mensajes de texto para constructores"""
    # Verificar que el usuario que envía el mensaje es el mismo que tiene el menú activo
    if not context.user_data.get('active_menu'):
        return

    # Obtener el mensaje del menú para actualizarlo
    menu_message_id = context.user_data.get('menu_message_id')
    if not menu_message_id:
        return

    # Procesar el mensaje según el estado actual
    if context.user_data.get('builder_state') == 'waiting_tag':
        await constructores_add(update, context, menu_message_id)
    elif context.user_data.get('builder_state') == 'waiting_duration':
        await constructores_build(update, context, menu_message_id)
    elif context.user_data.get('builder_state') == 'waiting_description':
        await constructores_build(update, context, menu_message_id)

async def constructores_add(update: Update, context: ContextTypes.DEFAULT_TYPE, menu_message_id=None):
    """Añade una nueva cuenta de constructor"""
    try:
        query = update.callback_query
        if query:
            # Si es una llamada desde un botón, pedir el tag
            if query.data == "builders_add":
                await query.message.edit_text(
                    "🔨 *Añadir Constructor*\n\n"
                    "Por favor, envía el tag del jugador (ejemplo: #VGGG0VY)\n"
                    "o el nombre del jugador.",
                    parse_mode="Markdown"
                )
                context.user_data['builder_state'] = 'waiting_tag'
                return

            # Si es una selección de cantidad de constructores
            if query.data.startswith("builder_count_"):
                cantidad = int(query.data.split('_')[2])
                account_data = context.user_data.get('account_data')
                
                if not account_data:
                    await query.message.edit_text(
                        "❌ Error: datos de cuenta no encontrados",
                        reply_markup=get_main_menu_keyboard()
                    )
                    context.user_data.clear()
                    return

                # Verificar una última vez si el jugador ya está registrado
                is_registered, owner = await builders_dao.is_player_registered(account_data['tag'])
                if is_registered:
                    await query.message.edit_text(
                        f"❌ Este jugador ya está registrado por {owner}\n"
                        f"Tag: {account_data['tag']}",
                        reply_markup=get_main_menu_keyboard()
                    )
                    context.user_data.clear()
                    return
                
                # Registrar la nueva cuenta usando el DAO
                success = await builders_dao.add_builder_account(
                    user_id=str(update.effective_user.id),
                    username=update.effective_user.username or update.effective_user.full_name,
                    player_tag=account_data['tag'],
                    player_data=account_data,
                    builder_count=cantidad
                )

                if success:
                    await query.message.edit_text(
                        f"✅ Se han asignado {cantidad} constructor{'es' if cantidad > 1 else ''} al jugador:\n"
                        f"Nombre: {account_data['name']} [ {account_data['tag']} ]\n"
                        f"Usuario TG: {update.effective_user.username or update.effective_user.full_name}",
                        reply_markup=get_main_menu_keyboard()
                    )
                else:
                    await query.message.edit_text(
                        "❌ Error al registrar los constructores",
                        reply_markup=get_main_menu_keyboard()
                    )
                
                context.user_data.clear()
                return

        # Si es una respuesta a la solicitud del tag
        if context.user_data.get('builder_state') == 'waiting_tag':
            player_tag = update.message.text.strip()
            
            # Verificar si el jugador ya está registrado
            is_registered, owner = await builders_dao.is_player_registered(player_tag)
            if is_registered:
                # Actualizar el mensaje del menú con el error
                if menu_message_id:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=menu_message_id,
                            text=f"❌ Este jugador ya está registrado por {owner}\n"
                                 f"Tag: {player_tag}",
                            reply_markup=get_main_menu_keyboard()
                        )
                    except Exception as e:
                        logger.error(f"Error al actualizar mensaje: {e}")
                context.user_data.clear()
                return

            # Obtener datos del jugador desde la API de Clash of Clans
            clan_members = await fetch_coc_data(f"/clans/{CLAN_TAG}/members")
            if not clan_members:
                # Actualizar el mensaje del menú con el error
                if menu_message_id:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=menu_message_id,
                            text="❌ Error obteniendo lista del clan",
                            reply_markup=get_main_menu_keyboard()
                        )
                    except Exception as e:
                        logger.error(f"Error al actualizar mensaje: {e}")
                context.user_data.clear()
                return

            # Buscar al jugador en los miembros del clan
            account_tag, account_data = None, None
            for member in clan_members.get('items', []):
                if (member["tag"] == player_tag or
                        player_tag == member["name"]):
                    account_tag = member["tag"]
                    account_data = member
                    break

            if not account_tag:
                # Actualizar el mensaje del menú con el error
                if menu_message_id:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=menu_message_id,
                            text=f"❌ El jugador {player_tag} no es miembro del clan actual",
                            reply_markup=get_main_menu_keyboard()
                        )
                    except Exception as e:
                        logger.error(f"Error al actualizar mensaje: {e}")
                context.user_data.clear()
                return

            # Verificar nuevamente si el jugador ya está registrado (por si acaso)
            is_registered, owner = await builders_dao.is_player_registered(account_tag)
            if is_registered:
                # Actualizar el mensaje del menú con el error
                if menu_message_id:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=menu_message_id,
                            text=f"❌ Este jugador ya está registrado por {owner}\n"
                                 f"Tag: {account_tag}",
                            reply_markup=get_main_menu_keyboard()
                        )
                    except Exception as e:
                        logger.error(f"Error al actualizar mensaje: {e}")
                context.user_data.clear()
                return

            # Crear botones para seleccionar cantidad de constructores
            keyboard = []
            for i in range(1, 7):
                keyboard.append([InlineKeyboardButton(f"{i} Constructor{'es' if i > 1 else ''}", 
                                                    callback_data=f"builder_count_{i}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="builders_menu")])
            
            # Actualizar el mensaje del menú
            if menu_message_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=menu_message_id,
                        text=f"✅ Jugador encontrado: {account_data['name']}\n"
                             "Selecciona la cantidad de constructores:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error al actualizar mensaje: {e}")
            
            context.user_data['builder_state'] = 'waiting_count'
            context.user_data['account_data'] = account_data
            return

    except Exception as e:
        logger.error(f"Error en constructores_add: {e}")
        if query:
            await query.message.edit_text(
                "⚠️ Error al procesar el comando",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            # Actualizar el mensaje del menú con el error
            if menu_message_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=menu_message_id,
                        text="⚠️ Error al procesar el comando",
                        reply_markup=get_main_menu_keyboard()
                    )
                except Exception as e:
                    logger.error(f"Error al actualizar mensaje: {e}")
        context.user_data.clear()


async def constructores_build(update: Update, context: ContextTypes.DEFAULT_TYPE, menu_message_id=None):
    """Registra una nueva construcción"""
    try:
        query = update.callback_query
        if query:
            # Si es una llamada desde el menú principal
            if query.data == "builders_build":
                # Obtener las cuentas del usuario
                user_id = str(update.effective_user.id)
                user_data = await builders_dao.get_user_builders(user_id)
                
                if not user_data or not user_data.get("accounts"):
                    await query.message.edit_text(
                        "❌ No tienes constructores registrados.\n"
                        "Usa la opción 'Añadir Constructor' primero.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                # Crear botones para cada cuenta
                keyboard = []
                for tag, account in user_data.get("accounts", {}).items():
                    active = len(account.get("active_builds", []))
                    max_b = account.get("max_builders", 0)
                    if active < max_b:  # Solo mostrar cuentas con constructores disponibles
                        keyboard.append([
                            InlineKeyboardButton(
                                f"{account['name']} (TH{account.get('th_level', '?')}) - {active}/{max_b}",
                                callback_data=f"build_account_{tag}"
                            )
                        ])

                if not keyboard:
                    await query.message.edit_text(
                        "❌ No tienes constructores disponibles en ninguna cuenta.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="builders_menu")])
                
                await query.message.edit_text(
                    "🔨 *Nueva Construcción*\n\n"
                    "Selecciona la cuenta donde quieres construir:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            # Si es una selección de cuenta
            if query.data.startswith("build_account_"):
                account_tag = query.data.split('_')[2]
                context.user_data['selected_account'] = account_tag
                
                # Enviar nuevo mensaje para la duración
                await query.message.reply_text(
                    "⏱️ *Duración de la construcción*\n\n"
                    "Envía la duración en formato:\n"
                    "• 3h30m\n"
                    "• 2d5h\n"
                    "• 45m",
                    parse_mode="Markdown"
                )
                context.user_data['builder_state'] = 'waiting_duration'
                return

        # Si es una entrada de duración
        if context.user_data.get('builder_state') == 'waiting_duration':
            duration_str = update.message.text.strip()
            try:
                duration = parse_duration(duration_str)
                if duration.total_seconds() < 1:
                    await update.message.reply_text(
                        "⚠️ La duración mínima es 1s",
                        reply_markup=get_main_menu_keyboard()
                    )
                    context.user_data.clear()
                    return
            except ValueError:
                await update.message.reply_text(
                    "❌ Formato de tiempo inválido. Ejemplos válidos:\n"
                    "• 3h30m\n• 2d5h\n• 45m",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            context.user_data['duration'] = duration_str
            
            # Enviar nuevo mensaje para la descripción
            await update.message.reply_text(
                "📝 *Descripción de la construcción*\n\n"
                "Envía una breve descripción de lo que vas a construir:",
                parse_mode="Markdown"
            )
            
            context.user_data['builder_state'] = 'waiting_description'
            return

        # Si es una entrada de descripción
        if context.user_data.get('builder_state') == 'waiting_description':
            description = update.message.text.strip()
            account_tag = context.user_data.get('selected_account')
            duration_str = context.user_data.get('duration')
            
            if not account_tag or not duration_str:
                await update.message.reply_text(
                    "❌ Error: datos de construcción incompletos",
                    reply_markup=get_main_menu_keyboard()
                )
                context.user_data.clear()
                return

            # Obtener datos del usuario
            user_id = str(update.effective_user.id)
            user_data = await builders_dao.get_user_builders(user_id)
            
            if not user_data or account_tag not in user_data.get("accounts", {}):
                await update.message.reply_text(
                    "❌ Error: cuenta no encontrada",
                    reply_markup=get_main_menu_keyboard()
                )
                context.user_data.clear()
                return

            account_data = user_data["accounts"][account_tag]

            # Crear la nueva tarea de construcción
            end_time = datetime.now() + parse_duration(duration_str)
            new_build = {
                "start_time": datetime.now().isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration_str,
                "description": description[:100],
                "status": "active"
            }

            # Registrar la construcción usando el DAO
            success = await builders_dao.add_builder_task(
                user_id=user_id,
                player_tag=account_tag,
                task_data=new_build
            )

            if success:
                time_left = format_time_left(end_time.isoformat())
                active_builds = len(account_data["active_builds"])
                max_builders = account_data["max_builders"]
                
                await update.message.reply_text(
                    f"🏗️ *Nueva construcción registrada*\n\n"
                    f"• 👷 Constructor: {account_data['name']} (TH{account_data.get('th_level', '?')})\n"
                    f"• ⏱️ Duración: {duration_str}\n"
                    f"• 📝 Descripción: {description}\n"
                    f"• 🔨 Constructores: {active_builds + 1}/{max_builders}",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "⚠️ Error al registrar la construcción",
                    reply_markup=get_main_menu_keyboard()
                )
            
            context.user_data.clear()
            return

    except Exception as e:
        logger.error(f"Error en constructores_build: {e}")
        if query:
            await query.message.edit_text(
                "⚠️ Error al procesar el comando",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "⚠️ Error al procesar el comando",
                reply_markup=get_main_menu_keyboard()
            )
        context.user_data.clear()


async def constructores_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista los constructores y construcciones activas"""
    try:
        query = update.callback_query
        user_id = str(update.effective_user.id)

        # Obtener datos del usuario
        user_data = await builders_dao.get_user_builders(user_id)
        if not user_data or not user_data.get("accounts"):
            if query:
                try:
                    await query.message.edit_text(
                        "❌ No tienes constructores registrados",
                        reply_markup=get_main_menu_keyboard()
                    )
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        logger.error(f"Error al editar mensaje: {e}")
            else:
                await update.message.reply_text(
                    "❌ No tienes constructores registrados",
                    reply_markup=get_main_menu_keyboard()
                )
            return

        # Construir el mensaje con todas las cuentas y construcciones
        message = ["🏗️ *Tus constructores registrados* 🏗️"]
        has_active_builds = False

        # Crear botones para filtrar por cuenta
        keyboard = []
        for tag, account in user_data["accounts"].items():
            message.append(
                f"\n🔧 *{account['name']}* (TH{account['th_level']}) - {tag}\n"
                f"Constructores: {len(account['active_builds'])}/{account['max_builders']} activos"
            )

            for i, build in enumerate(account["active_builds"], 1):
                has_active_builds = True
                time_left = format_time_left(build["end_time"])
                message.append(
                    f"{i}. ⏳ {build['description']}\n"
                    f"   🕒 Finaliza en {time_left}"
                )

            # Añadir botón para filtrar por cuenta
            keyboard.append([
                InlineKeyboardButton(
                    f"Ver {account['name']}",
                    callback_data=f"list_account_{tag}"
                )
            ])

        # Añadir botón para volver al menú principal
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="builders_menu")])

        # Manejar casos especiales
        if len(message) == 1:
            if query:
                try:
                    await query.message.edit_text(
                        "No tienes construcciones activas actualmente",
                        reply_markup=get_main_menu_keyboard()
                    )
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        logger.error(f"Error al editar mensaje: {e}")
            else:
                await update.message.reply_text(
                    "No tienes construcciones activas actualmente",
                    reply_markup=get_main_menu_keyboard()
                )
            return

        # Si es una solicitud de filtrado por cuenta
        if query and query.data.startswith("list_account_"):
            account_tag = query.data.split('_')[2]
            account = user_data["accounts"][account_tag]
            
            message = [
                f"🔧 *{account['name']}* (TH{account['th_level']}) - {account_tag}\n"
                f"Constructores: {len(account['active_builds'])}/{account['max_builders']} activos"
            ]

            if account["active_builds"]:
                for i, build in enumerate(account["active_builds"], 1):
                    time_left = format_time_left(build["end_time"])
                    message.append(
                        f"\n{i}. ⏳ {build['description']}\n"
                        f"   🕒 Finaliza en {time_left}"
                    )
            else:
                message.append("\nNo hay construcciones activas")

            message.append("\n_Usa el botón Volver para ver todas las cuentas_")
            
            try:
                await query.message.edit_text(
                    '\n'.join(message),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error al editar mensaje: {e}")
            return

        # Mostrar lista completa
        if query:
            try:
                await query.message.edit_text(
                    '\n'.join(message),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error al editar mensaje: {e}")
        else:
            await update.message.reply_text(
                '\n'.join(message),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Error en constructores_list: {e}")
        if query:
            try:
                await query.message.edit_text(
                    "⚠️ Error al listar constructores",
                    reply_markup=get_main_menu_keyboard()
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error al editar mensaje: {e}")
        else:
            await update.message.reply_text(
                "⚠️ Error al listar constructores",
                reply_markup=get_main_menu_keyboard()
            )


async def constructores_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela una construcción activa"""
    try:
        query = update.callback_query
        if query:
            # Si es una llamada desde el menú principal
            if query.data == "builders_cancel":
                # Obtener las cuentas del usuario
                user_id = str(update.effective_user.id)
                user_data = await builders_dao.get_user_builders(user_id)
                
                if not user_data or not user_data.get("accounts"):
                    await query.message.edit_text(
                        "❌ No tienes constructores registrados",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                # Crear botones para cada cuenta con construcciones activas
                keyboard = []
                for tag, account in user_data.get("accounts", {}).items():
                    if account.get("active_builds"):
                        keyboard.append([
                            InlineKeyboardButton(
                                f"{account['name']} ({len(account['active_builds'])} activas)",
                                callback_data=f"cancel_account_{tag}"
                            )
                        ])

                if not keyboard:
                    await query.message.edit_text(
                        "❌ No tienes construcciones activas para cancelar",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="builders_menu")])
                
                await query.message.edit_text(
                    "❌ *Cancelar Construcción*\n\n"
                    "Selecciona la cuenta donde quieres cancelar una construcción:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            # Si es una selección de cuenta para cancelar
            if query.data.startswith("cancel_account_"):
                account_tag = query.data.split('_')[2]
                user_id = str(update.effective_user.id)
                user_data = await builders_dao.get_user_builders(user_id)
                
                if not user_data or account_tag not in user_data.get("accounts", {}):
                    await query.message.edit_text(
                        "❌ Error: cuenta no encontrada",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                account = user_data["accounts"][account_tag]
                if not account.get("active_builds"):
                    await query.message.edit_text(
                        "❌ No hay construcciones activas en esta cuenta",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                # Crear botones para cada construcción activa
                keyboard = []
                for build in account["active_builds"]:
                    time_left = format_time_left(build["end_time"])
                    task_id = build.get('task_id', '')
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{build['description']} ({time_left})",
                            callback_data=f"cancel_build_{account_tag}|{task_id}"
                        )
                    ])

                keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="builders_cancel")])
                
                await query.message.edit_text(
                    f"❌ *Cancelar Construcción en {account['name']}*\n\n"
                    "Selecciona la construcción que quieres cancelar:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            # Si es una selección de construcción para cancelar
            if query.data.startswith("cancel_build_"):
                try:
                    # Extraer account_tag y task_id usando el separador |
                    parts = query.data.split('_')[2].split('|')
                    if len(parts) != 2:
                        raise ValueError("Formato de callback inválido")
                    
                    account_tag, task_id = parts
                    
                    user_id = str(update.effective_user.id)
                    user_data = await builders_dao.get_user_builders(user_id)
                    
                    if not user_data or account_tag not in user_data.get("accounts", {}):
                        await query.message.edit_text(
                            "❌ Error: cuenta no encontrada",
                            reply_markup=get_main_menu_keyboard()
                        )
                        return

                    account = user_data["accounts"][account_tag]

                    # Encontrar la construcción a cancelar
                    build_to_cancel = None
                    for build in account.get("active_builds", []):
                        if build.get("task_id") == task_id:
                            build_to_cancel = build
                            break

                    if not build_to_cancel:
                        await query.message.edit_text(
                            "⚠️ La construcción ya no existe",
                            reply_markup=get_main_menu_keyboard()
                        )
                        return

                    # Cancelar la construcción usando el DAO
                    success = await builders_dao.cancel_builder_task(
                        user_id=user_id,
                        player_tag=account_tag,
                        task_id=task_id
                    )

                    if success:
                        # Actualizar el mensaje con la confirmación y el menú principal
                        await query.message.edit_text(
                            f"🗑️ *Construcción cancelada exitosamente*\n\n"
                            f"• 🔧 Cuenta: {account['name']}\n"
                            f"• 📝 Descripción: {build_to_cancel['description']}\n\n"
                            f"🏗️ Constructores libres: {int(account['max_builders']) - len(account['active_builds']) + 1}",
                            reply_markup=get_main_menu_keyboard(),
                            parse_mode="Markdown"
                        )
                    else:
                        await query.message.edit_text(
                            "⚠️ Error al cancelar la construcción",
                            reply_markup=get_main_menu_keyboard()
                        )
                except Exception as e:
                    logger.error(f"Error al procesar la cancelación: {e}")
                    await query.message.edit_text(
                        "⚠️ Error al procesar la cancelación",
                        reply_markup=get_main_menu_keyboard()
                    )
                
                # Limpiar el estado después de la cancelación
                context.user_data.clear()
                # Restaurar el estado del menú activo
                context.user_data['active_menu'] = True
                return

    except Exception as e:
        logger.error(f"Error en constructores_cancel: {e}")
        if query:
            await query.message.edit_text(
                "⚠️ Error al cancelar la construcción",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "⚠️ Error al cancelar la construcción",
                reply_markup=get_main_menu_keyboard()
            )
        # Limpiar el estado y restaurar el menú activo
        context.user_data.clear()
        context.user_data['active_menu'] = True
