"""Satirlari Telegram mesajina cevirir (HTML parse mode)."""

from __future__ import annotations

from datetime import date
from html import escape

from .config import Config
from .nlu import format_date_tr


def _visible_fields(cfg: Config, row: dict[str, str]) -> list[tuple[str, str]]:
    """config.yaml > fields sirasina gore dolu alanlari dondurur."""
    out = []
    for column, label in cfg.fields.items():
        value = (row.get(column.lower()) or "").strip()
        if value:
            out.append((label, value))
    return out


def render_day(cfg: Config, day: date, row: dict[str, str] | None, *, header: bool = True) -> str:
    title = f"<b>📅 {escape(format_date_tr(day))}</b>"

    if not row:
        text = cfg.messages.get("no_data", "{tarih} için kayıt yok.")
        body = escape(text.format(tarih=format_date_tr(day)))
        return f"{title}\n\n{body}" if header else body

    fields = _visible_fields(cfg, row)
    if not fields:
        text = cfg.messages.get("no_data", "{tarih} için kayıt yok.")
        body = escape(text.format(tarih=format_date_tr(day)))
        return f"{title}\n\n{body}" if header else body

    lines = [f"{escape(label)}: {escape(value)}" for label, value in fields]
    body = "\n".join(lines)
    return f"{title}\n\n{body}" if header else body


def render_range(cfg: Config, days: list[tuple[date, dict[str, str] | None]], label: str) -> str:
    blocks = [f"<b>🗓 {escape(label)}</b>"]
    any_data = False

    for day, row in days:
        fields = _visible_fields(cfg, row or {})
        if not fields:
            continue
        any_data = True
        head = f"<b>{escape(format_date_tr(day))}</b>"
        body = "\n".join(f"{escape(lbl)}: {escape(val)}" for lbl, val in fields)
        blocks.append(f"{head}\n{body}")

    if not any_data:
        blocks.append(escape("Bu aralık için kayıt bulamadım."))

    return "\n\n".join(blocks)


def render_daily_post(cfg: Config, day: date, row: dict[str, str] | None) -> str | None:
    """Sabah gruba atilacak mesaj. Veri yoksa ve skip_if_empty acikca None."""
    fields = _visible_fields(cfg, row or {})
    if not fields and cfg.daily_post.skip_if_empty:
        return None

    parts = []
    intro = (cfg.daily_post.intro or "").strip()
    if intro:
        parts.append(escape(intro))
    parts.append(render_day(cfg, day, row))
    return "\n\n".join(parts)
