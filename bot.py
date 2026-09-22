"""MenuBot - giris noktasi.

Calistirma:
    .venv\\Scripts\\python.exe bot.py
"""

from __future__ import annotations

import logging
import sys

from telegram import Update
from telegram.ext import Application, ContextTypes

from app import handlers, jobs
from app.config import load_config
from app.datasource import MenuStore


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.getLogger("bot").error("Islenmemis hata", exc_info=context.error)


def main() -> None:
    setup_logging()
    log = logging.getLogger("bot")

    cfg = load_config()
    store = MenuStore(cfg)
    count = store.reload()
    log.info("Baslangicta %d gunluk kayit okundu.", count)

    app = Application.builder().token(cfg.bot_token).build()
    handlers.register(app, cfg, store)
    jobs.setup_daily_job(app, cfg, store)
    app.add_error_handler(on_error)

    log.info("Bot calisiyor. Durdurmak icin Ctrl+C.")
    # Gruplardaki normal mesajlari hic almiyoruz; sadece ozel sohbet ve
    # bota yazilan komutlar isleniyor.
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
