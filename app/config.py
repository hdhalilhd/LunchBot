"""config.yaml + .env okuma."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pytz
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class DataCfg:
    source: str = "local"
    local_path: str = "data/menu.csv"
    url: str = ""
    cache_ttl_minutes: int = 15
    date_column: str = "tarih"


@dataclass
class DailyPostCfg:
    enabled: bool = True
    time: str = "08:00"
    timezone: str = "Europe/Istanbul"
    skip_weekends: bool = False
    skip_if_empty: bool = True
    intro: str = ""

    @property
    def tz(self):
        # APScheduler 3.x sadece pytz saat dilimlerini kabul ediyor.
        return pytz.timezone(self.timezone)

    @property
    def hour_minute(self) -> tuple[int, int]:
        hh, _, mm = self.time.partition(":")
        return int(hh), int(mm or 0)


@dataclass
class Config:
    bot_token: str
    group_chat_id: int | None
    data: DataCfg
    daily_post: DailyPostCfg
    fields: dict[str, str] = field(default_factory=dict)
    messages: dict[str, str] = field(default_factory=dict)
    admins: list[int] = field(default_factory=list)

    @property
    def tz(self):
        return self.daily_post.tz

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins

    @property
    def setup_mode(self) -> bool:
        """Henuz admin tanimlanmamis: kurulum komutlari herkese acik."""
        return not self.admins

    def resolved_local_path(self) -> Path:
        p = Path(self.data.local_path)
        return p if p.is_absolute() else ROOT / p


def load_config(config_path: Path | None = None, *, require_token: bool = True) -> Config:
    """require_token=False ile token olmadan da yuklenir (onizleme/test icin)."""
    load_dotenv(ROOT / ".env")

    path = config_path or ROOT / "config.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token and require_token:
        raise SystemExit(
            "BOT_TOKEN bos. .env.example dosyasini .env olarak kopyalayip "
            "BotFather'dan aldigin token'i yaz."
        )

    raw_group = os.getenv("GROUP_CHAT_ID", "").strip()
    group_id: int | None = None
    if raw_group:
        try:
            group_id = int(raw_group)
        except ValueError:
            raise SystemExit(f"GROUP_CHAT_ID sayi olmali, gelen: {raw_group!r}")

    return Config(
        bot_token=token,
        group_chat_id=group_id,
        data=DataCfg(**(raw.get("data") or {})),
        daily_post=DailyPostCfg(**(raw.get("daily_post") or {})),
        fields=raw.get("fields") or {},
        messages=raw.get("messages") or {},
        admins=[int(a) for a in (raw.get("admins") or [])],
    )
