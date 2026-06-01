"""
FabrikaOS — CRM Demo Verisi (v2)
İş ortakları, firmalar, yetkililer ve iletişim kayıtları
"""
import random
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.crm import Firma, FirmaYetkilisi, CrmIletisimGecmisi
from app.models.kullanici import Kullanici


def seed():
    print('[22/22] CRM (Firmalar & İletişim)...')

    crm_yetkilisi = Kullanici.query.filter_by(rol='crm_yetkilisi').first() or Kullanici.query.first()
    bugun = datetime.now(timezone.utc)

    # ── FİRMALAR ──
    firmalar_data = [
        {'ad': 'Ford Otosan A.Ş.', 'sektor': 'otomotiv', 'vergi_no': '1234567890'},
        {'ad': 'Oyak Renault', 'sektor': 'otomotiv', 'vergi_no': '0987654321'},
        {'ad': 'Borusan Mannesmann', 'sektor': 'metal', 'vergi_no': '1122334455'},
        {'ad': 'Kardemir', 'sektor': 'metal', 'vergi_no': '5544332211'},
        {'ad': 'ABC Makina Sanayi', 'sektor': 'uretim', 'vergi_no': '9988776655'},
    ]

    firmalar = []
    for i, f in enumerate(firmalar_data):
        firma = Firma(
            firma_no=f"FRM-{bugun.year}-{i+1000}",
            unvan=f['ad'],
            vergi_dairesi='Büyük Mükellefler',
            vergi_no=f['vergi_no'],
            sektor=f['sektor'],
            adres='OSB Mahallesi, Sanayi Cad.',
            telefon='0850 111 22 33',
            eposta=f"info@{f['ad'].lower().split()[0].replace('ş','s')}.com.tr",
            durum=Firma.DURUM_AKTIF,
            olusturma_tarihi=bugun - timedelta(days=random.randint(100, 1000))
        )
        db.session.add(firma)
        firmalar.append(firma)
    
    db.session.flush()

    # ── FİRMA YETKİLİLERİ ──
    yetkililer_data = [
        {'firma_idx': 0, 'ad': 'Merve Aydın', 'gorev': 'Satın Alma Müdürü', 'tel': '0532 111 22 33'},
        {'firma_idx': 0, 'ad': 'Caner Türk', 'gorev': 'Kalite Uzmanı', 'tel': '0533 222 33 44'},
        {'firma_idx': 1, 'ad': 'Seda Yılmaz', 'gorev': 'Tedarik Zinciri Sorumlusu', 'tel': '0534 333 44 55'},
        {'firma_idx': 2, 'ad': 'Ercan Koçak', 'gorev': 'Satış Müdürü', 'tel': '0535 444 55 66'},
    ]

    yetkililer = []
    for y in yetkililer_data:
        yetkili = FirmaYetkilisi(
            firma_id=firmalar[y['firma_idx']].id,
            ad_soyad=y['ad'],
            gorev=y['gorev'],
            telefon=y['tel'],
            eposta=f"{y['ad'].split()[0].lower()}@{firmalar[y['firma_idx']].unvan.lower().split()[0]}.com.tr"
        )
        db.session.add(yetkili)
        yetkililer.append(yetkili)

    db.session.flush()

    # ── İLETİŞİM KAYITLARI ──
    iletisim_konulari = [
        ('Aylık Değerlendirme Toplantısı', 'Genel performans ve kalite metrikleri konuşuldu. Hedefler tutturuldu.', CrmIletisimGecmisi.ILETISIM_YUZ_YUZE),
        ('Fiyat Güncelleme Görüşmesi', 'Hammadde artışları sebebiyle %5 zam talebi iletildi. Haftaya dönüş yapılacak.', CrmIletisimGecmisi.ILETISIM_TELEFON),
        ('Yeni Proje Teklifi', 'Yeni model aracın sac parçaları için teknik resimler paylaşıldı.', CrmIletisimGecmisi.ILETISIM_EPOSTA),
        ('Kalite Şikayeti', 'Son partideki ölçüsel sapmalar hakkında uyarı aldık.', CrmIletisimGecmisi.ILETISIM_TELEFON),
    ]

    for _ in range(12):
        firma = random.choice(firmalar)
        konu, detay, tur = random.choice(iletisim_konulari)
        
        kayit = CrmIletisimGecmisi(
            ilgili_tip=CrmIletisimGecmisi.TIP_FIRMA,
            ilgili_id=firma.id,
            yapan_id=crm_yetkilisi.id,
            iletisim_turu=tur,
            konu=konu,
            detay=detay,
            sonuc='Olumlu',
            tarih=bugun - timedelta(days=random.randint(1, 60))
        )
        db.session.add(kayit)

    db.session.flush()
    print('  OK\n')
