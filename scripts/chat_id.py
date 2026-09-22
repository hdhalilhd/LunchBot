"""Grup chat_id'sini ogrenmek icin tek seferlik yardimci.

Kullanim:
    .venv\\Scripts\\python.exe scripts\\chat_id.py

Botu gruba ekle, gruba herhangi bir mesaj yaz (ya da "/chatid@BOTADIN"
yaz), sonra bu scripti calistir. Botun gordugu tum sohbetleri listeler.

Not: bot "privacy mode" acikken normal grup mesajlarini gormez; o yuzden
en garantisi gruba /chatid@BOTADIN yazmak ya da botu gruba yonetici
yapmaktir.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

token = os.getenv("BOT_TOKEN", "").strip()
if not token:
    sys.exit(".env icinde BOT_TOKEN yok.")

me = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=20).json()
if not me.get("ok"):
    sys.exit(f"Token gecersiz gorunuyor: {me}")
print(f"Bot: @{me['result']['username']}  (id: {me['result']['id']})\n")

resp = httpx.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"timeout": 5, "limit": 100},
    timeout=30,
).json()

if not resp.get("ok"):
    sys.exit(f"getUpdates hatasi: {resp}")

updates = resp.get("result", [])
if not updates:
    print("Hic guncelleme yok.")
    print("-> Botu gruba ekle ve gruba '/chatid@BOTADIN' yaz, sonra tekrar calistir.")
    print("-> Bot zaten calisiyorsa once onu durdur (ayni anda iki yerden okunamaz).")
    sys.exit(0)

seen: dict[int, tuple[str, str]] = {}
for upd in updates:
    msg = (
        upd.get("message")
        or upd.get("edited_message")
        or upd.get("channel_post")
        or upd.get("my_chat_member", {}).get("chat") and upd["my_chat_member"]
    )
    chat = (msg or {}).get("chat")
    if chat:
        seen[chat["id"]] = (
            chat.get("type", "?"),
            chat.get("title") or chat.get("username") or chat.get("first_name") or "",
        )

print("Gorulen sohbetler:")
for chat_id, (ctype, title) in seen.items():
    flag = "  <-- .env icine GROUP_CHAT_ID olarak bunu yaz" if ctype in ("group", "supergroup") else ""
    print(f"  {chat_id:>16}  {ctype:<12} {title}{flag}")
