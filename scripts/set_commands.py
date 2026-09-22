"""Telegram'daki komut menüsünü (yazarken çıkan liste) ayarlar.

    .venv\\Scripts\\python.exe scripts\\set_commands.py

Komutlar yalnızca özel sohbetlerde görünür; grupta menü kirlenmez.
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
    sys.exit(".env içinde BOT_TOKEN yok.")

COMMANDS = [
    {"command": "bugun", "description": "Bugünün menüsü"},
    {"command": "yarin", "description": "Yarının menüsü"},
    {"command": "hafta", "description": "Bu haftanın tamamı"},
    {"command": "gun", "description": "Belirli bir gün — örn: /gun 24 eylül"},
    {"command": "yardim", "description": "Nasıl sorarım?"},
]

resp = httpx.post(
    f"https://api.telegram.org/bot{token}/setMyCommands",
    json={"commands": COMMANDS, "scope": {"type": "all_private_chats"}},
    timeout=20,
).json()

if resp.get("ok"):
    print("Komut menüsü ayarlandı (yalnızca özel sohbetler):")
    for c in COMMANDS:
        print(f"  /{c['command']:<8} {c['description']}")
else:
    sys.exit(f"Hata: {resp}")
