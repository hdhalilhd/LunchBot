"""Telegram'a hic baglanmadan mesajlari terminalde gor.

Kullanim:
    .venv\\Scripts\\python.exe scripts\\preview.py "bugun ne var"
    .venv\\Scripts\\python.exe scripts\\preview.py "bu hafta"
    .venv\\Scripts\\python.exe scripts\\preview.py --sabah
    .venv\\Scripts\\python.exe scripts\\preview.py            (interaktif)
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_config  # noqa: E402
from app.datasource import MenuStore  # noqa: E402
from app.nlu import parse_when  # noqa: E402
from app.render import render_daily_post, render_day, render_range  # noqa: E402

TAGS = re.compile(r"</?(b|i|code|pre|u|s|a)[^>]*>")


def strip_html(text: str) -> str:
    text = TAGS.sub("", text)
    return (
        text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    )


def answer(cfg, store, text: str) -> str:
    today = datetime.now(cfg.tz).date()
    q = parse_when(text, today)
    if q is None:
        return cfg.messages.get("not_understood", "Anlayamadim.")
    if q.kind == "day":
        day = q.dates[0]
        return render_day(cfg, day, store.get(day))
    return render_range(cfg, store.get_many(q.dates), q.label)


def main() -> None:
    cfg = load_config(require_token=False)
    store = MenuStore(cfg)
    count = store.reload()

    args = sys.argv[1:]

    if args and args[0] in ("--sabah", "--daily"):
        today = datetime.now(cfg.tz).date()
        out = render_daily_post(cfg, today, store.get(today))
        print("--- sabah 08:00 gruba gidecek mesaj ---")
        print(strip_html(out) if out else "(veri yok, mesaj atilmaz)")
        return

    if args:
        print(strip_html(answer(cfg, store, " ".join(args))))
        return

    print(f"[{count} gunluk kayit okundu. Cikmak icin bos Enter.]\n")
    while True:
        try:
            line = input("sen > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            break
        print("\nbot >")
        print(strip_html(answer(cfg, store, line)))
        print()


if __name__ == "__main__":
    main()
