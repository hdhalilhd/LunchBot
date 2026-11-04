"""Her sabah gruba mesaj atan zamanlanmis is."""

from __future__ import annotations

import datetime as dt
import logging

from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes

from .config import Config
from .datasource import MenuStore
from .render import render_daily_post

log = logging.getLogger(__name__)


def setup_daily_job(app: Application, cfg: Config, store: MenuStore) -> None:
    if not cfg.daily_post.enabled:
        log.info("Sabah mesaji kapali (daily_post.enabled = false).")
        return

    if cfg.group_chat_id is None:
        log.warning("GROUP_CHAT_ID tanimli degil; sabah mesaji kurulmadi.")
        return

    if app.job_queue is None:
        log.error(
            "JobQueue yok. Kurulum: pip install \"python-telegram-bot[job-queue]\""
        )
        return

    hour, minute = cfg.daily_post.hour_minute
    when = dt.time(hour=hour, minute=minute, tzinfo=cfg.daily_post.tz)

    # PTB run_daily gun numaralari: 0=pazar ... 6=cumartesi. Pazartesi-cuma = 1-5.
    days = (1, 2, 3, 4, 5) if cfg.daily_post.skip_weekends else tuple(range(7))

    async def daily(ctx: ContextTypes.DEFAULT_TYPE) -> None:
        today = dt.datetime.now(cfg.tz).date()
        store.reload()  # sabah her zaman taze veriyle calis
        text = render_daily_post(cfg, today, store.get(today))
        if text is None:
            log.info("%s icin veri yok, sabah mesaji atlandi.", today)
            return
        await ctx.bot.send_message(
            chat_id=cfg.group_chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        log.info("Sabah mesaji gonderildi: %s -> %s", today, cfg.group_chat_id)

    app.job_queue.run_daily(
        daily,
        time=when,
        days=days,
        name="gunluk_duyuru",
        # Varsayilan tolerans 1 sn: bot o anda mesgulse gunun mesaji sessizce atlanir.
        job_kwargs={"misfire_grace_time": 600},
    )
    log.info(
        "Sabah mesaji kuruldu: %s %02d:%02d (%s), hedef %s",
        "hafta ici" if cfg.daily_post.skip_weekends else "her gun",
        hour, minute, cfg.daily_post.timezone, cfg.group_chat_id,
    )
