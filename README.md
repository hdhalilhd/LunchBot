# MenuBot — @Lunchaibot

Telegram botu. İki iş yapar:

1. **Özel sohbette** "bugün ne var", "yarın ne var", "çarşamba ne var",
   "24 eylül", "bu hafta" gibi sorulara cevap verir.
2. **Her sabah 08:00'de** belirlenen gruba o günün menüsünü yazar.
   *(Şu an kapalı — grup açılınca devreye girecek.)*

Grupta bot **hiçbir mesaja cevap vermez**; gruba sadece sabah duyurusunu gönderir.

Yapay zeka kullanmaz. Soru anlama tamamen kural tabanlıdır ([app/nlu.py](app/nlu.py)),
o yüzden bedava, anında ve öngörülebilir çalışır.

Menü verisi [hdhalilhd/lunchnotice](https://github.com/hdhalilhd/lunchnotice)
reposundaki `Yemek_Listesi.xlsx` dosyasından **doğrudan** okunur — Excel'i her ay
GitHub'a yükleme alışkanlığın aynen devam eder, dönüştürme adımı yok.

---

## 1. Çalıştırma (Windows)

```powershell
cd C:\Users\halii\menubot
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

Durdurmak için Ctrl+C. Aynı anda **tek** yerde çalışmalı (iki polling çakışır).

### Telegram'sız önizleme

Bot çalışmıyorken bile çıktıyı görebilirsin:

```powershell
.venv\Scripts\python.exe scripts\preview.py "bugün ne var"
.venv\Scripts\python.exe scripts\preview.py "bu hafta"
.venv\Scripts\python.exe scripts\preview.py --sabah      # sabah mesajı önizlemesi
.venv\Scripts\python.exe scripts\preview.py              # interaktif
```

---

## 2. Kullanım

Özel sohbette düz cümle yeter: "bugün ne var", "yarın menü nedir", "cuma",
"öbür gün", "1 ekim", "haftaya cuma", "bu hafta".

| Komut | Nerede | Ne yapar |
|---|---|---|
| `/start` | özel | Karşılama |
| `/bugun` | özel | Bugünün menüsü |
| `/yarin` | özel | Yarının menüsü |
| `/hafta` | özel | Bu haftanın tamamı |
| `/gun 24 eylül` | özel | Belirli bir gün |
| `/yardim` | özel | Örnek kullanımlar |
| `/chatid` | her yer | chat id + kullanıcı id (admin) |
| `/yenile` | özel | Veriyi yeniden oku (admin) |
| `/durum` | özel | Saat, zamanlayıcı, veri kapsamı (admin) |
| `/onizle` | özel | Sabah mesajının önizlemesi (admin) |

Komut menüsünü değiştirmek için `scripts/set_commands.py`.

---

## 3. Veri

Kaynak [config.yaml](config.yaml) içinde:

```yaml
data:
  source: url
  url: "https://raw.githubusercontent.com/hdhalilhd/lunchnotice/main/Yemek_Listesi.xlsx"
  cache_ttl_minutes: 15
  date_column: Tarih
```

Excel'i GitHub'da güncelledin mi bot en geç 15 dakikada görür; beklemek
istemezsen özel sohbette `/yenile` yaz.

### Kolonlar

Excel'in ilk satırı başlık olmalı. Şu an:

```
Tarih | Gün | Çorba | Ana Yemek | Yan | Ekstra
```

Mesajda hangi kolonun hangi başlıkla görüneceği [config.yaml](config.yaml) → `fields`:

```yaml
fields:
  "çorba": "🍲 Çorba"
  "ana yemek": "🍽️ Ana Yemek"
  "yan": "🥗 Yan"
  "ekstra": "🍮 Ekstra"
```

* Kolon adında büyük/küçük harf farkı önemsiz.
* `fields`'a yazmadığın kolon mesajda görünmez (`Gün` bilerek dışarıda —
  tarih satırı zaten günü yazıyor).
* Boş hücreler atlanır.
* Kolon eklersen/çıkarırsan **kod değil sadece bu liste** değişir.

### Tarih biçimi

`22 Eylül 2026` (mevcut biçim), `2026-09-22`, `22.09.2026`, `22/09/2026` ve
Excel'in gerçek tarih hücreleri — hepsi çalışır.

### Yeni ay menüsü geldiğinde

Akış aynı kalıyor — Excel'i [lunchnotice](https://github.com/hdhalilhd/lunchnotice)
reposuna `Yemek_Listesi.xlsx` adıyla yükle, bot otomatik görür.

Yüklemeden **önce** kontrol et:

```powershell
.venv\Scripts\python.exe scripts\kontrol.py "C:\yol\Ekim_Menu.xlsx"
```

Bu komut kaç gün okunduğunu, kolonların eşleşip eşleşmediğini, boş hücreleri,
eksik iş günlerini ve örnek mesajı gösterir. Hepsi ✅ ise yükleyebilirsin.

Yükledikten sonra bota `/yenile` yaz (yoksa 15 dakika bekler), sonra `/durum`
ile kapsamı doğrula.

Dikkat edilecekler:

* Dosya adı **aynı** olmalı: `Yemek_Listesi.xlsx`
* İlk satır başlık olmalı, başlıklar aynı kalmalı
* Tarih biçimi `1 Ekim 2026` (mevcut biçim) — gün adı Türkçe ay adıyla

### Alternatif kaynaklar

* **Yerel dosya:** `source: local` + `local_path: data/Yemek_Listesi.xlsx`
* **Google Sheets:** Dosya → Paylaş → Web'de yayınla → CSV; çıkan linki `url`'e yaz
* **CSV / JSON:** aynı şekilde okunur ([data/menu.csv](data/menu.csv) örnek biçim)

> ⚠️ Elimizdeki veri **30 Eylül 2026'da bitiyor.** Ekim menüsü yüklenmezse
> bot o tarihten sonra "menü bulamadım" der.

---

## 4. Grup açılınca yapılacaklar

1. Grubu kur, @Lunchaibot'u ekle.
2. Gruba `/chatid@Lunchaibot` yaz → çıkan `-100...` numarasını al.
3. `.env` içine `GROUP_CHAT_ID=-100...` yaz.
4. [config.yaml](config.yaml) → `daily_post.enabled: true`.
5. Botu yeniden başlat, `/onizle` ile kontrol et.

Gizlilik modu zaten açık (`can_read_all_group_messages: false`), yani bot
gruptaki konuşmaları **göremez**. Kodda da ayrıca engelli — çift kilit.

Eski GitHub Actions duyurusu hâlâ aktifse gruba günde iki mesaj gider;
[ROADMAP.md](ROADMAP.md) içindeki "Eski sistemle ilişki" bölümüne bak.

---

## 5. VM'e taşıma

VM kodu **GitHub'dan** çeker. Kod değişince VM'e dosya kopyalamazsın;
buradan push edersin, VM çeker.

### İlk kurulum (VM'de, bir kez)

```bash
sudo apt update && sudo apt install -y git
sudo git clone https://github.com/KULLANICI/menubot /opt/menubot
sudo bash /opt/menubot/deploy/install-vm.sh
sudo nano /opt/menubot/.env      # BOT_TOKEN, ADMIN_IDS, GROUP_CHAT_ID
sudo systemctl start menubot
journalctl -u menubot -f
```

Script paketleri kurar, saat dilimini `Europe/Istanbul` yapar, `menubot`
servis kullanıcısı açar, venv kurar, systemd servisi olarak açılışta
otomatik başlatır.

### Güncelleme

Windows'ta değiştir → `git push` → VM'de:

```bash
sudo /opt/menubot/deploy/update.sh
```

Script `git pull` yapar, **değişiklik yoksa hiçbir şey yapmaz**,
`requirements.txt` değiştiyse bağımlılıkları kurar, systemd dosyası
değiştiyse yeniden yükler, sonra botu yeniden başlatır ve gerçekten
ayağa kalktığını doğrular.

### Otomatik güncelleme (isteğe bağlı)

```bash
sudo systemctl enable --now menubot-update.timer
```

10 dakikada bir GitHub'ı kontrol eder, değişiklik varsa çeker ve yeniden
başlatır. Kapatmak için `sudo systemctl disable --now menubot-update.timer`.

> `.env` git'te değildir, VM'de kalır. Güncellemeler ona dokunmaz — token'ı
> tekrar tekrar girmezsin.

### Faydalı komutlar

```bash
journalctl -u menubot -f                    # canlı log
journalctl -u menubot-update --since today  # güncelleme geçmişi
sudo systemctl restart menubot              # yeniden başlat
systemctl list-timers menubot-update        # sonraki kontrol ne zaman
```

---

## 6. Test

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

---

## 7. Dosya düzeni

```
menubot/
├── bot.py                  # giriş noktası
├── config.yaml             # ayarlar (gizli olmayan)
├── .env                    # BOT_TOKEN, GROUP_CHAT_ID  (git'e girmez)
├── requirements.txt
├── app/
│   ├── config.py           # ayar okuma
│   ├── datasource.py       # xlsx/csv/json + yerel/URL + önbellek
│   ├── nlu.py              # "bugün ne var" → tarih  (AI yok)
│   ├── render.py           # tarih + satır → Telegram mesajı
│   ├── handlers.py         # komutlar ve serbest metin
│   └── jobs.py             # her sabah 08:00 grup mesajı
├── data/
│   ├── Yemek_Listesi.xlsx  # yerel yedek kopya
│   └── menu.csv            # CSV biçimi örneği
├── scripts/
│   ├── preview.py          # Telegram'sız önizleme
│   ├── set_commands.py     # komut menüsü
│   ├── chat_id.py          # grup id bulma
│   └── run.ps1             # Windows'ta çalıştır
├── deploy/
│   ├── menubot.service     # systemd
│   └── install-vm.sh       # VM kurulumu
└── tests/                  # 55 test
```
