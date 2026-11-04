from datetime import datetime, timedelta

import pytest
from telegram.ext import Application

from app import jobs
from app.config import Config, DailyPostCfg, DataCfg


def fire_times(**daily) -> list[datetime]:
    """Kurulan isin 2-8 Kasim 2026 (pazartesi-pazar) haftasindaki calisma anlari."""
    cfg = Config(
        bot_token="1:x",
        group_chat_id=-100,
        data=DataCfg(),
        daily_post=DailyPostCfg(**daily),
    )
    app = Application.builder().token(cfg.bot_token).build()
    jobs.setup_daily_job(app, cfg, store=None)

    trigger = app.job_queue.jobs()[0].job.trigger
    tz = cfg.daily_post.tz
    now, end = tz.localize(datetime(2026, 11, 2)), tz.localize(datetime(2026, 11, 9))

    out, prev = [], None
    while True:
        prev = trigger.get_next_fire_time(prev, now)
        if prev >= end:
            return out
        out.append(prev)
        now = prev + timedelta(seconds=1)


def test_hafta_sonu_haric_pazartesi_cuma():
    fires = fire_times(time="08:30", skip_weekends=True)
    assert [f.weekday() for f in fires] == [0, 1, 2, 3, 4]


def test_hafta_sonu_dahil_her_gun():
    fires = fire_times(time="08:30", skip_weekends=False)
    assert [f.weekday() for f in fires] == [0, 1, 2, 3, 4, 5, 6]


@pytest.mark.parametrize("saat,beklenen", [("08:30", (8, 30)), ("07:05", (7, 5))])
def test_istanbul_saatiyle_calisir(saat, beklenen):
    for f in fire_times(time=saat, timezone="Europe/Istanbul"):
        assert (f.hour, f.minute) == beklenen
        assert f.utcoffset() == timedelta(hours=3)


def test_gec_kalan_is_kaybolmaz():
    cfg = Config(bot_token="1:x", group_chat_id=-100, data=DataCfg(), daily_post=DailyPostCfg())
    app = Application.builder().token(cfg.bot_token).build()
    jobs.setup_daily_job(app, cfg, store=None)
    assert app.job_queue.jobs()[0].job.misfire_grace_time >= 300
