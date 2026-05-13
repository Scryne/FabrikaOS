# 🛡️ FabrikaOS - OWASP Güvenlik Kontrol Listesi

Bu belge, **FabrikaOS (FDYS)** platformunun OWASP Top 10 web uygulama güvenlik risklerine karşı aldığı kurumsal standartlardaki önlemleri açıklamaktadır.

## 1. Kırık Erişim Kontrolü (Broken Access Control)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Her endpoint için katı Role-Based Access Control (RBAC) uygulanmaktadır. `@role_required('yonetici')` vb. dekoratörler aracılığıyla operatörlerin yetkisiz modüllere, teknisyenlerin admin paneline erişimi engellenmiştir.
- **Doğrulama**: `tests/test_roles.py` içerisindeki erişim testleri, kısıtlı profillerin yasaklı alanlara girmeye çalıştığında `403 Forbidden` yanıtı aldığını doğrular.

## 2. Kriptografik Hatalar (Cryptographic Failures)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Tüm şifreler, düz metin yerine güçlü bir çalışma faktörüne sahip `bcrypt` algoritması ile karma (hash) haline getirilerek veritabanında saklanmaktadır. (Bkz: `app/extensions.py` -> `Flask-Bcrypt`).
- **Doğrulama**: Veritabanındaki `kullanici` tablosu incelendiğinde şifrelerin hashli olduğu görülebilir.

## 3. Enjeksiyon (Injection)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Sistem genelinde doğrudan SQL sorguları yerine **SQLAlchemy ORM** kullanılmıştır. Bu sayede tüm veritabanı sorguları otomatik olarak parametrize edilir ve SQL Injection (SQLi) atakları engellenir.
- **İstisna**: SQLite kullanıldığından dolayı harici bir veritabanı portu (örn. 3306, 5432) dışarıya açık değildir.

## 4. Güvensiz Tasarım (Insecure Design)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Mimari düzeyde, yetki/rol mantığı ve veri modelleri iş kurallarına uygun katı kurallarla (constraint) tasarlanmıştır. Güvensiz varsayılanlar (insecure defaults) bulunmamaktadır; yeni oluşturulan bir kullanıcı varsayılan olarak `operator` (en düşük yetki) rolüyle başlatılır.

## 5. Güvenlik Yanlış Yapılandırması (Security Misconfiguration)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Development ve Production ortamları tamamen ayrılmıştır. Production konfigürasyonunda `DEBUG = False` yapılmış olup, sunucu hataları ekrana basılmaz, standart 500 sayfaları (`app/templates/errors/500.html`) gösterilir.
- **Flask Secret Key**: Gizli anahtar rastgele ve güvenli bir şekilde environment variable veya `.env` üzerinden yönetilecek şekilde ayarlanmıştır.

## 6. Savunmasız ve Güncel Olmayan Bileşenler (Vulnerable and Outdated Components)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Uygulama `requirements.txt` içerisindeki Flask, SQLAlchemy, Werkzeug, Flask-Login, openpyxl, reportlab gibi popüler ve güncel kütüphanelerin kararlı (stable) sürümleriyle inşa edilmiştir.

## 7. Kimlik Doğrulama Hataları (Identification and Authentication Failures)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Flask-Limiter ile Brute-Force saldırılarına karşı `Rate Limiting` uygulanmıştır. 5 başarısız deneme sonrası hesap/IP 30 dakika süreyle kilitlenmektedir. Flask-Login kullanılarak oturum yönetimi profesyonel bir şekilde ele alınmış, oturum hijyeni `HttpOnly` ve `SameSite=Lax` bayraklarıyla desteklenmiştir.

## 8. Yazılım ve Veri Bütünlüğü Hataları (Software and Data Integrity Failures)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: Tüm POST, PUT, DELETE form işlemlerinde **Flask-WTF** aracılığıyla CSRF (Cross-Site Request Forgery) token kullanımı zorunlu tutulmuştur. Güvensiz veri deseriyalizasyonundan (örn. Pickle) tamamen kaçınılmıştır.

## 9. Güvenlik Günlüğü ve İzleme Hataları (Security Logging and Monitoring Failures)
**Durum**: Alınan Önlemler Yeterli ✅
- **Önlem**: `@log_action` dekoratörü (Bkz: `app/utils/decorators.py`) aracılığıyla sistemde yapılan tüm kritik işlemler (Ekleme, Silme, Güncelleme vb.) kimin, ne zaman yaptığı bilgisiyle beraber `KullaniciIslemi` tablosuna kaydedilir ve Admin Denetim İzi menüsünden takip edilebilir.

## 10. Sunucu Tarafı İstek Sahteciliği (SSRF)
**Durum**: Uygulanamaz / Risk Yok ✅
- **Açıklama**: FabrikaOS harici bir API/URL'den doğrudan veri getiren (fetch) veya webhooks (geri çağırma) alan bir yapıda olmadığından dolayı SSRF riski taşımamaktadır.

---
> **Not:** Sistemin canlı (production) ortama alınması durumunda; Nginx / Apache gibi bir Reverse Proxy önünde HTTPS (SSL/TLS) sertifikası ile çalıştırılması, sistemin uçtan uca güvenliğini sağlayacaktır.
