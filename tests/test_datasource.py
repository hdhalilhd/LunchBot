from datetime import date, datetime

import pytest

from app.config import Config, DailyPostCfg, DataCfg
from app.datasource import MenuStore, parse_cell_date


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2026-09-22", date(2026, 9, 22)),
        ("22.09.2026", date(2026, 9, 22)),
        ("22/09/2026", date(2026, 9, 22)),
        # lunchnotice Excel'indeki biçim
        ("1 Eylül 2026", date(2026, 9, 1)),
        ("22 Eylül 2026", date(2026, 9, 22)),
        ("3 Aralık 2026", date(2026, 12, 3)),
        # Excel gerçek tarih hücresi verirse
        (datetime(2026, 9, 22, 0, 0), date(2026, 9, 22)),
        (date(2026, 9, 22), date(2026, 9, 22)),
    ],
)
def test_parse_cell_date(value, expected):
    assert parse_cell_date(value) == expected


@pytest.mark.parametrize("value", [None, "", "   ", "Tarih", "abc", "32 Eylül 2026", "1 Xyz 2026"])
def test_parse_cell_date_gecersiz(value):
    assert parse_cell_date(value) is None


def _cfg(path: str, date_column: str, fields: dict) -> Config:
    return Config(
        bot_token="test",
        group_chat_id=None,
        data=DataCfg(source="local", local_path=path, date_column=date_column),
        daily_post=DailyPostCfg(),
        fields=fields,
        messages={},
        admins=[],
    )


def test_xlsx_okunuyor():
    store = MenuStore(
        _cfg("data/Yemek_Listesi.xlsx", "Tarih", {"çorba": "Çorba"})
    )
    assert store.reload() == 22  # Eylül 2026 iş günleri

    row = store.get(date(2026, 9, 22))
    assert row is not None
    assert row["çorba"] == "ISPANAK ÇORBA"
    assert row["ana yemek"] == "ETLİ NOHUT"
    assert row["gün"] == "Salı"

    # Hafta sonu Excel'de yok
    assert store.get(date(2026, 9, 26)) is None
    assert store.date_span == (date(2026, 9, 1), date(2026, 9, 30))


def test_csv_okunuyor():
    store = MenuStore(_cfg("data/menu.csv", "tarih", {"ogle": "Öğle"}))
    assert store.reload() == 10
    row = store.get(date(2026, 9, 22))
    assert row is not None
    assert "İzmir köfte" in row["ogle"]


def test_kaynak_bulunamazsa_bot_cokmez():
    store = MenuStore(_cfg("data/yok-boyle-bir-dosya.csv", "tarih", {}))
    assert store.reload() == 0
    assert store.get(date(2026, 9, 22)) is None
    assert "son hata" in store.status
