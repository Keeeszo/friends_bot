import logging
from telegram.ext import Application
from bot.handlers import register_handlers
from bot.jobs import check_builders_notifications
from config import TELEGRAM_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    register_handlers(application)

    if hasattr(application, "job_queue"):
        application.job_queue.run_repeating(
            check_builders_notifications,
            interval=60.0,
            first=10.0
        )
        logger.info("JobQueue configurado para notificaciones")
    else:
        logger.warning("JobQueue no disponible. Notificaciones desactivadas")

    application.bot.delete_webhook(drop_pending_updates=True)
    application.run_polling()


if __name__ == "__main__":
    main()