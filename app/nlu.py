"""Yapay zeka yok: kullanicinin yazdigi Turkce cumleden hangi gunu
sordugunu kural tabanli cikaran modul.

parse_when("bugun ne var")   -> Query(kind="day",   dates=[bugun])
parse_when("carsamba ne var")-> Query(kind="day",   dates=[gelecek carsamba])
parse_when("bu hafta")       -> Query(kind="range", dates=[pzt..pazar])
parse_when("selam")          -> None
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

# --- Turkce normalizasyon --------------------------------------------------

_TR = str.maketrans(
    {
        "ı": "i", "İ": "i", "I": "i",
        "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s",
        "ö": "o", "Ö": "o",
        "ç": "c", "Ç": "c",
    }
)


def normalize(text: str) -> str:
    """Turkce karakterleri sadelestirip kucuk harfe cevirir."""
    return re.sub(r"\s+", " ", text.translate(_TR).lower()).strip()


# --- Sabitler --------------------------------------------------------------

# Pazartesi = 0 (date.weekday() ile ayni)
WEEKDAYS = {
    "pazartesi": 0,
    "sali": 1,
    "carsamba": 2,
    "persembe": 3,
    "cuma": 4,
    "cumartesi": 5,
    "pazar": 6,
}

MONTHS = {
    "ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6,
    "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12,
}

WEEKDAY_TR = [
    "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar",
]
MONTH_TR = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def format_date_tr(d: date) -> str:
    return f"{d.day} {MONTH_TR[d.month]} {d.year} {WEEKDAY_TR[d.weekday()]}"


@dataclass
class Query:
    kind: str           # "day" | "range"
    dates: list[date]
    label: str          # insan okunur baslik


# --- Yardimcilar -----------------------------------------------------------

def _week_bounds(d: date, offset_weeks: int = 0) -> list[date]:
    monday = d - timedelta(days=d.weekday()) + timedelta(weeks=offset_weeks)
    return [monday + timedelta(days=i) for i in range(7)]


def _next_weekday(today: date, target: int, allow_today: bool = True) -> date:
    delta = (target - today.weekday()) % 7
    if delta == 0 and not allow_today:
        delta = 7
    return today + timedelta(days=delta)


def _clamp_year(y: int) -> int:
    if y < 100:
        return 2000 + y
    return y


# --- Ana cozumleyici -------------------------------------------------------

def parse_when(text: str, today: date) -> Query | None:
    t = normalize(text)
    if not t:
        return None

    # --- goreli gunler -----------------------------------------------------
    # "obur gun" / "oburgun" -> +2. "bugun" kelimesinden ONCE bakiliyor cunku
    # ikisi de "gun" iceriyor.
    if re.search(r"\bobur\s?gun", t) or re.search(r"\bertesi\s?gun", t):
        d = today + timedelta(days=2)
        return Query("day", [d], format_date_tr(d))

    if re.search(r"\bbugun", t) or re.search(r"\bbgn\b", t) or re.search(r"\bbu\s?gun", t):
        return Query("day", [today], format_date_tr(today))

    if re.search(r"\byarin", t) or re.search(r"\byrn\b", t):
        d = today + timedelta(days=1)
        return Query("day", [d], format_date_tr(d))

    if re.search(r"\bdun\b", t) or re.search(r"\bdunku\b", t):
        d = today - timedelta(days=1)
        return Query("day", [d], format_date_tr(d))

    # --- "24 eylul" / "24 eylul 2026" -------------------------------------
    m = re.search(r"\b(\d{1,2})\s+([a-z]+)(?:\s+(\d{4}))?", t)
    if m and m.group(2) in MONTHS:
        day, month = int(m.group(1)), MONTHS[m.group(2)]
        year = int(m.group(3)) if m.group(3) else today.year
        d = _safe_date(year, month, day)
        if d:
            # Yil yazilmadiysa ve tarih cok geride kaldiysa gelecek yili al.
            if not m.group(3) and (today - d).days > 180:
                d = _safe_date(year + 1, month, day) or d
            return Query("day", [d], format_date_tr(d))

    # --- 2026-09-24 --------------------------------------------------------
    m = re.search(r"\b(\d{4})[-./](\d{1,2})[-./](\d{1,2})\b", t)
    if m:
        d = _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            return Query("day", [d], format_date_tr(d))

    # --- 24.09.2026 / 24/09 ------------------------------------------------
    m = re.search(r"\b(\d{1,2})[-./](\d{1,2})(?:[-./](\d{2,4}))?\b", t)
    if m:
        year = _clamp_year(int(m.group(3))) if m.group(3) else today.year
        d = _safe_date(year, int(m.group(2)), int(m.group(1)))
        if d:
            if not m.group(3) and (today - d).days > 180:
                d = _safe_date(year + 1, int(m.group(2)), int(m.group(1))) or d
            return Query("day", [d], format_date_tr(d))

    # --- gun isimleri ------------------------------------------------------
    # Haftalardan ONCE bakiliyor: "haftaya cuma" tek bir gun demek,
    # "haftaya" tek basina ise butun hafta demek.
    # "pazartesi" icinde "pazar" gectigi icin uzun isimler once kontrol edilir.
    for name in sorted(WEEKDAYS, key=len, reverse=True):
        if re.search(rf"\b{name}", t):
            next_week = bool(re.search(r"\b(gelecek|onumuzdeki|sonraki|haftaya)\b", t))
            if next_week:
                d = _next_weekday(today + timedelta(days=7 - today.weekday()), WEEKDAYS[name])
            else:
                d = _next_weekday(today, WEEKDAYS[name], allow_today=True)
            return Query("day", [d], format_date_tr(d))

    # --- haftalar ----------------------------------------------------------
    # "haftaya" / "gelecek hafta" / "onumuzdeki hafta" -> +1 hafta
    if re.search(r"\bhaftaya\b", t) or re.search(r"\b(gelecek|onumuzdeki|sonraki)\s+hafta", t):
        days = _week_bounds(today, 1)
        return Query("range", days, f"Gelecek hafta ({days[0].day} - {days[-1].day} {MONTH_TR[days[-1].month]})")

    if re.search(r"\bgecen\s+hafta", t):
        days = _week_bounds(today, -1)
        return Query("range", days, f"Geçen hafta ({days[0].day} - {days[-1].day} {MONTH_TR[days[-1].month]})")

    if re.search(r"\bhafta\b", t) or re.search(r"\bhaftalik\b", t) or re.search(r"\bhaftanin\b", t):
        days = _week_bounds(today)
        return Query("range", days, f"Bu hafta ({days[0].day} - {days[-1].day} {MONTH_TR[days[-1].month]})")

    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
