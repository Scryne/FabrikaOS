# 🔌 FabrikaOS — REST API v1 Dokümantasyonu

**Sürüm:** v1.0.0  
**Base URL:** `http://localhost:5000/api/v1`  
**Kimlik Doğrulama:** JWT (JSON Web Token)  
**Format:** JSON

---

## İçindekiler

1. [Genel Bakış](#-genel-bakış)
2. [Kimlik Doğrulama](#-kimlik-doğrulama-auth)
3. [Yanıt Formatı](#-yanıt-formatı)
4. [Sayfalama & Filtreleme](#-sayfalama--filtreleme)
5. [Ortaklar (CRM)](#-ortaklar-crm)
6. [Firmalar (CRM)](#-firmalar-crm)
7. [Sözleşmeler](#-sözleşmeler)
8. [Talepler](#-talepler)
9. [Personel](#-personel)
10. [Makineler](#-makineler)
11. [Malzemeler (Stok)](#-malzemeler-stok)
12. [İş Emirleri](#-iş-emirleri)
13. [Duyurular](#-duyurular)
14. [İstatistik](#-istatistik)
15. [Hata Kodları](#-hata-kodları)
16. [Rate Limiting](#-rate-limiting)

---

## 📋 Genel Bakış

FabrikaOS REST API v1, üçüncü parti sistemlerle entegrasyon için JWT tabanlı bir API katmanı sunar. Tüm endpoint'ler tutarlı bir JSON yanıt formatı kullanır.

### Temel Özellikler
- **JWT kimlik doğrulama** (access + refresh token)
- **RBAC yetkilendirme** (modül bazlı erişim kontrolü)
- **Sayfalama, filtreleme, sıralama** desteği
- **Rate limiting** ile API güvenliği
- **CSRF muafiyeti** (token tabanlı koruma kullanılır)

### Endpoint Keşfi

API bilgi endpoint'i herhangi bir kimlik doğrulama gerektirmez:

```
GET /api/v1/
GET /api/v1/endpoints
```

---

## 🔐 Kimlik Doğrulama (Auth)

API, JWT Bearer Token yöntemi ile kimlik doğrulama yapar. Önce token alın, sonra her istekte `Authorization` başlığında gönderin.

### Token Alma (Login)

```
POST /api/v1/auth/login
```

**Rate Limit:** 10 istek/dakika

**İstek Gövdesi:**
```json
{
  "kullanici_adi": "admin",
  "sifre": "admin123"
}
```

**Başarılı Yanıt (200):**
```json
{
  "success": true,
  "message": "Giriş başarılı",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "kullanici": {
      "id": 1,
      "ad_soyad": "Sistem Yöneticisi",
      "kullanici_adi": "admin",
      "rol": "yonetici",
      "rol_adi": "Yönetici"
    }
  }
}
```

**Hata Yanıtları:**
- `400` — Kullanıcı adı veya şifre eksik
- `401` — Geçersiz kimlik bilgileri
- `403` — Hesap deaktif veya kilitli

### Token Yenileme (Refresh)

```
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

**Başarılı Yanıt (200):**
```json
{
  "success": true,
  "message": "Token yenilendi",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer"
  }
}
```

### Mevcut Kullanıcı Bilgisi

```
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Başarılı Yanıt (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "ad_soyad": "Sistem Yöneticisi",
    "kullanici_adi": "admin",
    "rol": "yonetici",
    "rol_adi": "Yönetici",
    "departman": "Yönetim",
    "modul_erisim": {...},
    "aktif": true,
    "son_giris": "2026-06-01T10:00:00"
  }
}
```

### Token Kullanımı

Tüm korumalı endpoint'lerde `Authorization` başlığını ekleyin:

```
Authorization: Bearer <access_token>
```

**Token Geçerlilik Süreleri:**
- **Access Token:** 1 saat
- **Refresh Token:** 30 gün

---

## 📦 Yanıt Formatı

Tüm API yanıtları aşağıdaki tutarlı formatta döner:

```json
{
  "success": true,
  "message": "İşlem açıklaması",
  "data": { ... },
  "meta": {
    "sayfa": 1,
    "adet": 20,
    "toplam": 100,
    "toplam_sayfa": 5,
    "siralama": "id",
    "yon": "desc"
  }
}
```

| Alan | Tip | Açıklama |
|------|-----|----------|
| `success` | boolean | İşlem başarılı mı |
| `message` | string | İşlem açıklaması |
| `data` | object/array | Yanıt verisi |
| `meta` | object | Sayfalama bilgisi (listelerde) |

---

## 📄 Sayfalama & Filtreleme

Tüm liste endpoint'leri ortak query parametrelerini destekler:

### Sayfalama Parametreleri

| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|------------|----------|
| `sayfa` | int | 1 | Sayfa numarası |
| `adet` | int | 20 | Sayfa başına kayıt (max: 100) |
| `siralama` | string | `id` | Sıralama alanı |
| `yon` | string | `desc` | Sıralama yönü (`asc` / `desc`) |
| `arama` | string | — | Genel arama metni |

### Örnek Kullanım

```bash
# 2. sayfa, sayfa başına 10 kayıt, ada göre artan sıralama
GET /api/v1/ortaklar?sayfa=2&adet=10&siralama=ad_soyad&yon=asc

# "Ahmet" araması
GET /api/v1/ortaklar?arama=Ahmet

# Aktif ortaklar, A bloktaki
GET /api/v1/ortaklar?durum=aktif&blok=A
```

---

## 👥 Ortaklar (CRM)

**Yetki:** CRM modül erişimi gerekli

### Ortak Listele

```
GET /api/v1/ortaklar
Authorization: Bearer <token>
```

**Filtreler:**

| Parametre | Açıklama | Değerler |
|-----------|----------|----------|
| `durum` | Durum filtresi | `aktif`, `pasif`, `cikis_yapti` |
| `blok` | Blok filtresi | Blok adı |
| `ortak_tipi` | Tip filtresi | `malik`, `kiraci`, `yetkili`, `vekil` |

**Arama alanları:** ad_soyad, ortak_no, tc_kimlik, telefon, blok

### Ortak Detay

```
GET /api/v1/ortaklar/{id}
Authorization: Bearer <token>
```

### Ortak Oluştur

```
POST /api/v1/ortaklar
Authorization: Bearer <token>
Content-Type: application/json
```

**İstek Gövdesi:**
```json
{
  "ortak_no": "ORT-001",
  "ad_soyad": "Ahmet Yılmaz",
  "tc_kimlik": "12345678901",
  "telefon": "05551234567",
  "eposta": "ahmet@ornek.com",
  "blok": "A",
  "daire_no": "101",
  "ortak_tipi": "malik",
  "hisse_orani": 50.0,
  "m2": 120.5,
  "milliyet": "T.C.",
  "adres": "Kocaeli, Gebze",
  "notlar": "Ek bilgi"
}
```

**Zorunlu alanlar:** `ortak_no`, `ad_soyad`

**Başarılı Yanıt (201):**
```json
{
  "success": true,
  "message": "Ortak oluşturuldu",
  "data": {
    "id": 1,
    "ortak_no": "ORT-001",
    "ad_soyad": "Ahmet Yılmaz",
    ...
  }
}
```

### Ortak Güncelle

```
PUT /api/v1/ortaklar/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

**İstek Gövdesi:** Güncellenecek alanları gönderin (tümü opsiyonel):
```json
{
  "telefon": "05559876543",
  "durum": "pasif"
}
```

### Ortak Sil (Soft Delete)

```
DELETE /api/v1/ortaklar/{id}
Authorization: Bearer <token>
```

---

## 🏢 Firmalar (CRM)

**Yetki:** CRM modül erişimi gerekli

### Firma Listele

```
GET /api/v1/firmalar
Authorization: Bearer <token>
```

**Filtreler:**

| Parametre | Açıklama | Değerler |
|-----------|----------|----------|
| `durum` | Durum filtresi | `aktif`, `pasif`, `cikis_yapti` |
| `blok` | Blok filtresi | Blok adı |
| `sektor` | Sektör filtresi | Sektör kodu |

### Firma Detay

```
GET /api/v1/firmalar/{id}
Authorization: Bearer <token>
```

Detaylı yanıt firma yetkili kişilerini de içerir.

### Firma Oluştur

```
POST /api/v1/firmalar
Authorization: Bearer <token>
Content-Type: application/json
```

**İstek Gövdesi:**
```json
{
  "firma_no": "FRM-001",
  "unvan": "AnadoluTech Metal Sanayi A.Ş.",
  "vergi_no": "1234567890",
  "vergi_dairesi": "Gebze",
  "sektor": "imalat",
  "faaliyet_alani": "CNC İşleme",
  "yetkili_kisi": "Mehmet Kaya",
  "telefon": "02621234567",
  "eposta": "info@anadolutech.com",
  "adres": "Kocaeli OSB",
  "calisan_sayisi": 150
}
```

**Zorunlu alanlar:** `firma_no`, `unvan`

### Firma Güncelle

```
PUT /api/v1/firmalar/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

### Firma Sil (Soft Delete)

```
DELETE /api/v1/firmalar/{id}
Authorization: Bearer <token>
```

---

## 📋 Sözleşmeler

**Yetki:** Sözleşme modül erişimi gerekli  
**Not:** Sözleşmeler salt okunurdur (CRUD sadece web arayüzünden).

### Sözleşme Listele

```
GET /api/v1/sozlesmeler
Authorization: Bearer <token>
```

**Filtreler:**

| Parametre | Açıklama | Değerler |
|-----------|----------|----------|
| `durum` | Durum filtresi | `aktif`, `pasif`, `suresi_dolmus`, `iptal` |
| `tur` | Tür filtresi | `kira`, `sigorta`, `hizmet`, `bakim`, `diger` |
| `taraf_tip` | Taraf tipi | `ortak`, `firma` |

### Sözleşme Detay

```
GET /api/v1/sozlesmeler/{id}
Authorization: Bearer <token>
```

**Yanıt örneği:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "sozlesme_no": "SZL-2026-001",
    "tur": "kira",
    "tur_adi": "Kira Sözleşmesi",
    "baslik": "A Blok 101 Kira Kontratı",
    "baslangic_tarihi": "2026-01-01",
    "bitis_tarihi": "2027-01-01",
    "tutar": 15000.00,
    "para_birimi": "TRY",
    "durum": "aktif",
    "durum_adi": "Aktif",
    "kalan_gun": 214,
    "odeme_periyodu": "aylik",
    "otomatik_yenileme": true,
    "hatirlatma_gun": 30
  }
}
```

---

## 🎫 Talepler

**Yetki:** Talep modül erişimi gerekli

### Talep Listele

```
GET /api/v1/talepler
Authorization: Bearer <token>
```

**Filtreler:**

| Parametre | Açıklama | Değerler |
|-----------|----------|----------|
| `durum` | Durum filtresi | `acik`, `yonlendirildi`, `devam`, `cozuldu`, `kapali`, `iptal` |
| `kategori` | Kategori filtresi | `ariza`, `oneri`, `sikayet`, `bilgi`, `diger` |
| `oncelik` | Öncelik filtresi | `dusuk`, `normal`, `yuksek`, `acil` |

**Arama alanları:** baslik, talep_no, talep_eden_adi

### Talep Detay

```
GET /api/v1/talepler/{id}
Authorization: Bearer <token>
```

Detaylı yanıt talep geçmişini de içerir (max 50 kayıt).

### Talep Oluştur

```
POST /api/v1/talepler
Authorization: Bearer <token>
Content-Type: application/json
```

**İstek Gövdesi:**
```json
{
  "baslik": "CNC-01 Tezgahında Titreşim Sorunu",
  "aciklama": "Son 2 gündür anormal titreşim gözlemlenmektedir.",
  "kategori": "ariza",
  "oncelik": "yuksek",
  "konum_bilgi": "Üretim Holü, CNC Bölgesi",
  "sms_bildirim": true,
  "eposta_bildirim": true
}
```

**Zorunlu alanlar:** `baslik`

**Başarılı Yanıt (201):**
```json
{
  "success": true,
  "message": "Talep oluşturuldu",
  "data": {
    "id": 1,
    "talep_no": "TLP-2026-00001",
    "baslik": "CNC-01 Tezgahında Titreşim Sorunu",
    "kategori": "ariza",
    "kategori_adi": "Arıza Bildirimi",
    "oncelik": "yuksek",
    "oncelik_adi": "Yüksek",
    "durum": "acik",
    "durum_adi": "Açık",
    "talep_eden_adi": "Sistem Yöneticisi",
    "olusturma_tarihi": "2026-06-01T10:00:00"
  }
}
```

---

## 👔 Personel

**Yetki:** Personel modül erişimi gerekli  
**Not:** Salt okunur endpoint.

### Personel Listele

```
GET /api/v1/personel
Authorization: Bearer <token>
```

**Arama alanları:** ad_soyad, sicil_no, departman

**Yanıt:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "sicil_no": "ATE-001",
      "ad_soyad": "Ahmet Yılmaz",
      "departman": "Üretim",
      "pozisyon": "Kıdemli CNC Operatörü",
      "ise_baslama": "2020-03-15",
      "durum": "aktif"
    }
  ],
  "meta": { ... }
}
```

---

## 🏭 Makineler

**Yetki:** Makine modül erişimi gerekli  
**Not:** Salt okunur endpoint.

### Makine Listele

```
GET /api/v1/makineler
Authorization: Bearer <token>
```

**Filtreler:**

| Parametre | Açıklama | Değerler |
|-----------|----------|----------|
| `durum` | Durum filtresi | `aktif`, `pasif`, `arizali`, `bakim` |

**Arama alanları:** ad, kod, lokasyon

**Yanıt:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "ad": "CNC Torna T-200",
      "kod": "CNC-01",
      "durum": "aktif",
      "lokasyon": "Üretim Holü A",
      "marka": "Doosan",
      "model": "Puma 2600"
    }
  ],
  "meta": { ... }
}
```

---

## 📦 Malzemeler (Stok)

**Yetki:** Stok modül erişimi gerekli  
**Not:** Salt okunur endpoint.

### Malzeme Listele

```
GET /api/v1/malzemeler
Authorization: Bearer <token>
```

**Arama alanları:** ad, kod

**Yanıt:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "ad": "HSS Matkap Ucu Ø10",
      "kod": "MLZ-001",
      "miktar": 45.0,
      "birim": "adet",
      "kategori": "kesici_takim",
      "min_stok": 10.0
    }
  ],
  "meta": { ... }
}
```

---

## 📋 İş Emirleri

**Yetki:** Makine modül erişimi gerekli  
**Not:** Salt okunur endpoint.

### İş Emri Listele

```
GET /api/v1/is-emirleri
Authorization: Bearer <token>
```

**Filtreler:**

| Parametre | Açıklama | Değerler |
|-----------|----------|----------|
| `durum` | Durum filtresi | `olusturuldu`, `atandi`, `devam`, `tamamlandi`, `iptal` |

**Arama alanları:** baslik, is_emri_no

**Yanıt:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "is_emri_no": "IE-2026-001",
      "baslik": "CNC-01 Periyodik Bakım",
      "durum": "devam",
      "oncelik": "yuksek",
      "olusturma_tarihi": "2026-05-15T08:00:00"
    }
  ],
  "meta": { ... }
}
```

---

## 📢 Duyurular

**Yetki:** Duyuru modül erişimi gerekli  
**Not:** Salt okunur endpoint.

### Duyuru Listele

```
GET /api/v1/duyurular
Authorization: Bearer <token>
```

**Arama alanları:** baslik

**Yanıt:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "baslik": "Yıllık İSG Eğitimi Duyurusu",
      "icerik": "Tüm çalışanların katılması zorunlu...",
      "tur": "bilgilendirme",
      "oncelik": "yuksek",
      "yayin_tarihi": "2026-05-20T09:00:00"
    }
  ],
  "meta": { ... }
}
```

---

## 📊 İstatistik

**Yetki:** JWT token yeterli (modül yetkisi gerekmez)

### Sistem Özeti

```
GET /api/v1/istatistik/ozet
Authorization: Bearer <token>
```

**Rate Limit:** 30 istek/dakika

**Yanıt:**
```json
{
  "success": true,
  "message": "Sistem özeti",
  "data": {
    "ortaklar": {
      "toplam": 25,
      "aktif": 20
    },
    "firmalar": {
      "toplam": 15,
      "aktif": 12
    },
    "sozlesmeler": {
      "toplam": 18,
      "aktif": 10
    },
    "talepler": {
      "toplam": 45,
      "acik": 8
    },
    "personel": {
      "toplam": 15
    },
    "makineler": {
      "toplam": 6,
      "calisir": 5,
      "arizali": 1
    }
  }
}
```

---

## ❌ Hata Kodları

| HTTP Kodu | Açıklama | Örnek Durum |
|-----------|----------|-------------|
| `400` | Bad Request | Eksik veya geçersiz parametre |
| `401` | Unauthorized | Token eksik, geçersiz veya süresi dolmuş |
| `403` | Forbidden | Yetkisiz erişim (rol/modül yetkisi yok) |
| `404` | Not Found | Kayıt bulunamadı |
| `409` | Conflict | Benzersiz alan çakışması (ör. tekrar eden ortak_no) |
| `429` | Too Many Requests | Rate limit aşıldı |
| `500` | Internal Server Error | Sunucu hatası |

**Hata yanıt formatı:**
```json
{
  "success": false,
  "message": "Hata açıklaması",
  "data": null
}
```

---

## ⏱️ Rate Limiting

| Endpoint Grubu | Limit |
|----------------|-------|
| `/auth/login` | 10 istek/dakika |
| Liste endpoint'leri | 60 istek/dakika |
| İstatistik | 30 istek/dakika |
| Genel (development) | 1000 istek/saat |
| Genel (production) | 100 istek/saat |

Rate limit aşıldığında `429 Too Many Requests` yanıtı döner.

---

## 💻 Kod Örnekleri

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"

# 1. Token al
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "kullanici_adi": "admin",
    "sifre": "admin123"
})
token = login_response.json()["data"]["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. Ortakları listele
ortaklar = requests.get(f"{BASE_URL}/ortaklar", headers=headers)
print(ortaklar.json())

# 3. Yeni ortak oluştur
yeni_ortak = requests.post(f"{BASE_URL}/ortaklar", headers=headers, json={
    "ortak_no": "ORT-100",
    "ad_soyad": "Yeni Ortak",
    "telefon": "05551234567",
    "ortak_tipi": "kiraci"
})
print(yeni_ortak.json())

# 4. Talep oluştur
yeni_talep = requests.post(f"{BASE_URL}/talepler", headers=headers, json={
    "baslik": "Asansör arıza bildirimi",
    "kategori": "ariza",
    "oncelik": "yuksek",
    "aciklama": "B Blok asansörü çalışmıyor."
})
print(yeni_talep.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:5000/api/v1';

// 1. Token al
const loginRes = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    kullanici_adi: 'admin',
    sifre: 'admin123'
  })
});
const { data: { access_token } } = await loginRes.json();

// 2. Ortakları listele
const ortaklarRes = await fetch(`${BASE_URL}/ortaklar?adet=10&siralama=ad_soyad&yon=asc`, {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const ortaklar = await ortaklarRes.json();
console.log(ortaklar);
```

### cURL

```bash
# Token al
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"kullanici_adi":"admin","sifre":"admin123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# Ortakları listele
curl http://localhost:5000/api/v1/ortaklar \
  -H "Authorization: Bearer $TOKEN"

# Sistem özeti
curl http://localhost:5000/api/v1/istatistik/ozet \
  -H "Authorization: Bearer $TOKEN"

# Yeni talep oluştur
curl -X POST http://localhost:5000/api/v1/talepler \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baslik":"Test talebi","kategori":"bilgi","oncelik":"normal"}'
```

---

<div align="center">
  <strong>© 2026 FabrikaOS REST API v1</strong><br>
  <em>Detaylı bilgi için: <a href="README.md">README.md</a></em>
</div>
