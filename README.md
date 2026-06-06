<div align="center">

  <br>

  <img src="https://raw.githubusercontent.com/Scryne/FabrikaOS/main/app/static/images/logo.png" alt="FabrikaOS Logo" width="140" onerror="this.src='https://via.placeholder.com/140/0f172a/38bdf8?text=FOS'"/>

  <br><br>

  # ⚙️ FabrikaOS

  **Fabrikanızın Dijital Beyni — Açık Kaynaklı MES + ERP Platformu**

  <br>

  *Yapay zeka destekli, gerçek zamanlı, kendi sunucunuzda çalışan*
  *metal ve ağır sanayi tesisleri için üretim yönetim sistemi.*

  <br>

  [![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![AI](https://img.shields.io/badge/AI-scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
  [![Realtime](https://img.shields.io/badge/Realtime-Socket.IO-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://socket.io/)
  [![License](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](#-lisans)

  <br>

  [🚀 Hızlı Başlangıç](#-hızlı-başlangıç--5-dakikada-çalışır) · [📸 Ekran Görüntüleri](#-ekran-görüntüleri) · [🤖 Yapay Zeka](#-yapay-zeka-motorları) · [🔑 Demo Hesaplar](#-demo-hesapları) · [📖 API](API_DOKUMANTASYONU.md)

</div>

<br>

---

<br>

## 📌 İçindekiler

- [Ne İşe Yarar?](#-ne-i̇şe-yarar)
- [Neden FabrikaOS?](#-neden-fabrikaos)
- [Ekran Görüntüleri](#-ekran-görüntüleri)
- [Modüller](#-27-entegre-modül)
- [Yapay Zeka Motorları](#-yapay-zeka-motorları)
- [Teknik Mimari](#-teknik-mimari)
- [Güvenlik](#-güvenlik--owasp-standartlarında)
- [Tasarım Sistemi](#-tasarım-sistemi--cinematic-industrial)
- [Hızlı Başlangıç](#-hızlı-başlangıç--5-dakikada-çalışır)
- [Demo Hesapları](#-demo-hesapları)
- [REST API](#-rest-api)
- [Demo Senaryosu](#-demo-senaryosu)
- [Test](#-test)
- [Deployment](#-deployment-üretim-ortamı)
- [Katkıda Bulunma](#-katkıda-bulunma)
- [Lisans](#-lisans)

<br>

---

<br>

## 💡 Ne İşe Yarar?

Türkiye'deki orta ve büyük ölçekli metal sanayi tesislerinin **%68'i** hâlâ üretim verilerini Excel'de, bakım planlarını beyaz tahtada, stok takibini kağıt üzerinde yönetiyor. Sonuç:

| Sorun | Gerçek Maliyet |
|:------|:---------------|
| ⏱️ Plansız makine duruşları | Yılda **240+ saat** üretim kaybı |
| 📋 Elle veri girişi ve raporlama | Haftalık **12+ adam-saat** israf |
| 🔧 "Kırıldığında tamir et" yaklaşımı | Arıza maliyetleri planlı bakımdan **3-5×** fazla |
| 📦 Stok görünmezliği | Acil siparişlerden **%15-25** maliyet artışı |
| 🛡️ İSG uyumsuzluğu | Yasal riskler, para cezaları, iş kazaları |

**FabrikaOS (FDYS — Fabrika Dijital Yönetim Sistemi)**, metal ve ağır sanayi tesisleri için sıfırdan tasarlanmış bir **MES (Manufacturing Execution System)** ve **ERP (Enterprise Resource Planning)** hibrit platformudur. Tüm fabrika verileri tek bir karanlık komuta merkezinde toplanır; yapay zeka arızaları önceden tahmin eder, gerçek zamanlı OEE takibi verimliliği görünür kılar, 27 entegre modül hammaddeden sevkiyata kadar her adımı dijitalleştirir.

**Tek cümleyle:** *Fabrikanızın her saniyesini ölçülebilir kılan dijital komuta merkezi.*

<br>

---

<br>

## 🏆 Neden FabrikaOS?

<div align="center">

| Özellik | FabrikaOS | Geleneksel ERP | Rakip MES Çözümleri |
|:--------|:---------:|:--------------:|:-------------------:|
| **Yapay Zeka Tahminleme** | ✅ 4 ayrı AI motoru | ❌ | ⚠️ Kısıtlı |
| **Gerçek Zamanlı (WebSocket)** | ✅ <1 sn gecikme | ❌ Dakikalarca | ⚠️ Polling |
| **İnteraktif Fabrika Haritası** | ✅ SVG Dijital İkiz | ❌ | ❌ |
| **REST API (JWT)** | ✅ Tam CRUD + Sayfalama | ⚠️ Ek modül | ⚠️ Kısıtlı |
| **Türkçe Tam Destek** | ✅ Doğal Türkçe | ⚠️ Çeviri kalitesi | ❌ |
| **Self-hosted** | ✅ Veriniz sizde kalır | ❌ SaaS kilidi | ⚠️ |
| **Rol Tabanlı Erişim (RBAC)** | ✅ 8+ rol, modül bazlı | ⚠️ Temel | ⚠️ Kısıtlı |
| **Kurulum Süresi** | ✅ **5 dakika** | ❌ Haftalarca | ❌ Günlerce |
| **Maliyet** | ✅ **Ücretsiz / MIT** | ❌ 6-7 haneli lisans | ❌ Yıllık ücret |

</div>

<br>

---

<br>

## 📸 Ekran Görüntüleri

> *Görmeden inanmam diyenler için — FabrikaOS'un gerçek arayüzünden kesitler.*

<br>

### 🖥️ Yönetici Dashboard'u

Tüm KPI'lar, AI uyarıları ve modül özetleri tek bir ekranda. Aktif personel sayısı, haftalık OEE trendi, kritik stok durumu, hata oranları ve yapay zeka asistanı — hepsi aynı bakışta.

<div align="center">
  <img src="docs/screenshots/dashboard_admin.png" alt="FabrikaOS Yönetici Dashboard — KPI şeridi, AI asistanı ve canlı OEE göstergesi" width="900"/>
  <br><em>Yönetici Dashboard — Fabrikanın 360° komuta merkezi</em>
</div>

<br>

### 🏭 İnteraktif Fabrika Haritası — Dijital İkiz

Fabrika zemininin SVG tabanlı, sürükle-bırak destekli dijital kopyası. Makinelerin anlık durumunu renk kodlarıyla gösterir:
🟢 Çalışıyor · 🟡 Bakımda · 🔴 Arızalı · ⚫ Kapalı

<div align="center">
  <img src="docs/screenshots/fabrika_harita.png" alt="FabrikaOS İnteraktif Fabrika Haritası — Dijital İkiz" width="900"/>
  <br><em>Fabrika Haritası — Sahanın canlı dijital ikizi</em>
</div>

<br>

### 🤖 AI Tahminleme Motoru

scikit-learn tabanlı 4 ayrı AI motoru: kestirimci bakım risk skorları, OEE trend tahminleri, stok tüketim öngörüleri ve anomali tespiti.

<div align="center">
  <img src="docs/screenshots/ai_tahmin.png" alt="FabrikaOS AI Tahminleme — Kestirimci bakım ve OEE trend analizi" width="900"/>
  <br><em>Yapay Zeka Motoru — Arıza riskini gün bazında tahmin eder</em>
</div>

<br>

### 📊 Gelişmiş Analitik Paneli

Operatör-makine performans matrisleri, korelasyon analizleri, vardiya bazlı hata trendleri ve maliyet dağılımları.

<div align="center">
  <img src="docs/screenshots/analitik_panel.png" alt="FabrikaOS Gelişmiş Analitik — Korelasyon matrisi ve trend analizi" width="900"/>
  <br><em>Gelişmiş Analitik — Veriden stratejiye</em>
</div>

<br>

### 📺 Kiosk Modu

Dev ekranlar, dokunmatik terminaller veya TV'ler için optimize edilmiş tam ekran görünüm. Otomatik yenilenen canlı veriler ve kayan uyarı yazıları.

<div align="center">
  <img src="docs/screenshots/kiosk_mode.png" alt="FabrikaOS Kiosk Modu — Tam ekran üretim takibi" width="900"/>
  <br><em>Kiosk Modu — Fabrika zemini için tasarlandı</em>
</div>

<br>

### ⚙️ Makine & Üretim Takibi

Tüm makine parkı tek ekranda: marka, model, kapasite, OEE hedefi, son bakım tarihi ve konum bilgisi.

<div align="center">
  <img src="docs/screenshots/makine_listesi.png" alt="FabrikaOS Makine Listesi — Tüm makine parkı" width="900"/>
  <br><em>Makine Parkı — Her şey kontrol altında</em>
</div>

<br>

---

<br>

## 🧩 27 Entegre Modül

FabrikaOS, birbirine bağlı **27 Blueprint modülü** ile fabrikanın tamamını tek platformda yönetir. Her modül bağımsız çalışabilir; asıl güç tüm modüllerin ortak veri havuzunu paylaşmasından gelir.

<br>

<div align="center">

```
╔═══════════════════════════════════════════════════════════════════╗
║                     🏭  FabrikaOS Modül Haritası                  ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ ║
║  │  ÜRETİM & OEE    │  │  BAKIM & İŞ EMRİ │  │  KALİTE & İSG   │ ║
║  │  ► Makine Takibi  │  │  ► Kestirimci     │  │  ► CAPA          │ ║
║  │  ► Üretim Girişi  │  │  ► Arıza Kayıt    │  │  ► Risk Değrl.   │ ║
║  │  ► OEE Motoru     │  │  ► Periyodik      │  │  ► Eğitim Takip  │ ║
║  │  ► Kiosk Modu     │  │  ► SLA Takibi     │  │  ► Kaza Kayıt    │ ║
║  └──────────────────┘  └──────────────────┘  └─────────────────┘ ║
║                                                                   ║
║  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ ║
║  │  STOK & TEDARİK  │  │  CRM & SÖZLEŞME  │  │  İNSAN          │ ║
║  │  ► Malzeme Takip  │  │  ► Firma Yönetim  │  │  KAYNAKLARI     │ ║
║  │  ► Satın Alma     │  │  ► Ortak Yönetim  │  │  ► Personel     │ ║
║  │  ► Tedarikçi Dğl. │  │  ► Kontrat Takip  │  │  ► İzin/Mesai   │ ║
║  │  ► AI Stok Tahmin │  │  ► Talep (Help)   │  │  ► Zimmet/Belge │ ║
║  └──────────────────┘  └──────────────────┘  └─────────────────┘ ║
║                                                                   ║
║  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ ║
║  │  AI & ANALİTİK   │  │  DİJİTAL İKİZ    │  │  KURUMSAL       │ ║
║  │  ► 4 AI Motoru    │  │  ► Fabrika Harita │  │  ► DYS (Doküm.) │ ║
║  │  ► Korelasyon     │  │  ► Site Harita    │  │  ► Duyuru Sist. │ ║
║  │  ► KPI Dashboard  │  │  ► Leaflet.js     │  │  ► Bildirim Mot.│ ║
║  │  ► PDF/Excel Rap. │  │  ► Sürükle-Bırak  │  │  ► REST API     │ ║
║  └──────────────────┘  └──────────────────┘  └─────────────────┘ ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

</div>

<br>

### Modül Detayları

<details>
<summary><strong>🏭 Üretim & OEE Motoru</strong> — Fabrikanın kalp atışı</summary>

<br>

Üretim hattındaki her makineyi, her vardiyayı, her parçayı takip eder. **OEE (Overall Equipment Effectiveness)** formülüyle anlık verimlilik hesaplar:

```
OEE = Kullanılabilirlik × Performans × Kalite

Kullanılabilirlik = (Planlanan Üretim − Duruş Süresi) / Planlanan Üretim
Performans        = (Gerçekleşen Üretim × İdeal Çevrim) / Çalışma Süresi
Kalite            = (Toplam Üretim − Fire) / Toplam Üretim
```

- 📊 **Dinamik OEE Göstergesi** — Makine bazlı, vardiya bazlı, gün bazlı canlı hesaplama
- 📺 **Kiosk Modu** — Fabrika zemininde dev ekranlarda, otomatik yenilenen üretim verileri
- ⚡ **Socket.IO** — <1 saniye gecikmeyle anlık WebSocket veri akışı
- 📈 **Trend Grafikleri** — Chart.js ile etkileşimli verimlilik grafikleri
- 🎯 **Hedef Takibi** — Makine başına OEE hedefi belirleme ve sapma analizi

</details>

<details>
<summary><strong>🤖 Yapay Zeka & Tahminleme</strong> — 4 ayrı AI motoru</summary>

<br>

| AI Motoru | Algoritma | Ne Yapar? |
|:----------|:----------|:----------|
| **Kestirimci Bakım** | Regresyon + Trend Analizi | Makine arıza olasılığını **gün bazında** tahmin eder |
| **OEE Trend Analizi** | Zaman Serisi | Gelecek dönem **verimlilik düşüşlerini** önceden bildirir |
| **Stok Tahmin** | Tüketim Trendi | **Kritik stok seviyelerini** haftalarca önce uyarır |
| **Anomali Tespiti** | İstatistiksel Sapma | Üretim verilerindeki **anormallikleri** anında yakalar |

**Bonus — AI Operatör Eşleştirme:** İş emri oluşturulurken operatörlerin geçmiş performansı (OEE, hata oranı) ve işin gereksinimleri (zorluk seviyesi, beceri seti) analiz edilerek en uygun personel yapay zeka ile otomatik eşleştirilir.

</details>

<details>
<summary><strong>🗺️ Dijital İkiz & Fabrika Haritası</strong> — Sahanın canlı kopyası</summary>

<br>

- **SVG tabanlı** interaktif fabrika planı — donanım hızlandırmalı CSS transform animasyonları
- **Sürükle-bırak** ile makine konumlandırma — düzen düzenleme modu
- **Renk kodlu** durum göstergeleri: 🟢 Çalışıyor | 🟡 Bakımda | 🔴 Arızalı | ⚫ Kapalı
- **Hover** ile anlık makine detay kartları (OEE, son arıza, bakım tarihi, mevcut operatör)
- **Leaflet.js** tabanlı site haritası ve alan yönetimi modülü (coğrafi konum bazlı görselleştirme)

</details>

<details>
<summary><strong>📋 İş Emri & Bakım Yönetimi</strong> — SLA takipli iş akışları</summary>

<br>

- Öncelik seviyeleri: `Düşük → Orta → Yüksek → Kritik`
- **SLA (Service Level Agreement)** takibi ile süre aşımı bildirimleri
- Durum akışı: `Oluşturuldu → Atandı → Devam Ediyor → Tamamlandı`
- İş emri yorumları ve tam aktivite geçmişi (audit trail)
- AI destekli operatör atama önerisi (beceri-iş eşleştirme)
- Periyodik bakım takvimi ve otomatik hatırlatıcılar

</details>

<details>
<summary><strong>👥 CRM, Sözleşme & Talep Yönetimi</strong> — Paydaş ilişkileri</summary>

<br>

- **CRM:** Firma ve ortak yönetimi, yetkili kişiler, iletişim geçmişi, sektör bazlı filtreleme
- **Sözleşme:** Kira kontratı, sigorta poliçesi, hizmet sözleşmeleri; otomatik yenileme ve süre bitiş hatırlatma
- **Talep (Helpdesk):** Arıza, öneri, şikayet, bilgi talebi — tam yaşam döngüsü yönetimi
- **Dış Panel:** Müşteri / tedarikçi / taşeron için kimlik doğrulamalı self-servis portal
- **Bildirim:** SMS ve e-posta bildirim entegrasyonu

</details>

<details>
<summary><strong>👔 İnsan Kaynakları & İSG</strong> — Yasal uyum</summary>

<br>

**İK Modülü:**
- Personel özlük dosyası yönetimi, savunma/tutanak sistemi
- Fazla mesai takibi, maaş skalası yönetimi
- Sertifika ve belge takip sistemi (sürüm kontrolü)
- Zimmet kayıtları, giriş-çıkış evrak takibi, yıllık izin yönetimi

**İSG Modülü:**
- İş kazası ve ramak kala olay kayıtları (detaylı form)
- Risk değerlendirme matrisi (Olasılık × Şiddet = Risk Skoru)
- İSG eğitim takibi, sağlık muayenesi periyot yönetimi
- Güvenlik skoru hesaplama ve İSG dashboard'u

</details>

<details>
<summary><strong>📦 Stok, Satın Alma & Enerji</strong> — Tedarik zinciri</summary>

<br>

- Malzeme giriş-çıkış hareketleri, kritik stok uyarıları ve min/max seviye yönetimi
- AI destekli stok tüketim tahmini (haftalık/aylık öngörü)
- Satın alma talebi oluşturma ve çok adımlı onay akışı (talep → teklif → sipariş)
- Teklif karşılaştırma, tedarikçi performans değerlendirme ve puanlama
- Makine bazlı enerji tüketim izleme (5 farklı enerji türü: elektrik, doğalgaz, su, basınçlı hava, buhar)
- Aylık/yıllık tüketim trend analizi ve maliyet raporlama

</details>

<details>
<summary><strong>📄 DYS, Duyuru & Raporlama</strong> — Kurumsal iletişim</summary>

<br>

- **Doküman Yönetim Sistemi (DYS):** Merkezi doküman deposu, sürüm kontrolü, erişim kontrolü, dosya kategorileri
- **Duyuru Sistemi:** Şirket içi duyuru yayınlama, okunma takibi, hedef kitle belirleme (tüm şirket / departman / kişi)
- **Raporlama:** PDF rapor oluşturma (ReportLab), Excel dışa aktarma (openpyxl), Chart.js grafikleri
- **Bildirim Motoru:** Toast notification (anlık), e-posta ve SMS bildirim altyapısı
- **Takvim:** Bakım planları, İSG eğitimleri ve vardiya planlarının takvim görünümü

</details>

<br>

---

<br>

## 🤖 Yapay Zeka Motorları

FabrikaOS'un AI motorları, geleneksel "kırıldığında tamir et" yaklaşımını ortadan kaldırır ve **proaktif, veriye dayalı karar almayı** fabrikanın DNA'sına işler.

<br>

<div align="center">

```
                      ╭──────────────────────────────────╮
                      │         📡 VERİ TOPLAMA           │
                      │    Üretim · Sensör · Arıza        │
                      │    Bakım · Enerji · Kalite         │
                      ╰───────────────┬──────────────────╯
                                      │
                                      ▼
                      ╭──────────────────────────────────╮
                      │       🧠 4 AI MOTORU ANALİZ       │
                      │                                  │
                      │   🔧 Kestirimci Bakım             │
                      │   📈 OEE Trend Tahmin             │
                      │   📦 Stok Tüketim Tahmin          │
                      │   ⚠️  Anomali Tespiti              │
                      ╰───────────────┬──────────────────╯
                                      │
                                      ▼
                      ╭──────────────────────────────────╮
                      │       🎯 PROAKTİF EYLEM           │
                      │                                  │
                      │   → Bakım planla (14 gün önce)    │
                      │   → Stok siparişi tetikle         │
                      │   → Operatör ata (AI eşleşme)     │
                      │   → Yöneticiyi uyar (dashboard)   │
                      ╰──────────────────────────────────╯
```

</div>

<br>

### Hedeflenen İyileşmeler

| Metrik | İyileşme |
|:-------|:--------:|
| ⏱️ Plansız duruş süresinde azalma | **%30+** |
| 📈 OEE artışı | **%15-25** |
| 🔧 Bakım maliyetinde düşüş | **%20+** |
| 📋 Raporlama süresinde kısalma | **%80+** |
| 🛡️ İSG uyum oranı | **%100** |

<br>

### AI Modül Dosya Yapısı

```
app/services/ai/
├── kestirimci_bakim.py    # Makine arıza olasılığı — regresyon + trend
├── oee_tahmin.py          # OEE verimlilik tahmini — zaman serisi
├── stok_tahmin.py         # Stok tüketim öngörüsü — tüketim trendi
└── anomali_tespit.py      # Üretim anomali tespiti — istatistiksel sapma
```

<br>

---

<br>

## 🏛️ Teknik Mimari

FabrikaOS, kurumsal düzeyde ölçeklenebilir bir mimari üzerine inşa edilmiştir. Her katman bağımsız test edilebilir, bakım yapılabilir ve genişletilebilir.

<br>

### Mimari Genel Bakış

```mermaid
graph TD
    Client["🖥️ Web Tarayıcı / 📱 Tablet / 📺 Kiosk"]
    API["🔌 REST API İstemcisi (JWT)"]
    Web["⚡ Gunicorn + Eventlet WSGI"]
    App["🏭 FabrikaOS Core — Flask 3.1"]
    DB[("💾 SQLite WAL / PostgreSQL")]
    Cache[("⚡ Redis / In-Memory Cache")]
    Queue["📦 Celery + Redis Worker"]
    AI["🤖 AI Motorları — scikit-learn + NumPy"]
    Mock["🎭 Mock Data Engine (Demo)"]
    
    Client <-->|"HTTPS / WebSocket"| Web
    API <-->|"JWT Bearer / HTTPS"| Web
    Web <--> App
    App <--> DB
    App <--> Cache
    App <--> Queue
    App <--> AI
    App -.->|"Simülasyon"| Mock
```

<br>

### Teknoloji Yığını (Full Stack)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        🎨 FRONTEND KATMANI                              │
│  HTML5 + Jinja2 · CSS3 (Cinematic Industrial Dark Theme)                │
│  Bootstrap 5.3 · Chart.js · Socket.IO Client · SVG · Leaflet.js        │
│  Plus Jakarta Sans + Inter (Google Fonts) · Glassmorphism Effects       │
├────────────────────────────────────────────────────────────────────────┤
│                        ⚙️ BACKEND KATMANI                                │
│  Python 3.12+ · Flask 3.1.1 (Application Factory + 27 Blueprint)        │
│  SQLAlchemy 2.0 · Flask-Login · Flask-Bcrypt · Flask-JWT-Extended        │
│  Flask-SocketIO + Eventlet · Flask-Limiter · Flask-Caching               │
│  Flask-Migrate + Alembic · Flask-WTF + CSRFProtect · Flask-CORS          │
├────────────────────────────────────────────────────────────────────────┤
│                        💾 VERİTABANI KATMANI                             │
│  SQLite WAL Mode (Geliştirme) · PostgreSQL (Üretim)                      │
│  35+ İlişkisel Tablo · Alembic Migrasyon · Foreign Key Bütünlüğü         │
│  Connection Pooling (PostgreSQL) · 256MB mmap + 64MB cache (SQLite)      │
├────────────────────────────────────────────────────────────────────────┤
│                        🤖 YAPAY ZEKA KATMANI                             │
│  NumPy 2.2 · scikit-learn 1.6 · 4 Ayrı Tahminleme Motoru                │
│  Kestirimci Bakım · OEE Tahmin · Stok Tahmin · Anomali Tespiti          │
│  Operatör-İş Eşleştirme (Beceri Matrisi)                                │
├────────────────────────────────────────────────────────────────────────┤
│                        📦 ASENKRON & ENTEGRASYON                         │
│  Celery 5.4 · Redis 5.2 · E-posta/SMS Bildirim · Rapor Oluşturma        │
│  OCR (Tesseract + Pillow) · ReportLab (PDF) · openpyxl (Excel)           │
└────────────────────────────────────────────────────────────────────────┘
```

<br>

### Proje Yapısı

```
FabrikaOS/
├── app/
│   ├── __init__.py          # Application Factory (create_app)
│   ├── extensions.py        # Flask uzantıları (db, jwt, socketio, ...)
│   ├── models/              # SQLAlchemy modelleri (23 dosya, 35+ tablo)
│   │   ├── kullanici.py     # Kullanıcı & RBAC
│   │   ├── makine.py        # Makine, üretim verisi, arıza kaydı
│   │   ├── is_emri.py       # İş emri & yorum
│   │   ├── stok.py          # Malzeme, stok hareketi, tedarikçi
│   │   ├── isg.py           # İş kazası, risk değerlendirme, eğitim
│   │   ├── crm.py           # Firma, ortak, yetkili kişi
│   │   └── ...              # +17 model dosyası
│   ├── routes/              # Blueprint route'ları (29 dosya)
│   │   ├── dashboard.py     # Ana dashboard
│   │   ├── api_v1.py        # REST API (JWT)
│   │   ├── fabrika_harita.py# Dijital ikiz
│   │   ├── dis_panel.py     # Dış kullanıcı portalı
│   │   └── ...              # +25 route dosyası
│   ├── services/            # İş mantığı katmanı
│   │   ├── ai/              # 4 AI motoru
│   │   ├── oee_hesaplama.py # OEE hesaplama servisi
│   │   ├── mock_engine.py   # Demo simülasyon motoru
│   │   ├── otomasyon_motoru.py
│   │   └── ...              # +18 servis dosyası
│   ├── templates/           # Jinja2 şablonları (28 modül dizini)
│   ├── static/              # CSS, JS, görsel varlıklar
│   ├── forms/               # WTForms form tanımları
│   ├── tasks/               # Celery asenkron görevleri
│   └── utils/               # Yardımcı araçlar (decorators, logger)
├── seeds/                   # Demo veri doldurma modülleri (22 dosya)
├── migrations/              # Alembic veritabanı migrasyonları
├── tests/                   # pytest test suite (21 dosya)
├── deployment/              # Üretim deployment araçları
├── docs/                    # Ekran görüntüleri & dokümantasyon
├── config.py                # Ortam yapılandırması (dev/prod/test)
├── run.py                   # Uygulama başlatıcı
├── seed_data.py             # Demo veri yükleyici
├── celery_worker.py         # Celery worker tanımı
└── requirements.txt         # Python bağımlılıkları
```

<br>

### Mimari Kararlar

| Karar | Gerekçe |
|:------|:--------|
| **Application Factory Pattern** | Test, geliştirme ve üretim ortamları aynı kodla çalışır; döngüsel import sorunları önlenir |
| **27 Blueprint Modülü** | Her modül bağımsız geliştirilebilir, test edilebilir ve devre dışı bırakılabilir |
| **3 Katmanlı Mimari** | Route (thin controller) → Service (iş mantığı) → Model (veri) ayrımı |
| **SQLite WAL → PostgreSQL** | Geliştirmede sıfır bağımlılık, üretimde kurumsal performans |
| **Socket.IO + Eventlet** | WebSocket ile gerçek zamanlı veri akışı, polling'e gerek yok |
| **JWT + Session hibrit auth** | Web arayüzü için session-based auth, REST API için JWT — her kullanıma uygun |
| **Batch Mode Migrations** | `render_as_batch=True` ile SQLite ALTER TABLE desteği |
| **Granüler RBAC** | Rol tabanlı erişimin ötesinde, modül bazlı okuma/yazma/silme izin sistemi |

<br>

---

<br>

## 🛡️ Güvenlik — OWASP Standartlarında

FabrikaOS, endüstriyel verilerin hassasiyetini bilerek **OWASP Top 10** standartlarına uygun güvenlik katmanlarıyla donatılmıştır.

<br>

```mermaid
graph LR
    A["🌐 HTTP İsteği"] --> B{"🚦 Rate Limiter"}
    B -->|"Limit Aşıldı"| C["429 Too Many Requests"]
    B -->|"OK"| D{"🔑 CSRF / JWT Token"}
    D -->|"Geçersiz"| E["403 Forbidden"]
    D -->|"OK"| F{"🔐 Kimlik Doğrulama"}
    F -->|"Oturum Yok"| G["→ Login"]
    F -->|"OK"| H{"🛡️ RBAC Yetki"}
    H -->|"Yetkisiz"| I["403 Erişim Engeli"]
    H -->|"OK"| J["✅ İşlem Gerçekleştir"]
```

<br>

| Güvenlik Katmanı | Teknoloji | Detay |
|:-----------------|:----------|:------|
| **Kimlik Doğrulama** | Flask-Login + Bcrypt + JWT | Session tabanlı web auth + JWT API auth |
| **Parola Güvenliği** | Bcrypt hash + salt | Tüm parolalar tek yönlü hash'lenir |
| **RBAC** | 8+ Rol | `yonetici`, `operator`, `teknisyen`, `ik_uzmani`, `isg_uzmani`, `muhasebe`, `crm_yetkilisi`, `satin_alma` |
| **Granüler İzinler** | Modül bazlı JSON map | Her kullanıcıya modül × izin türü (`okuma`/`yazma`/`silme`) atanır |
| **CSRF Koruması** | Flask-WTF CSRFProtect | Tüm formlarda otomatik token doğrulama (API hariç) |
| **Rate Limiting** | Flask-Limiter | Login: 10/dk, API: 60/dk, genel: 200/saat (prod: 100/saat) |
| **Security Headers** | Custom Middleware | `X-Frame-Options`, `HSTS`, `CSP`, `X-XSS-Protection`, `X-Content-Type-Options` |
| **Session Güvenliği** | HTTPOnly + SameSite=Lax | Cookie hijacking koruması, üretimde Secure flag |
| **Veri Bütünlüğü** | SQLite WAL + Foreign Key | Write-Ahead Logging, referans bütünlüğü |
| **Secret Yönetimi** | Ortam değişkenleri | Üretimde varsayılan SECRET_KEY kullanılırsa uygulama başlamayı reddeder |

<br>

---

<br>

## 🎨 Tasarım Sistemi — "Cinematic Industrial"

FabrikaOS'un arayüzü rastgele bir karanlık tema değil, **bilinçli bir tasarım sistemi** üzerine kurulmuştur.

> Metal sanayisinin güçlü yapısını yansıtan, Bloomberg Terminal'in veri yoğunluğuyla lüks otomotiv arayüzlerinin estetiğini birleştiren **"Institutional Glassmorphism"** tasarım dili.

| Tasarım Öğesi | Yaklaşım |
|:--------------|:---------|
| **Renk Paleti** | Ultra-koyu yüzeyler (`#0f172a`, `#131317`) — kontrol odaları için göz yorgunluğunu minimize eder |
| **Işık Kaynakları** | Neon mavi (`#38bdf8`) ve zümrüt yeşil (`#56e5a9`) — kritik veriyi ışık kaynağı gibi vurgular |
| **Glassmorphism** | `backdrop-blur: 20px` + `%6 opacity` kenarlıklar — derinlik ve katman hissi |
| **Tipografi** | Plus Jakarta Sans (başlıklar, ExtraBold) + Inter (veri tabloları, Regular) |
| **Atmosfer** | 16×16px dot-grid arka plan, radyal glow efektleri, luminous outline |
| **Animasyonlar** | Skeleton loading, toast notifications, donanım hızlandırmalı CSS transforms |
| **Bileşenler** | Neon-fill butonlar, focus glow input alanları, backdrop-blur kartlar, gradient progress bar |

<br>

---

<br>

## 🚀 Hızlı Başlangıç — 5 Dakikada Çalışır

FabrikaOS'u kendi makinenizde çalıştırmak için tek gereken **Python 3.12+** ve **5 dakika**.

<br>

### 1️⃣ Depoyu Klonlayın

```bash
git clone https://github.com/Scryne/FabrikaOS.git
cd FabrikaOS
```

### 2️⃣ Sanal Ortam & Bağımlılıklar

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3️⃣ Çevre Değişkenleri

Kök dizinde `.env` dosyası oluşturun:

```ini
FLASK_APP=run.py
FDYS_CONFIG=development
SECRET_KEY=super-gizli-kurumsal-anahtar-degistir-bunu
```

> **Not:** Üretim ortamında `FDYS_SECRET_KEY` ve `JWT_SECRET_KEY` ortam değişkenlerini **mutlaka** değiştirin. Değiştirmezseniz uygulama başlamayı reddedecektir.

### 4️⃣ Veritabanı & Demo Verileri

```bash
# Veritabanı tablolarını oluştur
flask db upgrade

# Demo verileri yükle (AnadoluTech Metal Sanayi senaryosu)
python seed_data.py
```

> ⚠️ `seed_data.py` mevcut veritabanını **tamamen siler** ve sıfırdan oluşturur.

### 5️⃣ Uygulamayı Başlatın 🚀

```bash
python run.py
```

Tarayıcınızda **`http://localhost:5000`** adresini açın — FabrikaOS sizi karşılıyor!

Uygulama başlatıldığında **Mock Data Engine** otomatik olarak devreye girer ve gerçekçi fabrika verileri simüle eder (makine durumları, OEE değişimleri, anlık üretim verileri).

<br>

### 6️⃣ (Opsiyonel) Asenkron Görevler

Celery + Redis ile arka plan görevlerini (e-posta, SMS, rapor oluşturma) etkinleştirmek için:

```bash
# Redis sunucusu başlatın (ayrı terminal)
redis-server

# Celery worker başlatın (ayrı terminal)
celery -A celery_worker.celery worker --loglevel=info

# Windows'ta çalıştırıyorsanız:
celery -A celery_worker.celery worker --loglevel=info --pool=solo
```

> **Not:** Redis/Celery opsiyoneldir — uygulama bunlar olmadan da çalışır, sadece asenkron görevler devre dışı kalır.

<br>

---

<br>

## 🔑 Demo Hesapları

Sisteme farklı roller ile giriş yaparak her rolün kendine özel dashboard deneyimini keşfedin. Demo verileri `python seed_data.py` komutuyla yüklenir.

<br>

### 🏢 İç Kullanıcılar — Fabrika Çalışanları

| # | Ad Soyad | Kullanıcı Adı | Şifre | Rol | Departman |
|:-:|:---------|:-------------|:------|:----|:----------|
| 1 | Deniz Yazar | `admin` | `admin123` | 👑 Yönetici | Yönetim |
| 2 | Ahmet Yılmaz | `ahmet.yilmaz` | `demo123` | 🔧 Operatör | Üretim |
| 3 | Fatma Demir | `fatma.demir` | `demo123` | 🔧 Operatör | Üretim |
| 4 | Mehmet Kaya | `mehmet.kaya` | `demo123` | 🛠️ Teknisyen | Bakım |
| 5 | Ayşe Özkan | `ayse.ozkan` | `demo123` | 🛠️ Teknisyen | Bakım |
| 6 | Selin Aktaş | `selin.aktas` | `demo123` | 🛡️ İSG Uzmanı | İSG |
| 7 | Zeynep Arslan | `zeynep.arslan` | `demo123` | 👔 İK Uzmanı | İnsan Kaynakları |
| 8 | Elif Yıldız | `elif.yildiz` | `demo123` | 💰 Muhasebe | Muhasebe |
| 9 | Deniz Korkmaz | `deniz.korkmaz` | `demo123` | 📞 CRM Yetkilisi | CRM |
| 10 | Mustafa Şahin | `mustafa.sahin` | `demo123` | 📦 Satın Alma | Satın Alma |

<br>

### 🌐 Dış Kullanıcılar — Müşteri, Tedarikçi & Taşeron Portalı

Bu hesaplarla dış kullanıcı portalına (`/dis-panel/`) giriş yapılır:

| # | Ad Soyad | Kullanıcı Adı | Şifre | Firma | Tip |
|:-:|:---------|:-------------|:------|:------|:----|
| 1 | Merve Aydın | `merve.aydin` | `musteri123` | Ford Otosan | 🏭 Müşteri |
| 2 | Seda Yılmaz | `seda.yilmaz` | `musteri123` | Renault | 🏭 Müşteri |
| 3 | Ercan Koçak | `ercan.kocak` | `tedarikci123` | Borusan Holding | 📦 Tedarikçi |
| 4 | Hakan Demir | `hakan.demir` | `tedarikci123` | Kardemir | 📦 Tedarikçi |
| 5 | Ali Vefa | `ali.vefa` | `taseron123` | ABC Makina | 🔨 Taşeron |

<br>

### 🔐 Rol Bazlı Erişim Matrisi

Her rol farklı modüllere farklı düzeylerde erişim sağlar:

| Modül | Yönetici | Operatör | Teknisyen | İSG | İK | Muhasebe | CRM | Satın Alma |
|:------|:--------:|:--------:|:---------:|:---:|:--:|:--------:|:---:|:----------:|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Makine & Üretim | ✅ | ✍️ | ✍️ | 👁️ | — | — | — | — |
| Stok & Malzeme | ✅ | ✍️ | ✍️ | — | — | 👁️ | — | ✍️ |
| İş Emri & Bakım | ✅ | 👁️ | ✍️ | — | — | — | — | — |
| Kalite | ✅ | ✍️ | — | 👁️ | — | — | — | — |
| İSG | ✅ | 👁️ | 👁️ | ✅ | 👁️ | — | — | — |
| Personel & İK | ✅ | 👁️ | — | 👁️ | ✅ | — | — | — |
| CRM & Sözleşme | ✅ | — | — | — | — | ✍️ | ✅ | 👁️ |
| Satın Alma | ✅ | — | — | — | — | 👁️ | — | ✅ |
| Enerji | ✅ | — | ✍️ | — | — | 👁️ | — | — |
| DYS & Duyuru | ✅ | 👁️ | 👁️ | ✍️ | ✍️ | 👁️ | 👁️ | 👁️ |
| AI & Analitik | ✅ | — | — | — | — | — | — | — |
| Admin Panel | ✅ | — | — | — | — | — | — | — |

> ✅ = Tam yetki &nbsp;|&nbsp; ✍️ = Okuma + Yazma &nbsp;|&nbsp; 👁️ = Sadece okuma &nbsp;|&nbsp; — = Erişim yok

<br>

---

<br>

## 🔌 REST API

FabrikaOS, üçüncü parti sistemlerle (ERP, SCADA, mobil uygulama, IoT gateway) entegrasyon için **JWT tabanlı REST API** sunar.

### Hızlı Başlangıç

```bash
# 1. JWT token alın
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"kullanici_adi": "admin", "sifre": "admin123"}'

# 2. Korumalı endpoint'e erişin
curl http://localhost:5000/api/v1/makineler \
  -H "Authorization: Bearer <access_token>"
```

### API Endpoint Özeti

| Modül | Endpoint | Metotlar | Yetki |
|:------|:---------|:---------|:------|
| **Auth** | `/api/v1/auth/login`, `/refresh`, `/me` | POST, GET | Genel |
| **Ortaklar** | `/api/v1/ortaklar`, `/ortaklar/{id}` | GET, POST, PUT, DELETE | CRM |
| **Firmalar** | `/api/v1/firmalar`, `/firmalar/{id}` | GET, POST, PUT, DELETE | CRM |
| **Sözleşmeler** | `/api/v1/sozlesmeler`, `/sozlesmeler/{id}` | GET | Sözleşme |
| **Talepler** | `/api/v1/talepler`, `/talepler/{id}` | GET, POST | Talep |
| **Personel** | `/api/v1/personel` | GET | Personel |
| **Makineler** | `/api/v1/makineler` | GET | Makine |
| **Malzemeler** | `/api/v1/malzemeler` | GET | Stok |
| **İş Emirleri** | `/api/v1/is-emirleri` | GET | Makine |
| **Duyurular** | `/api/v1/duyurular` | GET | Duyuru |
| **İstatistik** | `/api/v1/istatistik/ozet` | GET | JWT yeterli |
| **Keşif** | `/api/v1/`, `/api/v1/endpoints` | GET | Genel |

### API Özellikleri

- 🔐 **JWT Authentication** — Access token (1 saat) + Refresh token (30 gün)
- 📄 **Sayfalama** — `?sayfa=1&adet=20&siralama=id&yon=desc`
- 🔍 **Arama & Filtreleme** — `?arama=CNC&durum=aktif`
- 🚦 **Rate Limiting** — Login: 10/dk, API: 60/dk
- 📋 **Tutarlı JSON Formatı** — `{success, message, data, meta}`

> 📖 Detaylı API dokümantasyonu: [`API_DOKUMANTASYONU.md`](API_DOKUMANTASYONU.md)

<br>

---

<br>

## 🎭 Demo Senaryosu

Demo ortamı, gerçekçi bir metal sanayi tesisini simüle eder:

> **Şirket:** AnadoluTech Metal Sanayi A.Ş.
> **Konum:** Kocaeli Organize Sanayi Bölgesi
> **Sektör:** Otomotiv Yan Sanayi — CNC İşleme & Metal Şekillendirme

### Demo'da Neler Var?

| Veri Kategorisi | Miktar | Detay |
|:----------------|:------:|:------|
| 👥 Sistem kullanıcısı | 10 | 8 farklı iç rol + dış kullanıcılar |
| 👔 Çalışan kadrosu | 20 | Zengin İK profilleri, beceri matrisi |
| 🏭 Makine | 8 | CNC Torna, CNC Freze, Abkant, Pres, Kaynak, Taşlama, Lazer, Montaj |
| 📊 Üretim verisi | 180 gün | Vardiya bazlı, makine bazlı gerçekçi veriler |
| 🔧 Arıza kaydı | 8+ | Farklı makine ve arıza tipleri |
| 📦 Malzeme | 12+ | Kesici takım, ham malzeme, yedek parça |
| 🛡️ İSG kaydı | 25+ | Kaza, ramak kala, risk değerlendirme |
| 🤖 AI tahmini | 14+ | Kestirimci bakım ve OEE tahminleri |
| 📈 KPI hedefi | 132+ | Makine ve departman bazlı hedefler |
| 📋 İş emri | 10+ | Farklı öncelik ve durumlarda |
| 🏢 CRM firması | 5+ | Müşteri, tedarikçi, taşeron |
| 📜 Sözleşme | 5+ | Kira, sigorta, hizmet, bakım |
| 📢 Duyuru | 5+ | Farklı kategorilerde |
| 📄 DYS dokümanı | 10+ | Prosedür, talimat, form |

Tüm veriler birbirleriyle tutarlı ilişkiler içerir ve gerçek bir metal sanayi tesisini yansıtır.

<br>

---

<br>

## 🧪 Test

FabrikaOS, kapsamlı bir test altyapısına sahiptir. Testler `pytest` ile çalışır ve in-memory SQLite veritabanı kullanır.

```bash
# Tüm testleri çalıştır
pytest

# Belirli bir test dosyası
pytest tests/test_api.py

# Belirli bir test fonksiyonu (verbose)
pytest tests/test_api.py::test_name -v

# Hızlı smoke test
pytest tests/smoke_test.py

# Test kapsamı raporu
pytest --tb=short -q
```

### Test Kapsamı

| Test Kategorisi | Dosya | Kapsam |
|:----------------|:------|:-------|
| Temel uygulama | `test_basic.py` | Uygulama fabrikası, config, uzantılar |
| REST API | `test_api.py` | JWT auth, endpoint yanıtları |
| İş mantığı | `test_logic.py` | OEE hesaplama, servis katmanı |
| Kullanıcı senaryoları | `test_kullanici_senaryolari.py` | Login, rol bazlı erişim |
| AI servisleri | `test_ai_servisleri.py` | Tahmin motorları, anomali tespiti |
| Analitik | `test_analitik_servisleri.py` | KPI hesaplama, korelasyon |
| CRM | `test_crm.py` | Firma/ortak CRUD |
| İK | `test_ik.py` | Personel, izin, zimmet |
| İSG | `test_isg_genisletme.py` | Kaza, risk, eğitim |
| Otomasyon | `test_otomasyon.py` | Otomasyon motoru |
| Performans | `test_performance.py` | Yanıt süreleri, yük testi |
| Entegrasyon | `test_integration.py` | Modüller arası etkileşim |
| Rol yetkileri | `test_roles.py` | RBAC doğrulama |
| Smoke | `smoke_test.py` | Hızlı sağlık kontrolü |

<br>

---

<br>

## 🚢 Deployment (Üretim Ortamı)

### Ortam Değişkenleri

```bash
# Zorunlu — uygulama bu olmadan başlamayı reddeder
export FDYS_SECRET_KEY="<güçlü-rastgele-anahtar>"
export JWT_SECRET_KEY="<güçlü-rastgele-jwt-anahtarı>"
export FDYS_CONFIG=production

# Veritabanı (PostgreSQL önerilir)
export DATABASE_URL="postgresql://user:pass@host:5432/fabrikaos"

# Opsiyonel
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export SOCKETIO_CORS_ALLOWED_ORIGINS="https://fabrika.sirketim.com"
export SMS_GATEWAY_URL="https://api.sms-provider.com/send"
export SMS_API_KEY="<sms-api-anahtarı>"
```

### Gunicorn ile Başlatma

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 "app:create_app('production')"
```

### Windows Batch Script

Proje içerisinde hazır `deployment/run_server.bat` scripti mevcuttur.

### Üretim Güvenlik Kontrol Listesi

- [ ] `FDYS_SECRET_KEY` ve `JWT_SECRET_KEY` değiştirildi
- [ ] HTTPS/TLS sertifikası yapılandırıldı (`SESSION_COOKIE_SECURE=True` üretimde aktif)
- [ ] PostgreSQL veritabanı kullanılıyor (`DATABASE_URL` ayarlandı)
- [ ] Redis sunucusu çalışıyor (Celery görevleri için)
- [ ] Reverse proxy (nginx/Caddy) yapılandırıldı
- [ ] `SOCKETIO_CORS_ALLOWED_ORIGINS` belirli domain'lerle sınırlandırıldı
- [ ] Rate limiting üretim değerlerine ayarlandı (100/saat)
- [ ] Yedekleme sistemi kuruldu (`deployment/backup.py` kullanılabilir)
- [ ] Log rotasyonu yapılandırıldı

<br>

---

<br>

## 🤝 Katkıda Bulunma

FabrikaOS'a katkıda bulunmak isterseniz aşağıdaki kurallara dikkat edin:

### Geliştirme Kuralları

1. **Türkçe Kod Tabanı** — Modül isimleri, model sınıfları, route fonksiyonları, veritabanı sütunları ve yorumlar **Türkçe** yazılır (örn: `Kullanici`, `Makine`, `IsEmri`)
2. **Mimari Uyum** — Blueprint MVC pattern, Application Factory, 3 katmanlı mimari (route → service → model)
3. **Decorator Sırası** — Route'larda: `@bp.route` → `@login_required` → `@modul_erisim_gerekli` → `@log_action`
4. **Testler** — Tüm testlerin geçtiğini doğrulayın: `pytest tests/ -v`
5. **Responsive Tasarım** — Tüm arayüz bileşenleri mobil uyumlu olmalıdır
6. **CSP Uyumu** — Yeni bir CDN/dış kaynak ekliyorsanız `_register_security_headers` fonksiyonundaki CSP string'ini güncelleyin
7. **Migrasyon** — Model değişikliklerinde `flask db migrate -m "açıklama"` ile migrasyon oluşturun, doğrudan şema düzenlemeyin
8. **Seed Bağımlılık Sırası** — Yeni seed modülü eklerken `seed_data.py::run_seeds()` içindeki bağımlılık zincirini takip edin

### Katkı Süreci

```bash
# 1. Fork & Clone
git clone https://github.com/<kullanici>/FabrikaOS.git

# 2. Feature branch oluşturun
git checkout -b ozellik/yeni-modul-adi

# 3. Değişikliklerinizi yapın ve testleri çalıştırın
pytest tests/ -v

# 4. Commit & Push
git commit -m "feat: yeni modül açıklaması"
git push origin ozellik/yeni-modul-adi

# 5. Pull Request açın
```

<br>

---

<br>

## 📜 Lisans

Bu proje **[MIT Lisansı](LICENSE)** altında lisanslanmıştır.

Ticari ve bireysel kullanıma açıktır. Kaynak kodunu değiştirebilir, dağıtabilir ve kendi projelerinizde kullanabilirsiniz.

```
MIT License — Copyright (c) 2025 FDYS — Fabrika Dijital Yönetim Sistemi
```

<br>

---

<br>

<div align="center">

  <img src="https://raw.githubusercontent.com/Scryne/FabrikaOS/main/app/static/images/logo.png" alt="FabrikaOS" width="60" onerror="this.src='https://via.placeholder.com/60/0f172a/38bdf8?text=F'"/>

  <br><br>

  **FabrikaOS — Üretim verileri artık bir yük değil, stratejik bir güç.**

  <br>

  *Geliştirici: [Scryne](https://github.com/Scryne)*

  <br>

  [![GitHub](https://img.shields.io/badge/GitHub-Scryne/FabrikaOS-181717?style=for-the-badge&logo=github)](https://github.com/Scryne/FabrikaOS)

  <br>

  © 2025-2026 FabrikaOS — Fabrika Dijital Yönetim Sistemi (FDYS)

  <br>

  ⭐ **Beğendiyseniz bir yıldız bırakmayı unutmayın!**

</div>
