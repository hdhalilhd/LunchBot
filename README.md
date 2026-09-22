# MenuBot

Telegram botu. İki iş yapar:

1. **Özel sohbette** "bugün ne var", "yarın ne var", "çarşamba ne var", "24 eylül", "bu hafta" gibi sorulara cevap verir.
2. **Her sabah 08:00'de** belirlenen gruba o günün programını yazar.

Grupta bot **hiçbir mesaja cevap vermez** — gruba sadece sabah duyurusunu gönderir.

Yapay zeka kullanmaz. Soru anlama tamamen kural tabanlıdır (`app/nlu.py`), o yüzden
bedava, anında ve internetsiz çalışır.

---

## 1. Hızlı başlangıç (Windows, bu bilgisayar)

Python 3.12 ve sanal ortam zaten kurulu. Tek yapman gereken:

```powershell
cd C:\Users\halii\menubot

# Token olmadan mesajların nasıl görüneceğine bak:
.venv\Scripts\python.exe scripts\preview.py "bugün ne var"
.venv\Scripts\python.exe scripts\preview.py "bu hafta"
.venv\Scripts\python.exe scripts\preview.py --sabah

# İnteraktif deneme (bot varmış gibi yazışırsın):
.venv\Scripts\python.exe scripts\preview.py
```

Botu gerçekten çalıştırmak için önce `.env` lazım (bkz. bölüm 2), sonra:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

---

## 2. Telegram tarafı kurulumu

### 2.1 Bot oluştur

1. Telegram'da **@BotFather**'a yaz → `/newbot`
2. Bir isim ve `...bot` ile biten bir kullanıcı adı ver.
3. Sana verdiği **token**'ı kopyala (`123456789:AA...` biçiminde).

### 2.2 Botu gruptaki konuşmalara sağır yap

BotFather'da:

```
/setprivacy  →  botunu seç  →  Enable
```

Bu ayar açıkken bot, gruplardaki normal mesajları **hiç görmez**. Kod tarafında da
ayrıca engelli (`filters.ChatType.PRIVATE`), yani iki katmanlı koruma var.

### 2.3 .env dosyasını doldur

```powershell
Copy-Item .env.example .env
notepad .env
```

```
BOT_TOKEN=123456789:AA...
GROUP_CHAT_ID=-1001234567890
```

### 2.4 Grup id'sini öğren

1. Botu gruba ekle.
2. Gruba `/chatid@BOTKULLANICIADIN` yaz. (Privacy açık olsa bile komutlar bota ulaşır.)
3. Bot `chat_id: -100...` diye cevap verir → bunu `.env` içine yaz.

Bot henüz çalışmıyorsa alternatif:

```powershell
.venv\Scripts\python.exe scripts\chat_id.py
```

> `chat_id` grup için hep **eksi** ile başlar. `admins:` listesi boşken `/chatid`
> herkese açıktır; kurulum bitince kendi kullanıcı id'ni `config.yaml` içindeki
> `admins` listesine ekle.

---

## 3. Veri (yemek listesi)

`data/menu.csv` — Excel veya Google Sheets ile rahatça düzenlenir.

```csv
tarih,kahvalti,ogle,aksam,not
2026-09-22,"Omlet, Zeytin","Mercimek çorbası, Köfte, Makarna","Fırın tavuk, Sütlaç",Kermes var
```

Kurallar:

* **`tarih` kolonu zorunlu.** `2026-09-22`, `22.09.2026`, `22/09/2026` kabul edilir.
* Diğer kolonların adı sana kalmış. Mesajda görünmesini istediğin her kolonu
  `config.yaml` → `fields` altına ekle:

  ```yaml
  fields:
    kahvalti: "🍳 Kahvaltı"
    ogle: "🍽️ Öğle"
  ```

* Boş hücreler mesajda hiç görünmez.
* İçinde virgül olan hücreleri `"tırnak"` içine al.
* Yerel dosyada değişiklik yaptığında bot otomatik fark eder (dosya tarihine bakar).

JSON da desteklenir:

```json
{ "2026-09-22": { "ogle": "Köfte", "aksam": "Çorba" } }
```

> Bu yapı yemek listesine özel değil. `fields`'ı değiştirerek ders programı,
> nöbet listesi, etkinlik takvimi için de aynı botu kullanabilirsin.

### 3.1 Veriyi GitHub'dan çekmek

`menu.csv`'yi bir repoya koy, sonra `config.yaml`:

```yaml
data:
  source: url
  url: "https://raw.githubusercontent.com/KULLANICI/REPO/main/menu.csv"
  cache_ttl_minutes: 15
```

Artık listeyi güncellemek için VM'e girmene gerek yok — GitHub'da dosyayı
değiştirmen yeterli, bot en geç 15 dakikada yakalar (`/yenile` ile anında).

### 3.2 Veriyi Google Sheets'ten çekmek

Sheets'te: **Dosya → Paylaş → Web'de yayınla → CSV → Yayınla**.
Çıkan linki aynı şekilde `data.url` alanına yaz. API anahtarı gerekmez.

---

## 4. Komutlar

| Komut | Nerede | Ne yapar |
|---|---|---|
| `/start` | özel | Karşılama |
| `/bugun` | özel | Bugünün programı |
| `/yarin` | özel | Yarının programı |
| `/hafta` | özel | Bu haftanın tamamı |
| `/gun 24 eylül` | özel | Belirli bir gün |
| `/yardim` | özel | Örnek kullanımlar |
| `/chatid` | her yer | chat id + kullanıcı id (admin / kurulum modu) |
| `/yenile` | özel | Veriyi yeniden oku (admin) |
| `/durum` | özel | Saat, grup, zamanlayıcı, veri durumu (admin) |
| `/onizle` | özel | Sabah mesajının önizlemesi (admin) |

Komut yazmadan düz cümle de olur: "bugün ne var", "yarın menü nedir", "cuma",
"öbür gün", "1 ekim", "haftaya".

---

## 5. VM'e taşıma

Ubuntu/Debian bir VM'de:

```bash
git clone <repo-url> menubot   # ya da dosyaları scp ile kopyala
cd menubot
sudo bash deploy/install-vm.sh
sudo nano /opt/menubot/.env    # BOT_TOKEN ve GROUP_CHAT_ID
sudo systemctl restart menubot
journalctl -u menubot -f
```

Script şunları yapar: paketleri kurar, saat dilimini `Europe/Istanbul` yapar,
`menubot` adında servis kullanıcısı açar, `/opt/menubot` altına kurar, venv
oluşturur, systemd servisi olarak çalıştırır ve açılışta otomatik başlatır.

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
│   ├── datasource.py       # CSV/JSON + yerel/URL + önbellek
│   ├── nlu.py              # "bugün ne var" → tarih  (AI yok, kural tabanlı)
│   ├── render.py           # tarih + satır → Telegram mesajı
│   ├── handlers.py         # komutlar ve serbest metin
│   └── jobs.py             # her sabah 08:00 grup mesajı
├── data/menu.csv           # veri
├── scripts/
│   ├── preview.py          # Telegram'sız önizleme
│   ├── chat_id.py          # grup id bulma
│   └── run.ps1             # Windows'ta çalıştır
├── deploy/
│   ├── menubot.service     # systemd
│   └── install-vm.sh       # VM kurulumu
└── tests/test_nlu.py
```
