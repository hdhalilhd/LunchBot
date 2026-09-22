# Yol haritası

Durum: `[x]` bitti · `[ ]` sırada · **(sen)** senden bir şey gerekiyor

Bot: **@Lunchaibot** (id `000000000`, ad "Yemek-bot-ai")
Veri: [hdhalilhd/lunchnotice](https://github.com/hdhalilhd/lunchnotice) → `Yemek_Listesi.xlsx`

---

## Faz 0 — Ortam  ✅ bitti

- [x] Python 3.12.10 ve Git 2.55 kuruldu
- [x] `C:\Users\halii\menubot` altında sanal ortam + bağımlılıklar

## Faz 1 — Çalışan taslak  ✅ bitti

- [x] Veri katmanı: **.xlsx** / .csv / .json, yerel dosya **veya** URL, önbellek, hata toleransı
- [x] Kural tabanlı soru çözümleme — AI yok
- [x] Mesaj şablonu (`config.yaml` → `fields`)
- [x] Komutlar + serbest metin, **sadece özel sohbette**
- [x] Günlük duyuru işi (şu an kapalı, grup bekleniyor)
- [x] `scripts/preview.py` — Telegram'sız önizleme
- [x] 55 birim testi, hepsi geçiyor

## Faz 2 — Telegram bağlantısı  ✅ bitti

- [x] Bot token `.env` içinde (git'e girmiyor)
- [x] Gizlilik modu zaten **açık** — bot grup konuşmalarını okuyamıyor
      (`can_read_all_group_messages: false`). Ayrıca kodda da engelli.
- [x] Komut menüsü kuruldu (`scripts/set_commands.py`)
- [x] Admin id `000000000` tanımlı
- [ ] **(sen)** @Lunchaibot'a özel mesaj at, cevapları doğrula

## Faz 3 — Gerçek veri  ✅ bitti

- [x] `Yemek_Listesi.xlsx` doğrudan GitHub raw linkinden okunuyor —
      **iş akışın hiç değişmiyor**, Excel'i her ay yüklemeye devam et
- [x] Kolonlar eşlendi: Çorba / Ana Yemek / Yan / Ekstra
- [x] "22 Eylül 2026" biçimindeki Türkçe tarihler çözülüyor
- [ ] **(sen)** Ekim menüsünü yükle — elimizdeki veri **30 Eylül'de bitiyor**

## Faz 4 — Grup  ⬅️ **sırada (sen)**

- [ ] **(sen)** Grubu aç, @Lunchaibot'u ekle
- [ ] **(sen)** Gruba `/chatid@Lunchaibot` yaz → çıkan numarayı bana ver
- [ ] `.env` → `GROUP_CHAT_ID`, `config.yaml` → `daily_post.enabled: true`
- [ ] **Karar gerek:** eski GitHub Actions duyurusu kapatılsın mı?
      (bkz. aşağıdaki "Eski sistemle ilişki")

## Faz 5 — VM'e taşıma

- [ ] **(sen)** VM aç (Ubuntu 22.04/24.04, 1 vCPU / 1 GB yeter)
- [ ] **(sen)** SSH erişimi ver — anahtarı ben üretip public kısmını veririm
- [ ] `deploy/install-vm.sh` → systemd servisi, açılışta otomatik başlar
- [ ] Windows'taki kopyayı kapat (aynı token iki yerden **polling** yapamaz)

## Faz 6 — İsteğe bağlı

- [ ] Menüde arama: "bu hafta köfte var mı"
- [ ] Ay sonu yaklaşınca "yeni menüyü yükle" hatırlatması
- [ ] Hatalarda yöneticiye özel mesaj bildirimi
- [ ] Anket / "yemeğe geliyor musun" butonları

---

## Eski sistemle ilişki (lunchnotice + GitHub Actions)

Şubat 2026'dan beri çalışan bir kurulum var: GitHub Actions cron'u her gün
`menu_to_telegram.py` çalıştırıp menüyü gönderiyor. Bulgular:

**1. Cron saati tutmuyor.** Workflow'da `cron: "00 2 * * *"` yazıyor
(= 05:00 TSİ), yorumda "TSİ 07:08" deniyor, gerçekte son 10 çalışma
07:13–07:50 UTC arasında, yani **TSİ 10:13–10:50**. Workflow dosyasındaki
cron 13 kez değiştirilmiş — saat tutturulmaya çalışılıp başarılamamış.

Sebep: GitHub Actions'ın zamanlanmış işleri "en erken şu saatte" anlamına
gelir, garanti değildir; yoğunlukta saatlerce gecikir, bazen hiç çalışmaz.
**Sabit 08:00 istiyorsan VM'deki bot bunu kesin yapar** — asıl gerekçe bu.

**2. Yeşil çalışma ≠ mesaj gitti.** `send_telegram` hatayı yakalayıp
yalnızca `print` ediyor, çıkış kodu yine 0. 288 çalışmanın hepsi "success"
görünüyor ama bu, mesajın ulaştığını kanıtlamıyor.

**3. Kolon etiketleri kaymış.** Excel kolonları `Tarih | Gün | Çorba |
Ana Yemek | Yan | Ekstra`. Kodda `yard, tatli` değişkenlerine alınıp
mesajda "🥗 Yardımcı" ve "🍮 Tatlı/Meyve" diye yazılıyor; oysa içerik
"Yan" (pilav/makarna) ve "Ekstra" (tatlı + salata + içecek karışık).
Satır 50'deki "Ekstra çıkarıldı" yorumu da doğru değil — çıkarılmamış.
Yeni botta başlıklar gerçek kolon adlarıyla eşlendi.

**4. Kişisel id kodda açıkta.** `menu_to_telegram.py` içinde kendi
kullanıcı id'n (`000000000`) ve grup id'si sabit yazılı, repo public.
Grup id'si kritik değil ama id'lerin `.env`/secrets'ta durması daha iyi.

### Geçiş için iki seçenek

| | Eski (Actions) | Yeni (VM) |
|---|---|---|
| Sabah duyurusu | ~10:30 TSİ, kayan | 08:00 TSİ, sabit |
| "Bugün ne var" sorusu | yok | var |
| Maliyet | bedava | VM ücreti |
| Excel güncelleme | GitHub'a yükle | **aynı** |

Grup açıldığında ikisi birden açık kalırsa gruba **günde iki mesaj** gider.
Önerim: yeni bot grupta bir hafta sorunsuz çalıştıktan sonra Actions
workflow'unu devre dışı bırak (dosyayı silmeye gerek yok, GitHub arayüzünden
"Disable workflow" yeter — istersen geri açarsın).

---

## Bilinçli tasarım kararları

| Karar | Neden |
|---|---|
| AI yok, kural tabanlı | "Bugün ne var" için LLM israf: maliyet, gecikme, öngörülemezlik. Kurallar test edilebilir. |
| Excel doğrudan okunuyor | Mevcut iş akışın değişmesin; CSV'ye dönüştürme adımı yok. |
| Veri GitHub raw'dan | Menü güncellemek için VM'e SSH gerekmez. |
| Grup dinlenmiyor | Hem kodda (`ChatType.PRIVATE`) hem Telegram ayarında — çift kilit. |
| `fields` yapılandırılabilir | Kolon değişirse kod değil config değişir. |
| systemd + `Restart=always` | VM yeniden başlasa da bot geri gelir. |
| Veri çekilemezse eldeki kullanılır | GitHub bir an erişilemezse bot susmaz. |
