# 🏭 FabrikaOS — Kurulum ve Kullanım Rehberi

**Sürüm:** 1.0.0 (Faz 9 Kurumsal Sürüm)  
**Tarih:** Haziran 2026

---

## 1. Sisteme Giriş ve Kurulum (IT Personeli İçin)

FabrikaOS, fabrikanızın kapalı ağında (LAN) veya bulut sunucusunda çalışmak üzere tasarlanmıştır.

### 1.1. Gereksinimler

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **Python** | 3.11+ | 3.12+ |
| **RAM** | 2 GB | 4 GB+ |
| **Disk** | 500 MB | 2 GB+ |
| **İşletim Sistemi** | Windows 10 / Ubuntu 20.04 | Windows Server 2022 / Ubuntu 22.04 |
| **Redis** (opsiyonel) | 6.x | 7.x |
| **Tesseract OCR** (opsiyonel) | 5.x | 5.x |

### 1.2. Hızlı Kurulum (Geliştirme Ortamı)

```bash
# 1. Projeyi klonlayın
git clone https://github.com/Scryne/FabrikaOS.git
cd FabrikaOS

# 2. Sanal ortam oluşturun
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

# 3. Bağımlılıkları yükleyin
python -m pip install -r requirements.txt

# 4. .env dosyasını oluşturun
echo FLASK_APP=run.py > .env
echo FDYS_CONFIG=development >> .env
echo SECRET_KEY=super-gizli-kurumsal-anahtar-123 >> .env

# 5. Veritabanını ve demo verileri oluşturun
flask db upgrade
python seed_data.py

# 6. Sunucuyu başlatın
python run.py
```

Sistem `http://localhost:5000` adresinde aktif olacaktır.

### 1.3. Windows Üzerinde Üretim Ortamında Başlatma

1. Python 3.12+ sürümünün yüklü olduğundan emin olun.
2. Komut satırında proje ana klasörüne gidin.
3. Bağımlılıkları yükleyin: `python -m pip install -r requirements.txt`
4. `.env` dosyasında `FDYS_CONFIG=production` ve benzersiz `SECRET_KEY` ayarlayın.
5. Veritabanını oluşturun: `flask db upgrade && python seed_data.py`
6. `deployment` klasörü içindeki `run_server.bat` dosyasını çalıştırın.
7. Sunucu **http://localhost:8080** adresinde başlayacaktır.

> **Not:** Eğer eski bir sanal ortam başka bir klasörden taşındıysa, `pip` launcher'ı eski yolu tutabilir. Bu durumda `pip` yerine `python -m pip` kullanın veya sanal ortamı silip yeniden oluşturun.

> ⚠️ **Üretim ortamında** `SECRET_KEY` mutlaka değiştirilmelidir. Varsayılan anahtar ile production modda uygulama başlamayı reddeder.

### 1.4. Redis & Celery Kurulumu (Asenkron Görevler)

Asenkron görevler (bildirim gönderme, rapor oluşturma, arka plan işleri) için Redis ve Celery gereklidir:

#### Windows

```bash
# Redis'i Windows üzerinde çalıştırmak için Memurai veya WSL kullanabilirsiniz:
# WSL ile:
wsl -d Ubuntu -- redis-server

# Celery worker'ı başlatın (ayrı terminal):
celery -A celery_worker.celery worker --loglevel=info --pool=solo
```

#### Linux

```bash
# Redis yükleyin ve başlatın
sudo apt install redis-server
sudo systemctl start redis

# Celery worker'ı başlatın
celery -A celery_worker.celery worker --loglevel=info
```

#### .env Yapılandırması

```ini
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

> **Not:** Redis ve Celery opsiyoneldir. Kurulmadığında sistem yine çalışır, ancak asenkron görevler devre dışı kalır.

### 1.5. SMS Gateway Yapılandırması

Talep yönetimi ve bildirim modüllerinde SMS bildirimi göndermek için bir SMS gateway'i yapılandırın:

```ini
# .env dosyasına ekleyin:
SMS_GATEWAY_URL=https://api.sms-saglayici.com/send
SMS_API_KEY=sizin-api-anahtariniz
SMS_SENDER_ID=FABRIKA_OS
```

Desteklenen SMS sağlayıcıları:
- NetGSM
- İleti Merkezi
- Vodafone Toplu SMS
- Herhangi bir HTTP API tabanlı sağlayıcı

> **Not:** SMS yapılandırması opsiyoneldir. Ayarlanmadığında SMS bildirimleri gönderilmez, ancak diğer bildirim kanalları (e-posta, uygulama içi) çalışmaya devam eder.

### 1.6. E-posta Yapılandırması

Sistem bildirimlerini e-posta ile göndermek için SMTP ayarlarını admin panelinden veya doğrudan veritabanından yapılandırın:

1. **Admin panelinden:** Yönetici olarak giriş yapın → Ayarlar → E-posta Ayarları.
2. **Desteklenen protokoller:** SMTP, SMTP+TLS, SMTP+SSL.
3. **Önerilen sağlayıcılar:** Yandex İş, Gmail (uygulama şifresi ile), kurumsal SMTP.

### 1.7. OCR Yapılandırması (Doküman Tarama)

DYS modülünde doküman tarama ve metin çıkarma için Tesseract OCR'ı kurun:

#### Windows

```bash
# Tesseract'ı indirin ve kurun:
# https://github.com/UB-Mannheim/tesseract/wiki

# .env dosyasına Tesseract yolunu ekleyin:
OCR_ENGINE=tesseract
# Windows'ta tam yolu belirtmeniz gerekebilir:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

#### Linux

```bash
sudo apt install tesseract-ocr tesseract-ocr-tur
```

> **Not:** OCR opsiyoneldir. Kurulmadığında DYS modülü metin çıkarma olmadan çalışır.

### 1.8. Otomatik Yedekleme Ayarlama

Sistemin veritabanı ve yüklenen dosyaları her gün yedeklenmelidir.
- Görev Zamanlayıcı'yı (Task Scheduler) açın.
- Yeni bir görev oluşturun, tetikleyiciyi "Her gün gece 03:00" olarak ayarlayın.
- Eylem olarak `python.exe` yolunu seçin ve argüman olarak `deployment\backup.py` dosyasını gösterin.
- Yedekler ana klasördeki `backups` klasörüne ZIP olarak kaydedilir. En eski 7 gün silinir.

---

## 2. Kullanım Senaryoları (Yönetici ve Operatörler İçin)

### 2.1. Üretim ve OEE Takibi
- **Operatör:** Menüden "Makine & Üretim" modülüne girer. İlgili makineyi seçip "Vardiya Üretim Girişi" yapar. Hatasız ve hatalı parça sayısını, üretim süresini girer.
- **Sistem:** Otomatik olarak Kullanılabilirlik, Performans ve Kalite oranlarını çarparak OEE % değerini hesaplar.
- **Yönetici:** Dashboard üzerinden gerçek zamanlı OEE grafiklerini izler. Hedefin %10 altına düşüldüğünde bildirim alır.

### 2.2. Kalite ve Hata Girişi
- **Kalite Personeli:** "Kalite" modülünden 60 saniyede Hata Kaydı oluşturur.
- **Sistem:** Pareto analizi otomatik güncellenir. En çok karşılaşılan 5 hata tipi ısı haritasında gösterilir.
- **Teknisyen:** Gerektiğinde kök neden analizi yaparak "Düzeltici Faaliyet (CAPA)" başlatır.

### 2.3. İSG (İş Güvenliği) Uyarıları
- **Personel:** Sahada bir risk gördüğünde sisteme "Ramak Kala" olarak kaydeder.
- **İSG Uzmanı:** Riski 3x3 matris ile değerlendirir. Yüksek risk ise kırmızı alarm verilir ve Yöneticiye bildirim düşer.
- Eğitim süreleri dolmak üzere olan çalışanlar için sistem otomatik önleyici uyarı oluşturur.

### 2.4. CRM — Ortak ve Firma Yönetimi
- **Yönetici:** "CRM" modülünden ortak (malik/kiracı) ve firma kayıtlarını yönetir.
- **Yetkili ekleme:** Firma detayından "Yetkili Ekle" butonu ile firma yetkili kişilerini tanımlayın.
- **İletişim geçmişi:** Her ortak/firma ile yapılan görüşmeleri, notları ve iletişim kayıtlarını sisteme girin.
- **Harita görünümü:** Ortakların ve firmaların konum bilgilerini harita üzerinde görselleştirin.

### 2.5. Sözleşme Yönetimi
- **Yönetici:** "Sözleşmeler" modülünden kira kontratı, sigorta poliçesi veya genel sözleşme oluşturun.
- **Otomatik hatırlatma:** Sözleşme bitiş tarihi yaklaştığında sistem otomatik bildirim gönderir.
- **Standart metinler:** Sık kullanılan sözleşme maddelerini şablon olarak kaydedin ve hızlıca yeni sözleşmelere ekleyin.

### 2.6. Talep Yönetimi (Helpdesk)
- **Dahili talep:** Çalışanlar "Talepler" modülünden arıza bildirimi, öneri, şikayet veya bilgi talebi oluşturabilir.
- **Dış panel:** Müşteriler/vatandaşlar `dış panel` üzerinden TC Kimlik + telefon doğrulaması ile talep takibi yapabilir.
- **SMS bildirim:** Talep durum değişikliklerinde otomatik SMS gönderilir (SMS gateway yapılandırılmışsa).
- **Durum akışı:** `Açık → Yönlendirildi → Devam Ediyor → Çözüldü → Kapalı`

### 2.7. İnsan Kaynakları (İK)
- **Savunma/Tutanak:** Disiplin süreçleri için savunma ve tutanak kayıtları oluşturun.
- **Fazla Mesai:** Çalışan fazla mesai saatlerini takip edin ve onay akışını yönetin.
- **Sertifika Takibi:** Çalışan sertifika ve belge geçerlilik sürelerini izleyin. Süre dolmadan uyarı alın.
- **Zimmet:** Çalışanlara verilen ekipman ve malzemelerin zimmet kayıtlarını tutun.

### 2.8. Doküman Yönetim Sistemi (DYS)
- **Merkezi depo:** Tüm şirket dokümanlarını kategorize ederek tek bir yerden yönetin.
- **Sürüm kontrolü:** Doküman güncellemelerinin geçmişini takip edin.
- **Erişim kontrolü:** Departman ve rol bazlı doküman erişim yetkilendirmesi.

### 2.9. Duyuru Sistemi
- **Yönetici:** Şirket içi duyurular yayınlayın (acil, bilgilendirme, kutlama vb.).
- **Hedef kitle:** Duyuruları tüm şirkete veya belirli departmanlara yönlendirin.
- **Okunma takibi:** Hangi çalışanların duyuruyu okuduğunu raporlayın.

### 2.10. Satın Alma Yönetimi
- **Talep oluşturma:** İhtiyaç duyulan malzeme/hizmet için satın alma talebi açın.
- **Onay akışı:** Taleplerin yönetici onayından geçmesini sağlayın.
- **Teklif karşılaştırma:** Farklı tedarikçi tekliflerini yan yana karşılaştırın.
- **Sipariş takibi:** Onaylanan talepleri siparişe dönüştürün ve teslimat süreçlerini izleyin.

### 2.11. Bildirim Motoru
Sağ üst köşedeki Çan ikonundan şu konularda uyarı alırsınız:
- Stok minimum eşiğin altına düştüğünde.
- Makine arıza yaptığında veya bakım tarihi geldiğinde.
- Sözleşme bitiş tarihi yaklaştığında.
- Talep durumu değiştiğinde.
- 5 kez yanlış şifre denendiğinde (Güvenlik Uyarısı).

### 2.12. REST API Kullanımı
Üçüncü parti sistemlerle entegrasyon için REST API kullanabilirsiniz:
1. `POST /api/v1/auth/login` ile JWT token alın.
2. Token'ı `Authorization: Bearer <token>` başlığı ile gönderin.
3. Detaylı bilgi için: [`API_DOKUMANTASYONU.md`](API_DOKUMANTASYONU.md)

---

## 3. Yapılandırma Referansı

### 3.1. Ortam Değişkenleri (.env)

| Değişken | Açıklama | Varsayılan | Zorunlu |
|----------|----------|------------|---------|
| `FDYS_CONFIG` | Ortam seçimi | `development` | ✅ |
| `SECRET_KEY` | Flask gizli anahtar | — | ✅ (prod) |
| `DATABASE_URL` | Veritabanı bağlantı URI'si | SQLite | ❌ |
| `JWT_SECRET_KEY` | JWT imzalama anahtarı | — | ❌ |
| `CELERY_BROKER_URL` | Redis broker URL'si | `redis://localhost:6379/0` | ❌ |
| `CELERY_RESULT_BACKEND` | Celery sonuç deposu | `redis://localhost:6379/0` | ❌ |
| `SMS_GATEWAY_URL` | SMS API endpoint'i | — | ❌ |
| `SMS_API_KEY` | SMS API anahtarı | — | ❌ |
| `SMS_SENDER_ID` | SMS gönderici kimliği | `FABRIKA_OS` | ❌ |
| `OCR_ENGINE` | OCR motoru | `tesseract` | ❌ |
| `LOG_LEVEL` | Log seviyesi | `INFO` | ❌ |
| `SOCKETIO_CORS_ALLOWED_ORIGINS` | WebSocket CORS | `*` | ❌ |

### 3.2. Yapılandırma Modları

| Mod | Açıklama | Kullanım |
|-----|----------|----------|
| `development` | Debug açık, gevşek rate limit | Geliştirme |
| `production` | Debug kapalı, güvenlik sıkılaştırma | Canlı ortam |
| `testing` | In-memory SQLite, CSRF kapalı | Test suite |

---

> Lütfen teknik sorunlar için Bilgi İşlem departmanı ile iletişime geçin.
> Daha detaylı yapılandırma ayarları `config.py` üzerinden yapılmaktadır.
