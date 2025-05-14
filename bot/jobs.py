from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from bot.utils import load_constructores, save_constructores, send_to_topic, send_to_topic_html
import logging

logger = logging.getLogger(__name__)

async def check_builders_notifications(context: ContextTypes.DEFAULT_TYPE):
    try:
        data = load_constructores()
        now = datetime.now()
        modified = False

        for user_id, user_data in data.items():
            for tag, account in user_data.get("accounts", {}).items():
                builds_to_remove = []

                for idx, build in enumerate(account.get("active_builds", [])):
                    end_time = datetime.fromisoformat(build["end_time"])
                    time_left = end_time - now

                    if timedelta(seconds=0) < time_left <= timedelta(minutes=1):
                        try:
                            logger.info(f"Notificando a {user_id}")
                            await send_to_topic_html(
                                f"⏰ <a href='tg://user?id={user_id}'>"
                                f"{user_data['username']}</a>, tu construcción "
                                f"'{build['description']}' de la cuenta {account['name']} está por finalizar "
                                f"en 1 minuto."
                            )
                            builds_to_remove.append(idx)
                            modified = True
                        except Exception as e:
                            logger.error(f"Error notificando: {e}")

                for idx in sorted(builds_to_remove, reverse=True):
                    account["active_builds"].pop(idx)

        if modified:
            save_constructores(data)
            logger.info("Registros de construcciones finalizadas eliminados")

    except Exception as e:
        logger.error(f"Error en check_builders_notifications: {e}")