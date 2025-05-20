from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from bot.commands import (
    clan as clan_commands,
    war as war_commands,
    builders as builders_commands,
    capital as capital_commands,
    league as league_commands,
    villages as villages_commands
)

from bot.utils import send_to_topic

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de comandos disponibles"""
    commands_list = [
        ("/comandos", "Lista de comandos disponibles"),
        ("/info", "Muestra información básica del clan"),
        ("/guerra", "Estado detallado de la guerra actual"),
        ("/capital", "Progreso del fin de semana de ataque a la capital"),
        ("/liga", "Información de la liga de clanes actual"),
        ("/miembros", "Lista de miembros + Top 5 donadores del clan"),
        ("/constructores", "Gestión de múltiples constructores para tu cuenta de Telegram"),
        ("/aldeas", "Lista de aldeas recomendadas por el líder del clan"),
        ("/agregarAldea", "Agregar una nueva aldea (solo líder del clan)")
    ]

    message = "📜 *COMANDOS DISPONIBLES*:\n\n" + "\n".join(
        f"▸ {cmd} : {desc}" for cmd, desc in commands_list
    )
    await send_to_topic(message, update)

def register_handlers(application: Application):
    """Registra todos los manejadores de comandos"""
    # Comandos básicos
    application.add_handler(CommandHandler("comandos", comandos))
    application.add_handler(CommandHandler("info", clan_commands.claninfo))
    application.add_handler(CommandHandler("guerra", war_commands.guerra))
    application.add_handler(CommandHandler("capital", capital_commands.capital))
    application.add_handler(CommandHandler("liga", league_commands.liga))
    application.add_handler(CommandHandler("miembros", clan_commands.miembros))
    
    # Comandos de constructores
    application.add_handler(CommandHandler("constructores", builders_commands.constructores_handler))
    
    # Manejadores de callbacks para constructores
    application.add_handler(CallbackQueryHandler(
        builders_commands.handle_builder_callback,
        pattern="^builders_"
    ))
    application.add_handler(CallbackQueryHandler(
        builders_commands.constructores_add,
        pattern="^builder_count_"
    ))
    application.add_handler(CallbackQueryHandler(
        builders_commands.constructores_build,
        pattern="^build_account_"
    ))
    application.add_handler(CallbackQueryHandler(
        builders_commands.constructores_list,
        pattern="^list_account_"
    ))
    application.add_handler(CallbackQueryHandler(
        builders_commands.constructores_cancel,
        pattern="^cancel_account_"
    ))
    application.add_handler(CallbackQueryHandler(
        builders_commands.constructores_cancel,
        pattern="^cancel_build_"
    ))

    # Comandos de aldeas
    application.add_handler(CommandHandler("aldeas", villages_commands.aldeas))
    
    # Conversación para agregar aldea
    aldeas_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("agregarAldea", villages_commands.agregar_aldea)],
        states={
            villages_commands.CHOOSING_TH: [
                CallbackQueryHandler(villages_commands.th_selected, pattern="^th_")
            ],
            villages_commands.CHOOSING_TYPE: [
                CallbackQueryHandler(villages_commands.type_selected, pattern="^type_")
            ],
            villages_commands.ENTERING_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, villages_commands.url_received)
            ],
            villages_commands.ENTERING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, villages_commands.description_received)
            ]
        },
        fallbacks=[CommandHandler("cancel", villages_commands.cancel)]
    )
    application.add_handler(aldeas_conv_handler)
    
    # Manejador de mensajes de texto para constructores (debe ir al final)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        builders_commands.handle_text
    ))
