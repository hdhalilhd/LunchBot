from datetime import date

import pytest

from app.nlu import format_date_tr, normalize, parse_when

# 22 Eylul 2026 = Sali
TODAY = date(2026, 9, 22)


def when(text: str):
    q = parse_when(text, TODAY)
    assert q is not None, f"anlasilamadi: {text!r}"
    return q


@pytest.mark.parametrize(
    "text,expected",
    [
        ("bugün ne var", date(2026, 9, 22)),
        ("BUGÜN NE VAR?", date(2026, 9, 22)),
        ("bugun", date(2026, 9, 22)),
        ("bgn ne var", date(2026, 9, 22)),
        ("yarın ne var", date(2026, 9, 23)),
        ("yarin menü nedir", date(2026, 9, 23)),
        ("dün ne vardı", date(2026, 9, 21)),
        ("öbür gün ne var", date(2026, 9, 24)),
        ("obur gun", date(2026, 9, 24)),
    ],
)
def test_goreli_gunler(text, expected):
    q = when(text)
    assert q.kind == "day"
    assert q.dates == [expected]


@pytest.mark.parametrize(
    "text,expected",
    [
        # Bugun sali; "sali" bugunu isaret eder.
        ("salı ne var", date(2026, 9, 22)),
        ("çarşamba ne var", date(2026, 9, 23)),
        ("cuma ne var", date(2026, 9, 25)),
        ("pazartesi ne var", date(2026, 9, 28)),
        ("pazar ne var", date(2026, 9, 27)),
        ("cumartesi", date(2026, 9, 26)),
        ("perşembe menü", date(2026, 9, 24)),
    ],
)
def test_gun_isimleri(text, expected):
    q = when(text)
    assert q.dates == [expected]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("gelecek cuma ne var", date(2026, 10, 2)),
        # "haftaya cuma" tek gun demek, butun hafta degil
        ("haftaya cuma ne var", date(2026, 10, 2)),
        ("haftaya pazartesi", date(2026, 9, 28)),
        ("önümüzdeki salı", date(2026, 9, 29)),
    ],
)
def test_gelecek_hafta_gun_ismi(text, expected):
    q = when(text)
    assert q.kind == "day"
    assert q.dates == [expected]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("24 eylül ne var", date(2026, 9, 24)),
        ("24 eylul 2026", date(2026, 9, 24)),
        ("1 ekim ne var", date(2026, 10, 1)),
        ("24.09.2026", date(2026, 9, 24)),
        ("24/09", date(2026, 9, 24)),
        ("2026-09-24", date(2026, 9, 24)),
    ],
)
def test_tarihler(text, expected):
    assert when(text).dates == [expected]


def test_gecmis_ay_gelecek_yila_kayar():
    # Mart cok geride kaldi -> bir sonraki yilin marti
    assert when("3 mart").dates == [date(2027, 3, 3)]


def test_bu_hafta():
    q = when("bu hafta ne var")
    assert q.kind == "range"
    assert q.dates[0] == date(2026, 9, 21)   # pazartesi
    assert q.dates[-1] == date(2026, 9, 27)  # pazar
    assert len(q.dates) == 7


def test_gelecek_hafta():
    q = when("haftaya ne var")
    assert q.kind == "range"
    assert q.dates[0] == date(2026, 9, 28)


@pytest.mark.parametrize("text", ["selam", "naber", "teşekkürler", "", "   ", "ne var ne yok"])
def test_anlasilmayanlar(text):
    assert parse_when(text, TODAY) is None


def test_normalize():
    assert normalize("ÇARŞAMBA Günü İYİ") == "carsamba gunu iyi"
    assert normalize("  bugün   ne  var ") == "bugun ne var"


def test_format_date_tr():
    assert format_date_tr(date(2026, 9, 22)) == "22 Eylül 2026 Salı"
    assert format_date_tr(date(2026, 3, 1)) == "1 Mart 2026 Pazar"
