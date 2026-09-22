"""Menu verisini okuyan katman.

Kaynak yerel bir CSV/JSON dosyasi ya da bir URL (GitHub raw linki,
Google Sheets'in "web'de yayinla > CSV" linki) olabilir. URL modunda
veri bellekte TTL suresi kadar tutulur; indirme basarisiz olursa son
basarili veri kullanilmaya devam eder (bot susmaz).
"""

from __future__ import annotations

import csv
import io
import json
import logging
import time
from datetime import date, datetime

import httpx

from .config import Config

log = logging.getLogger(__name__)

# CSV'de kabul edilen tarih yazimlari
_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")


def parse_cell_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class MenuStore:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._rows: dict[date, dict[str, str]] = {}
        self._loaded_at: float = 0.0
        self._last_error: str | None = None

    # -- genel API ----------------------------------------------------------

    def get(self, day: date) -> dict[str, str] | None:
        self._refresh_if_needed()
        return self._rows.get(day)

    def get_many(self, days: list[date]) -> list[tuple[date, dict[str, str] | None]]:
        self._refresh_if_needed()
        return [(d, self._rows.get(d)) for d in days]

    def reload(self) -> int:
        """Onbellegi zorla tazeler, okunan gun sayisini dondurur."""
        self._load()
        return len(self._rows)

    @property
    def status(self) -> str:
        if not self._loaded_at:
            return "henüz yüklenmedi"
        age = int(time.time() - self._loaded_at)
        src = self.cfg.data.url if self.cfg.data.source == "url" else str(self.cfg.resolved_local_path())
        line = f"{len(self._rows)} gün | kaynak: {src} | {age} sn önce yüklendi"
        if self._last_error:
            line += f"\n⚠️ son hata: {self._last_error}"
        return line

    # -- ic isleyis ---------------------------------------------------------

    def _refresh_if_needed(self) -> None:
        ttl = self.cfg.data.cache_ttl_minutes * 60
        if self.cfg.data.source == "local":
            # Yerel dosyada mtime degistiyse yeniden oku.
            path = self.cfg.resolved_local_path()
            mtime = path.stat().st_mtime if path.exists() else 0
            if not self._loaded_at or mtime > self._loaded_at:
                self._load()
            return
        if not self._loaded_at or (time.time() - self._loaded_at) > ttl:
            self._load()

    def _load(self) -> None:
        try:
            text = self._fetch()
            rows = self._parse(text)
        except Exception as exc:  # noqa: BLE001 - bot ayakta kalmali
            self._last_error = f"{type(exc).__name__}: {exc}"
            log.warning("Menu yuklenemedi (%s). Eldeki veri kullanilacak.", self._last_error)
            if not self._rows:
                self._loaded_at = time.time()  # surekli denemeyi engelle
            return

        self._rows = rows
        self._loaded_at = time.time()
        self._last_error = None
        log.info("Menu yuklendi: %d gun", len(rows))

    def _fetch(self) -> str:
        if self.cfg.data.source == "url":
            url = self.cfg.data.url.strip()
            if not url:
                raise ValueError("config.yaml icinde data.url bos")
            resp = httpx.get(url, timeout=20, follow_redirects=True)
            resp.raise_for_status()
            return resp.text
        path = self.cfg.resolved_local_path()
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8-sig")

    def _parse(self, text: str) -> dict[date, dict[str, str]]:
        stripped = text.lstrip()
        if stripped.startswith("[") or stripped.startswith("{"):
            return self._parse_json(stripped)
        return self._parse_csv(text)

    def _parse_csv(self, text: str) -> dict[date, dict[str, str]]:
        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return self._rows_from_dicts(reader)

    def _parse_json(self, text: str) -> dict[date, dict[str, str]]:
        payload = json.loads(text)
        if isinstance(payload, dict):
            # {"2026-09-22": {"ogle": "..."} } bicimi
            records = []
            for key, value in payload.items():
                row = dict(value or {})
                row[self.cfg.data.date_column] = key
                records.append(row)
            return self._rows_from_dicts(records)
        return self._rows_from_dicts(payload)

    def _rows_from_dicts(self, records) -> dict[date, dict[str, str]]:
        date_col = self.cfg.data.date_column
        out: dict[date, dict[str, str]] = {}
        for raw in records:
            if not raw:
                continue
            # Kolon adlarindaki bosluk/buyuk-kucuk farklarini tolere et.
            row = {
                (k or "").strip().lower(): ("" if v is None else str(v).strip())
                for k, v in raw.items()
                if k
            }
            day = parse_cell_date(row.get(date_col.lower(), ""))
            if day is None:
                continue
            out[day] = row
        return out
