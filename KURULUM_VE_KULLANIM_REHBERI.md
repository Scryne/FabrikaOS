# 🏭 FDYS — Kurulum ve Kullanım Rehberi

**Sürüm:** 1.0.0 (Faz 6 Profesyonel Sürüm)  
**Tarih:** Mayıs 2026

---

## 1. Sisteme Giriş ve Kurulum (IT Personeli İçin)

FDYS, fabrikanızın kapalı ağında (LAN) veya bulut sunucusunda çalışmak üzere tasarlanmıştır.

### Windows Üzerinde Üretim Ortamında Başlatma
1. Python 3.11+ sürümünün yüklü olduğundan emin olun.
2. Komut satırında proje ana klasörüne gidin.
3. Bağımlılıkları yükleyin: `pip install -r requirements.txt`
4. Veritabanını oluşturun: `python seed_data.py`
5. `deployment` klasörü içindeki `run_server.bat` dosyasını çalıştırın.
6. Sunucu **http://localhost:8080** adresinde başlayacaktır.

### Otomatik Yedekleme Ayarlama
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

### 2.4. Bildirim Motoru
Sağ üst köşedeki Çan ikonundan şu konularda uyarı alırsınız:
- Stok minimum eşiğin altına düştüğünde.
- Makine arıza yaptığında veya bakım tarihi geldiğinde.
- 5 kez yanlış şifre denendiğinde (Güvenlik Uyarısı).

---

> Lütfen teknik sorunlar için Bilgi İşlem departmanı ile iletişime geçin.
> Daha detaylı yapılandırma ayarları `config.py` üzerinden yapılmaktadır.
