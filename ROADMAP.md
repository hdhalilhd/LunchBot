# Yol haritası

Durum: `[x]` bitti · `[ ]` sırada · **(sen)** senden bir şey gerekiyor

---

## Faz 0 — Ortam  ✅ bitti

- [x] Python 3.12.10 kuruldu (`winget`, kullanıcı kapsamı)
- [x] Git 2.55 kuruldu
- [x] `C:\Users\halii\menubot` altında sanal ortam + bağımlılıklar
      (python-telegram-bot 22.8, PyYAML, python-dotenv, pytz, httpx)

## Faz 1 — Çalışan taslak  ✅ bitti

- [x] CSV/JSON veri katmanı (yerel dosya **veya** URL, önbellek, hata toleransı)
- [x] Kural tabanlı soru çözümleme — AI yok: bugün / yarın / dün / öbür gün /
      gün isimleri / "24 eylül" / "24.09.2026" / bu hafta / haftaya
- [x] Mesaj şablonu (`config.yaml` → `fields` ile tamamen özelleştirilebilir)
- [x] Komutlar + serbest metin, **sadece özel sohbette**
- [x] Her sabah 08:00 (Europe/Istanbul) grup duyurusu — zamanlayıcı doğrulandı
- [x] `scripts/preview.py` — Telegram'a hiç bağlanmadan çıktıyı görme
- [x] 34 birim testi, hepsi geçiyor

## Faz 2 — Telegram'a bağlanma  ⬅️ **şimdi burdayız (sen)**

- [ ] **(sen)** BotFather'dan bot aç, token'ı `.env` içine yaz
- [ ] **(sen)** BotFather → `/setprivacy` → **Enable**
- [ ] **(sen)** Grubu kur, botu gruba ekle, `/chatid@BOTUN` ile grup id'sini al
- [ ] `.env` doldurulunca botu ayağa kaldır, özel sohbette test
- [ ] Sabah mesajını bir kez elle tetikleyip grupta doğrula
- [ ] **(sen)** Kendi kullanıcı id'ni `config.yaml` → `admins` listesine ekle

## Faz 3 — Gerçek veri

- [ ] **(sen)** Gerçek listeyi `data/menu.csv` biçimine dök
      (ya da mevcut Excel'ini ver, ben dönüştüreyim)
- [ ] Kolonlar netleşince `config.yaml` → `fields` güncelle
- [ ] Veriyi GitHub'a taşı, `data.source: url` yap
      → liste güncellemek için VM'e girmeye gerek kalmaz

## Faz 4 — VM'e taşıma

- [ ] **(sen)** VM'i aç (Ubuntu 22.04/24.04 yeter, 1 vCPU / 1 GB fazlasıyla yeterli)
- [ ] **(sen)** SSH erişimini ver
- [ ] `deploy/install-vm.sh` çalıştır → systemd servisi, açılışta otomatik başlar
- [ ] `journalctl -u menubot -f` ile ilk sabah mesajını izle
- [ ] Windows'taki kopyayı kapat (aynı token iki yerden çalışamaz)

## Faz 5 — İsteğe bağlı iyileştirmeler

- [ ] `/abone` — özel sohbette kişiye özel sabah mesajı
- [ ] Anket / "bugün yemeğe geliyor musun" butonları
- [ ] Menüde arama: "bu hafta köfte var mı"
- [ ] Yönetici komutuyla Telegram üzerinden gün güncelleme
- [ ] Hatalarda yöneticiye özel mesaj bildirimi
- [ ] Yalnızca gerekirse: anlaşılmayan sorular için LLM yedeği

---

## Bilinçli tasarım kararları

| Karar | Neden |
|---|---|
| AI yok, kural tabanlı | "Bugün ne var" için LLM israf: maliyet, gecikme, öngörülemezlik. Kurallar %100 tahmin edilebilir ve testlenebilir. |
| CSV ana format | Excel ve Sheets ile açılır; veriyi güncelleyecek kişinin kod bilmesi gerekmez. |
| Veri kaynağı URL olabilir | Liste güncellemek için VM'e SSH gerekmez. |
| Grup dinlenmiyor | Hem kodda (`ChatType.PRIVATE`) hem Telegram ayarında (`/setprivacy`) — çift kilit. |
| `fields` yapılandırılabilir | Aynı bot ders programı, nöbet listesi vb. için de çalışır. |
| systemd + `Restart=always` | VM yeniden başlasa da bot geri gelir. |
| Veri çekilemezse eldeki kullanılır | GitHub/Sheets bir an erişilemezse bot susmaz. |
