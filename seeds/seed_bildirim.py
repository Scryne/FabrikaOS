"""
FabrikaOS — Bildirim ve Denetim İzi Demo Verisi
Senaryo: AnadoluTech Metal Sanayi

- 15 bildirim (kritik, uyarı, bilgi, güvenlik — tüm modüllerden)
- Kullanıcı bazlı dağıtım
- 12 denetim izi (audit trail)
"""
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.bildirim import Bildirim
from app.models.kullanici import Kullanici, DenetimIzi
from app.models.makine import Makine


def seed():
    print('[12/12] Bildirimler ve denetim izleri...')

    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    tum_kullanicilar = Kullanici.query.all()
    admin_id = admin.id if admin else 1

    prs = Makine.query.filter_by(kod='PRS-001').first()
    prs_id = prs.id if prs else 1
    
    abk = Makine.query.filter_by(kod='ABK-001').first()
    abk_id = abk.id if abk else 2
    
    cnc2 = Makine.query.filter_by(kod='CNC-002').first()
    cnc2_id = cnc2.id if cnc2 else 3

    # ══════════════════════════════════════════════════════════════
    # ADMIN BİLDİRİMLERİ (15 adet — okunmamış + okunmuş karışık)
    # ══════════════════════════════════════════════════════════════
    bildirimler = [
        # KRİTİK — Okunmamış
        {
            'baslik': 'Kritik Arıza: Hidrolik Pres (PRS-001)',
            'mesaj': 'Hidrolik silindir rod keçesinden yağ sızıntısı başladı. '
                     'Basınç 180 bar → 145 bar. Üretim durdu. Acil müdahale gerekiyor.',
            'seviye': 'kritik', 'modul': 'makine', 'url': f'/makine/detay/{prs_id}',
            'saat': 6,
        },
        {
            'baslik': 'Kritik Arıza: Abkant Pres (ABK-001)',
            'mesaj': 'Kalıp kilitleme ünitesinde toggle mekanizması aşınması tespit edildi. '
                     'Kilitleme kuvveti yetersiz, ürünlerde çapak oluşuyor.',
            'seviye': 'kritik', 'modul': 'makine', 'url': f'/makine/detay/{abk_id}',
            'saat': 12,
        },
        {
            'baslik': 'Ramak Kala: Kaynak Bölgesi Yangın Riski',
            'mesaj': 'D Hattı kaynak bölgesinde zemine düşen hidrolik yağ lekesi '
                     'kaynak kıvılcımı ile tutuştu. Müdahale edildi, hasar yok. '
                     'Olay araştırması devam ediyor.',
            'seviye': 'kritik', 'modul': 'isg', 'url': '/isg/',
            'saat': 18,
        },

        # UYARI — Okunmamış
        {
            'baslik': 'Stok Uyarısı: Kesim Dirençli Eldiven',
            'mesaj': 'Nitril Kesim Dirençli Eldiven (MLZ-006) mevcut stok: 12 adet. '
                     'Minimum stok eşiği: 40 adet. Acil sipariş verilmesi önerilir.',
            'seviye': 'uyari', 'modul': 'stok', 'url': '/stok/',
            'saat': 24,
        },
        {
            'baslik': 'Bakım Zamanı: Pres Makinesi (PRS-001)',
            'mesaj': 'PRS-001 periyodik bakım tarihi 86 gün önce yapılmıştır. '
                     'Bir sonraki bakım tarihi geçmiştir. Bakım planı oluşturun.',
            'seviye': 'uyari', 'modul': 'makine', 'url': f'/makine/detay/{prs_id}',
            'saat': 30,
        },
        {
            'baslik': 'OEE Düşüşü: CNC Freze (CNC-002)',
            'mesaj': 'CNC-002 son 7 günlük ortalama OEE değeri %71.8 ile '
                     'hedefin (%82) önemli ölçüde altında. İnceleme önerilir.',
            'seviye': 'uyari', 'modul': 'makine', 'url': f'/makine/detay/{cnc2_id}',
            'saat': 36,
        },
        {
            'baslik': 'CAPA Hedef Tarihi Yaklaşıyor',
            'mesaj': 'CAPA-2026-001 (Krank Mili Çap Tolerans) düzeltici faaliyetin '
                     'hedef tarihi 7 gün içinde doluyor. İlerleme durumunu kontrol edin.',
            'seviye': 'uyari', 'modul': 'kalite', 'url': '/kalite/',
            'saat': 42,
        },
        {
            'baslik': 'Eğitim Süresi Doldu: İSG Uzmanı',
            'mesaj': 'Selin Aktaş (P010) — İSG Uzmanı C Sınıfı Yenileme Eğitimi süresi '
                     '15.01.2026 tarihinde dolmuştur. Yasal zorunluluk gereği yenilenmeli.',
            'seviye': 'uyari', 'modul': 'isg', 'url': '/isg/egitimler',
            'saat': 48,
        },
        {
            'baslik': 'Enerji Tüketimi Hedef Aşımı',
            'mesaj': 'Nisan ayı üretim elektrik tüketimi: 51.200 kWh (hedef: 47.000 kWh). '
                     'Hedefin %8.9 üzerinde. Fazla mesai üretimleri etkili.',
            'seviye': 'uyari', 'modul': 'enerji', 'url': '/enerji/',
            'saat': 54,
        },

        # BİLGİ — Bazıları okunmuş
        {
            'baslik': 'İzin Talebi Bekliyor',
            'mesaj': 'Ahmet Yılmaz (P001) 7 günlük yıllık izin talebinde bulundu '
                     f'(15 gün sonra). Onayınızı bekliyor.',
            'seviye': 'bilgi', 'modul': 'personel', 'url': '/personel/izinler',
            'saat': 60, 'okundu': True,
        },
        {
            'baslik': 'Yeni Çalışan Kaydı',
            'mesaj': 'Canan Erdem (P015) Staj Mühendis olarak Planlama departmanında '
                     'göreve başlamıştır.',
            'seviye': 'bilgi', 'modul': 'personel', 'url': '/personel/',
            'saat': 72, 'okundu': True,
        },
        {
            'baslik': 'Bakım Tamamlandı: CNC Torna (CNC-001)',
            'mesaj': 'CNC-001 periyodik bakımı başarıyla tamamlandı. '
                     'Bir sonraki bakım: 90 gün sonra.',
            'seviye': 'bilgi', 'modul': 'makine', 'url': '/makine/',
            'saat': 84, 'okundu': True,
        },
        {
            'baslik': 'Kalite Raporu Oluşturuldu',
            'mesaj': 'Nisan 2026 kalite kontrol raporu hazırlandı. '
                     'Toplam hata: 84 adet, Fire oranı: %2.6',
            'seviye': 'bilgi', 'modul': 'kalite', 'url': '/kalite/',
            'saat': 96, 'okundu': True,
        },
        {
            'baslik': 'Tedarikçi Teslimatı Alındı',
            'mesaj': 'Sandvik Coromant sipariş teslimatı alındı — 80 adet CNMG kesici uç. '
                     'Fatura: FTR-2026-0412. Giriş kalite kontrolü bekleniyor.',
            'seviye': 'bilgi', 'modul': 'stok', 'url': '/stok/',
            'saat': 108, 'okundu': True,
        },

        # GÜVENLİK
        {
            'baslik': 'Sistem Başlatıldı',
            'mesaj': 'FabrikaOS v2.0 üretim ortamında başarıyla başlatıldı. '
                     'Tüm modüller aktif. Son güncelleme: Mayıs 2026.',
            'seviye': 'bilgi', 'modul': None, 'url': None,
            'saat': 120, 'okundu': True,
        },
    ]

    for b in bildirimler:
        okundu = b.get('okundu', False)
        bildirim = Bildirim(
            kullanici_id=admin_id,
            baslik=b['baslik'],
            mesaj=b['mesaj'],
            seviye=b['seviye'],
            modul=b['modul'],
            url=b['url'],
            okundu_mu=okundu,
            olusturma_tarihi=datetime.now(timezone.utc) - timedelta(hours=b['saat']),
        )
        if okundu:
            bildirim.okunma_tarihi = datetime.now(timezone.utc) - timedelta(
                hours=b['saat'] - 1
            )
        db.session.add(bildirim)

    # Diğer kullanıcılara modül bazlı bildirimler
    for k in tum_kullanicilar:
        if k.id == admin_id:
            continue

        # Hoş geldiniz bildirimi
        b_hosgeldin = Bildirim(
            kullanici_id=k.id,
            baslik='FabrikaOS\'a Hoş Geldiniz!',
            mesaj=f'{k.ad_soyad}, AnadoluTech Metal Sanayi dijital yönetim sistemine '
                  f'hoş geldiniz. {k.rol.title()} rolüyle giriş yapabilirsiniz.',
            seviye='bilgi',
            okundu_mu=True,
            olusturma_tarihi=datetime.now(timezone.utc) - timedelta(days=7),
            okunma_tarihi=datetime.now(timezone.utc) - timedelta(days=6),
        )
        db.session.add(b_hosgeldin)

        # Teknisyenlere arıza bildirimi
        if k.rol == 'teknisyen':
            b_ariza = Bildirim(
                kullanici_id=k.id,
                baslik='Yeni Arıza Ataması',
                mesaj='Size yeni bir arıza kaydı atandı. Detaylar için arıza '
                      'listesini kontrol edin.',
                seviye='uyari',
                modul='makine',
                url='/makine/arizalar',
                okundu_mu=False,
                olusturma_tarihi=datetime.now(timezone.utc) - timedelta(hours=8),
            )
            db.session.add(b_ariza)

        # Operatörlere vardiya bildirimi
        if k.rol == 'operator':
            b_vardiya = Bildirim(
                kullanici_id=k.id,
                baslik='Haftalık Vardiya Planı Yayınlandı',
                mesaj='Bu haftanın vardiya planı güncellendi. '
                      'Personel modülünden kontrol edebilirsiniz.',
                seviye='bilgi',
                modul='personel',
                url='/personel/vardiya',
                okundu_mu=False,
                olusturma_tarihi=datetime.now(timezone.utc) - timedelta(hours=12),
            )
            db.session.add(b_vardiya)

    db.session.flush()
    print('  + Bildirimler oluşturuldu')

    # ══════════════════════════════════════════════════════════════
    # DENETİM İZLERİ (Audit Trail — 12 kayıt)
    # ══════════════════════════════════════════════════════════════
    izler = [
        {
            'islem': 'Oluştur', 'tablo': 'kullanici', 'kayit_id': 1,
            'detay': '{"kullanici_adi": "admin", "rol": "yonetici", '
                     '"islem": "Sistem yöneticisi hesabı oluşturuldu"}',
            'ip': '192.168.1.100', 'saat': 120,
        },
        {
            'islem': 'Oluştur', 'tablo': 'makine', 'kayit_id': 1,
            'detay': '{"kod": "CNC-001", "ad": "CNC Torna T-400", '
                     '"marka": "Doosan", "lokasyon": "A Hattı"}',
            'ip': '192.168.1.100', 'saat': 118,
        },
        {
            'islem': 'Oluştur', 'tablo': 'calisan', 'kayit_id': 1,
            'detay': '{"sicil_no": "P001", "ad_soyad": "Ahmet Yılmaz", '
                     '"departman": "Üretim", "pozisyon": "Kıdemli CNC Operatörü"}',
            'ip': '192.168.1.100', 'saat': 116,
        },
        {
            'islem': 'Güncelle', 'tablo': 'makine', 'kayit_id': 4,
            'detay': '{"alan": "durum", "eski": "aktif", "yeni": "arizali", '
                     '"neden": "Hidrolik silindir sızıntısı"}',
            'ip': '192.168.1.100', 'saat': 48,
        },
        {
            'islem': 'Oluştur', 'tablo': 'ariza_kaydi', 'kayit_id': 1,
            'detay': '{"makine": "PRS-001", "oncelik": "yuksek", '
                     '"ariza_turu": "mekanik", "bildiren": "ahmet.yilmaz"}',
            'ip': '192.168.1.105', 'saat': 47,
        },
        {
            'islem': 'Oluştur', 'tablo': 'stok_hareketi', 'kayit_id': 1,
            'detay': '{"malzeme": "MLZ-001", "tur": "giris", "miktar": 80, '
                     '"fatura": "FTR-2026-0412", "tedarikci": "Sandvik Coromant"}',
            'ip': '192.168.1.100', 'saat': 72,
        },
        {
            'islem': 'Güncelle', 'tablo': 'izin_talebi', 'kayit_id': 2,
            'detay': '{"durum": "bekliyor → onaylandi", '
                     '"calisan": "P002 Fatma Demir", "tur": "saglik"}',
            'ip': '192.168.1.100', 'saat': 60,
        },
        {
            'islem': 'Oluştur', 'tablo': 'is_kazasi', 'kayit_id': 1,
            'detay': '{"olay_no": "KZ-2026-001", "siddet": "orta", '
                     '"calisan": "P005 Ali Çelik", "yer": "C Hattı Pres"}',
            'ip': '192.168.1.100', 'saat': 96,
        },
        {
            'islem': 'Oluştur', 'tablo': 'hata_kaydi', 'kayit_id': 1,
            'detay': '{"urun": "Krank Mili Ø48", "hata": "Çap tolerans aşımı", '
                     '"parti": "LOT-2026-0401", "adet": 12}',
            'ip': '192.168.1.100', 'saat': 36,
        },
        {
            'islem': 'Oluştur', 'tablo': 'duzeltici_faaliyet', 'kayit_id': 1,
            'detay': '{"capa_no": "CAPA-2026-001", "durum": "devam", '
                     '"kategori": "makine", "hedef_tarih": "7 gün sonra"}',
            'ip': '192.168.1.100', 'saat': 30,
        },
        {
            'islem': 'Oluştur', 'tablo': 'enerji_tuketimi', 'kayit_id': 1,
            'detay': '{"donem": "Ocak 2026", "tur": "elektrik", '
                     '"miktar": "52400 kWh", "maliyet": "149.340 TL"}',
            'ip': '192.168.1.100', 'saat': 24,
        },
        {
            'islem': 'Güncelle', 'tablo': 'duzeltici_faaliyet', 'kayit_id': 3,
            'detay': '{"capa_no": "CAPA-2026-003", "durum": "devam → kapandi", '
                     '"dogrulama": "Son 5 günde 0 porozite"}',
            'ip': '192.168.1.100', 'saat': 12,
        },
    ]

    for iz in izler:
        di = DenetimIzi(
            kullanici_id=admin_id,
            islem=iz['islem'],
            tablo=iz['tablo'],
            kayit_id=iz['kayit_id'],
            detay=iz['detay'],
            ip_adresi=iz['ip'],
            tarih=datetime.now(timezone.utc) - timedelta(hours=iz['saat']),
        )
        db.session.add(di)

    db.session.flush()
    print('  + Denetim izleri oluşturuldu\n')
