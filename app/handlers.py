"""Telegram komut ve mesaj isleyicileri.

Onemli kural: serbest metin ve normal komutlar SADECE ozel sohbette
calisir (filters.ChatType.PRIVATE). Grupta bot kimseye cevap vermez;
gruba sadece sabah isi (jobs.py) mesaj atar.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Config
from .datasource import MenuStore
from .nlu import format_date_tr, parse_when
from .render import render_day, render_daily_post, render_range

log = logging.getLogger(__name__)

PRIVATE = filters.ChatType.PRIVATE


def _today(cfg: Config):
    return datetime.now(cfg.tz).date()


async def _reply(update: Update, text: str) -> None:
    await update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


def build_handlers(cfg: Config, store: MenuStore) -> list:
    # ---------------------------------------------------------------- start

    async def start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        name = update.effective_user.first_name or "merhaba"
        await _reply(
            update,
            f"Selam {name}! 👋\n\n"
            "Bana <b>bugün ne var</b>, <b>yarın ne var</b>, <b>çarşamba ne var</b> "
            "ya da <b>bu hafta</b> diye yazabilirsin.\n\n"
            "Komutlar: /bugun /yarin /hafta /yardim",
        )

    async def yardim(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await _reply(update, cfg.messages.get("not_understood", "Örnek: bugün ne var"))

    # ------------------------------------------------------------ sorgular

    async def _answer_query(update: Update, text: str) -> bool:
        q = parse_when(text, _today(cfg))
        if q is None:
            return False
        if q.kind == "day":
            day = q.dates[0]
            await _reply(update, render_day(cfg, day, store.get(day)))
        else:
            await _reply(update, render_range(cfg, store.get_many(q.dates), q.label))
        return True

    async def bugun(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        day = _today(cfg)
        await _reply(update, render_day(cfg, day, store.get(day)))

    async def yarin(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        day = _today(cfg) + timedelta(days=1)
        await _reply(update, render_day(cfg, day, store.get(day)))

    async def hafta(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        q = parse_when("bu hafta", _today(cfg))
        await _reply(update, render_range(cfg, store.get_many(q.dates), q.label))

    async def gun(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        arg = " ".join(ctx.args or []).strip()
        if not arg:
            await _reply(update, "Kullanım: <code>/gun 24 eylül</code> veya <code>/gun 24.09.2026</code>")
            return
        if not await _answer_query(update, arg):
            await _reply(update, f"<code>{arg}</code> tarihini anlayamadım.")

    async def serbest_metin(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.effective_message.text or ""
        if not await _answer_query(update, text):
            await _reply(update, cfg.messages.get("not_understood", "Anlayamadım."))

    # ------------------------------------------------------------- kurulum

    async def chatid(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not (cfg.setup_mode or cfg.is_admin(user.id)):
            return
        chat = update.effective_chat
        await update.effective_message.reply_text(
            f"chat_id: {chat.id}\nchat tipi: {chat.type}\nsenin kullanıcı id: {user.id}"
        )

    # -------------------------------------------------------------- yonetim

    def _admin_only(handler):
        async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
            if not cfg.is_admin(update.effective_user.id):
                return
            await handler(update, ctx)

        return wrapper

    @_admin_only
    async def yenile(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        count = store.reload()
        await _reply(update, f"♻️ Yenilendi. {count} günlük kayıt var.")

    @_admin_only
    async def durum(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        now = datetime.now(cfg.tz)
        await _reply(
            update,
            "<b>Durum</b>\n"
            f"Saat: {now:%d.%m.%Y %H:%M} ({cfg.daily_post.timezone})\n"
            f"Bugün: {format_date_tr(now.date())}\n"
            f"Grup: <code>{cfg.group_chat_id}</code>\n"
            f"Sabah mesajı: {cfg.daily_post.time} "
            f"({'açık' if cfg.daily_post.enabled else 'kapalı'})\n"
            f"Veri: {store.status}",
        )

    @_admin_only
    async def onizle(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        day = _today(cfg)
        text = render_daily_post(cfg, day, store.get(day))
        if text is None:
            await _reply(update, "Bugün için veri yok; sabah mesajı atılmayacak.")
        else:
            await _reply(update, text)

    # ------------------------------------------------------------ kayitlar

    return [
        CommandHandler("start", start, filters=PRIVATE),
        CommandHandler(["yardim", "help"], yardim, filters=PRIVATE),
        CommandHandler("bugun", bugun, filters=PRIVATE),
        CommandHandler("yarin", yarin, filters=PRIVATE),
        CommandHandler("hafta", hafta, filters=PRIVATE),
        CommandHandler("gun", gun, filters=PRIVATE),
        # chatid kurulum icin gruplarda da calisir (admin / kurulum modu)
        CommandHandler("chatid", chatid),
        CommandHandler("yenile", yenile, filters=PRIVATE),
        CommandHandler("durum", durum, filters=PRIVATE),
        CommandHandler("onizle", onizle, filters=PRIVATE),
        MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, serbest_metin),
    ]


def register(app: Application, cfg: Config, store: MenuStore) -> None:
    for handler in build_handlers(cfg, store):
        app.add_handler(handler)
