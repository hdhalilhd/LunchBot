"""Yeni menü dosyasını GitHub'a yüklemeden önce kontrol eder.

    .venv\\Scripts\\python.exe scripts\\kontrol.py                      (canlı kaynağı kontrol et)
    .venv\\Scripts\\python.exe scripts\\kontrol.py C:\\yol\\Ekim.xlsx    (yerel dosyayı kontrol et)
    .venv\\Scripts\\python.exe scripts\\kontrol.py https://...          (bir URL'i kontrol et)

Söyledikleri: kaç gün okundu, hangi kolonlar var, config'deki başlıklarla
eşleşiyor mu, hafta içi eksik gün var mı, ve örnek bir mesaj.
"""

from __future__ import annotations

import re
import sys
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_config  # noqa: E402
from app.datasource import MenuStore  # noqa: E402
from app.nlu import format_date_tr  # noqa: E402
from app.render import render_day  # noqa: E402

TAGS = re.compile(r"</?(b|i|code|pre|u|s|a)[^>]*>")


def strip_html(text: str) -> str:
    return TAGS.sub("", text).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def main() -> int:
    cfg = load_config(require_token=False)

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg:
        if arg.startswith("http"):
            cfg.data = replace(cfg.data, source="url", url=arg)
            nerede = arg
        else:
            path = Path(arg).resolve()
            if not path.exists():
                print(f"❌ Dosya yok: {path}")
                return 1
            cfg.data = replace(cfg.data, source="local", local_path=str(path))
            nerede = str(path)
    else:
        nerede = cfg.data.url if cfg.data.source == "url" else str(cfg.resolved_local_path())

    print(f"Kaynak : {nerede}")
    print(f"Tarih kolonu : {cfg.data.date_column}\n")

    store = MenuStore(cfg)
    gun_sayisi = store.reload()

    if gun_sayisi == 0:
        print("❌ Hiç gün okunamadı.")
        print(store.status)
        print("\nOlası sebepler:")
        print("  • Tarih kolonunun adı farklı (config.yaml > data.date_column)")
        print("  • İlk satır başlık satırı değil")
        print("  • Tarih biçimi tanınmıyor (beklenen: '1 Ekim 2026' veya '2026-10-01')")
        return 1

    span = store.date_span
    print(f"✅ {gun_sayisi} gün okundu")
    print(f"   Kapsam: {format_date_tr(span[0])}  →  {format_date_tr(span[1])}\n")

    # --- kolonlar ---------------------------------------------------------
    kolonlar = store.columns
    print(f"Dosyadaki kolonlar: {', '.join(kolonlar)}\n")

    eksik = [k for k in cfg.fields if k.strip().lower() not in kolonlar]
    kullanilmayan = [
        k for k in kolonlar
        if k not in {f.strip().lower() for f in cfg.fields}
        and k != cfg.data.date_column.strip().lower()
    ]

    print("Mesajda görünecek alanlar:")
    for kolon, baslik in cfg.fields.items():
        isaret = "✅" if kolon.strip().lower() in kolonlar else "❌"
        print(f"  {isaret} {baslik}   <- '{kolon}' kolonu")

    if eksik:
        print(f"\n⚠️  Bu kolonlar dosyada YOK: {', '.join(eksik)}")
        print("    Ya Excel'deki başlığı düzelt ya da config.yaml > fields'ı güncelle.")
    if kullanilmayan:
        print(f"\nℹ️  Dosyada olup mesajda gösterilmeyen: {', '.join(kullanilmayan)}")

    # --- boş hücreler -----------------------------------------------------
    bos_uyari = []
    for gun, satir in sorted(store.get_many([span[0] + timedelta(days=i)
                                             for i in range((span[1] - span[0]).days + 1)])):
        if satir is None:
            continue
        bos = [b for k, b in cfg.fields.items() if not satir.get(k.strip().lower())]
        if bos:
            bos_uyari.append((gun, bos))
    if bos_uyari:
        print(f"\n⚠️  {len(bos_uyari)} günde boş hücre var (o satır mesajda görünmez):")
        for gun, bos in bos_uyari[:5]:
            print(f"    {format_date_tr(gun)}: {', '.join(bos)}")
        if len(bos_uyari) > 5:
            print(f"    ... ve {len(bos_uyari) - 5} gün daha")

    # --- eksik iş günleri -------------------------------------------------
    eksik_gunler = []
    gun = span[0]
    while gun <= span[1]:
        if gun.weekday() < 5 and store.get(gun) is None:
            eksik_gunler.append(gun)
        gun += timedelta(days=1)
    if eksik_gunler:
        print(f"\nℹ️  Kapsam içinde {len(eksik_gunler)} hafta içi gün yok "
              "(resmi tatil ise normal):")
        for g in eksik_gunler[:10]:
            print(f"    {format_date_tr(g)}")
        if len(eksik_gunler) > 10:
            print(f"    ... ve {len(eksik_gunler) - 10} gün daha")

    # --- örnek mesaj ------------------------------------------------------
    print("\n" + "-" * 55)
    print("İLK GÜNÜN MESAJI:\n")
    print(strip_html(render_day(cfg, span[0], store.get(span[0]))))
    print("\n" + "-" * 55)
    print("SON GÜNÜN MESAJI:\n")
    print(strip_html(render_day(cfg, span[1], store.get(span[1]))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
