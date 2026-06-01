"""
FabrikaOS — Bildirimler ve Denetim İzi Demo Verisi (v2)
Tüm kullanıcılara okunmuş/okunmamış bildirimler ve sistem denetim logları
"""
import random
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.bildirim import Bildirim
from app.models.kullanici import Kullanici


def seed():
    print('[18/22] Bildirimler...')
    random.seed(999)

    kullanicilar = Kullanici.query.all()
    bugun = datetime.now(timezone.utc)

    # Rol bazlı bildirim şablonları
    sablonlar = {
        'yonetici': [
            ('bilgi', 'Haftalık Rapor', 'Haftalık üretim ve kalite raporu hazırlandı.', '/raporlar/haftalik'),
            ('kritik', 'Sistem Uyarısı', 'Veritabanı yedeklemesi 2 gündür alınamıyor.', '/ayarlar'),
            ('uyari', 'Bütçe Aşımı', 'Aylık enerji bütçesi %15 oranında aşıldı.', '/enerji'),
            ('bilgi', 'Yeni Çalışan', 'İK departmanına 2 yeni personel eklendi.', '/personel'),
            ('uyari', 'Onay Bekleyen Talepler', 'Satın alma modülünde 5 adet onay bekleyen talep var.', '/satin-alma/onaylar'),
        ],
        'operator': [
            ('bilgi', 'Vardiya Planı', 'Gelecek haftanın vardiya planı yayınlandı.', '/personel/vardiya'),
            ('uyari', 'Eğitim Hatırlatması', 'KKD Kullanımı eğitiminiz 3 gün sonra.', '/isg/egitimler'),
            ('bilgi', 'İzin Onayı', '24.05 tarihindeki mazeret izniniz onaylandı.', '/personel/izinler'),
            ('kritik', 'Kalite Uyarısı', 'Son partide hata oranı eşik değeri aştı.', '/kalite'),
            ('bilgi', 'Duyuru', 'Yemekhane menüsü güncellendi.', '/duyuru'),
        ],
        'teknisyen': [
            ('kritik', 'Yeni Arıza Ataması', 'PRS-001 makinesinde hidrolik sızıntı.', '/is-emri/arizalar'),
            ('uyari', 'Yaklaşan Bakım', 'CNC-001 makinesinin periyodik bakımı yarına planlandı.', '/is-emri/bakimlar'),
            ('bilgi', 'Malzeme Teslimi', 'Talep ettiğiniz SKF rulmanlar depoya ulaştı.', '/stok/hareketler'),
            ('bilgi', 'İş Emri Kapandı', 'İE-2026-0012 numaralı iş emriniz kalite tarafından onaylandı.', '/is-emri/gecmis'),
            ('uyari', 'Eksik Form', 'Dünkü bakım formunda imza eksiği bulunuyor.', '/dys'),
        ],
        'isg_uzmani': [
            ('kritik', 'Ramak Kala Bildirimi', 'Kaygan zemin kaynaklı yeni ramak kala raporlandı.', '/isg/kazalar'),
            ('uyari', 'Süresi Dolan Eğitim', '5 çalışanın yüksekte çalışma eğitim süresi doldu.', '/isg/egitimler'),
            ('bilgi', 'Risk Değerlendirmesi', 'Aylık saha turu raporu eklendi.', '/isg/riskler'),
            ('bilgi', 'Doküman Onayı', 'Acil durum eylem planı yöneticiden onay aldı.', '/dys'),
        ],
        'ik_uzmani': [
            ('bilgi', 'Yeni İzin Talebi', 'Ahmet Yılmaz yıllık izin talebinde bulundu.', '/personel/izinler'),
            ('uyari', 'Savunma Bekleniyor', 'Tutanak No: 42 için savunma süresi dolmak üzere.', '/ik/tutanaklar'),
            ('bilgi', 'Mesai Onayı', 'Dünkü 14 saatlik toplam fazla mesai onaylandı.', '/ik/mesailer'),
        ],
        'satin_alma': [
            ('uyari', 'Kritik Stok', 'CNC Freze Ucu stok seviyesi minimumun altına düştü.', '/stok/kritik'),
            ('bilgi', 'Yeni Talep', 'Bakım departmanı yedek parça talebi açtı.', '/satin-alma/talepler'),
            ('bilgi', 'Teklif Geldi', 'Misumi Türkiye\'den fiyat teklifi alındı.', '/satin-alma/teklifler'),
        ],
    }

    genel_sablonlar = [
        ('bilgi', 'Sistem Güncellemesi', 'FabrikaOS v2.1 yayına alındı. Yeni özellikleri inceleyin.', '/duyuru'),
        ('bilgi', 'Profil Güncelleme', 'Lütfen iletişim bilgilerinizi güncelleyin.', '/profil'),
        ('uyari', 'Şifre Değişikliği', 'Şifrenizi değiştirmenizin üzerinden 90 gün geçti.', '/profil/sifre'),
    ]

    for k in kullanicilar:
        # Rol bazlı bildirimler
        rol_sablon = sablonlar.get(k.rol, genel_sablonlar)
        sablonlar_havuzu = rol_sablon + genel_sablonlar

        # Kullanıcı başına 5-8 bildirim
        bildirim_sayisi = random.randint(5, 8)
        secilenler = random.choices(sablonlar_havuzu, k=bildirim_sayisi)

        for i, (seviye, baslik, mesaj, url) in enumerate(secilenler):
            # İlk 2-3 bildirim okunmamış olsun, diğerleri okunmuş
            okundu = i >= random.randint(2, 3)
            gun_once = random.randint(0, 15)
            olusturma = bugun - timedelta(days=gun_once, hours=random.randint(1, 23))

            b = Bildirim(
                kullanici_id=k.id,
                baslik=baslik,
                mesaj=mesaj,
                seviye=seviye,
                modul='sistem',
                url=url,
                okundu_mu=okundu,
                okunma_tarihi=olusturma + timedelta(hours=1) if okundu else None,
                olusturma_tarihi=olusturma,
            )
            db.session.add(b)

    db.session.flush()
    print(f'  + {len(kullanicilar)} kullanıcıya bildirimler eklendi\n')
