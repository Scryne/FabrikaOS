"""
FabrikaOS — Talepler Demo Verisi (v2)
Çalışanların IT, İK, Bakım, Satın Alma talepleri
"""
import random
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.talep import Talep, TalepGecmisi
from app.models.kullanici import Kullanici


def seed():
    print('[24/22] İç Talepler...') # Sembolik numara

    kullanicilar = Kullanici.query.filter_by(aktif=True).all()
    bugun = datetime.now(timezone.utc)

    talepler = [
        {'kategori': 'teknik_hizmet', 'oncelik': 'yuksek', 'baslik': 'Muhasebe yazıcısı arızalı', 'aciklama': 'Muhasebe departmanındaki HP yazıcı kağıt sıkıştırıyor. Acil fatura kesmemiz gerekiyor.', 'durum': 'acik'},
        {'kategori': 'idari', 'oncelik': 'normal', 'baslik': 'Yeni personel e-posta hesabı', 'aciklama': 'Satın alma departmanına yeni katılan arkadaşımız için e-posta açılması.', 'durum': 'tamamlandi'},
        {'kategori': 'mekanik', 'oncelik': 'dusuk', 'baslik': 'Soyunma odası dolap kilidi', 'aciklama': 'Erkek soyunma odası 15 numaralı dolabın kilidi bozuk.', 'durum': 'devam'},
        {'kategori': 'mekanik', 'oncelik': 'normal', 'baslik': 'Ofis kliması su damlatıyor', 'aciklama': 'Satış ofisindeki klima çalışırken su damlatıyor.', 'durum': 'yonlendirildi'},
        {'kategori': 'idari', 'oncelik': 'normal', 'baslik': 'Maaş bordrosu talebi', 'aciklama': 'Vize başvurusu için son 3 aylık imzalı maaş bordrosu talep ediyorum.', 'durum': 'tamamlandi'},
        {'kategori': 'idari', 'oncelik': 'dusuk', 'baslik': 'Yemekhane menüsü önerisi', 'aciklama': 'Menüde daha fazla zeytinyağlı seçeneği olmasını rica ediyoruz.', 'durum': 'reddedildi'},
        {'kategori': 'idari', 'oncelik': 'normal', 'baslik': 'Yeni kırtasiye malzemesi', 'aciklama': 'Üretim ofisi için 5 paket A4 kağıt ve tükenmez kalem gerekiyor.', 'durum': 'acik'},
        {'kategori': 'idari', 'oncelik': 'yuksek', 'baslik': 'İş güvenliği ayakkabısı değişimi', 'aciklama': 'Ayakkabımın tabanı yarıldı, yeni 42 numara çelik burunlu ayakkabı talebi.', 'durum': 'devam'},
        {'kategori': 'otopark', 'oncelik': 'dusuk', 'baslik': 'Otopark çizgileri', 'aciklama': 'Ziyaretçi otoparkındaki çizgiler silinmiş, yeniden boyanması iyi olur.', 'durum': 'yonlendirildi'},
    ]

    for i, t in enumerate(talepler):
        olusturan = random.choice(kullanicilar)
        gun_once = random.randint(1, 20)
        tarih = bugun - timedelta(days=gun_once, hours=random.randint(1, 10))
        
        # Eğer durum tamamlandı veya reddedildi ise, bitiş tarihi ekle
        bitis_tarihi = None
        if t['durum'] in ['tamamlandi', 'kapandi', 'reddedildi']:
            bitis_tarihi = tarih + timedelta(days=random.randint(1, 5))

        talep = Talep(
            talep_no=f"TLP-{bugun.year}-{i+100}",
            talep_eden_tip='dahili',
            talep_eden_id=olusturan.id,
            talep_eden_adi=olusturan.ad_soyad,
            kategori=t['kategori'],
            oncelik=t['oncelik'],
            baslik=t['baslik'],
            aciklama=t['aciklama'],
            durum=t['durum'],
            olusturma_tarihi=tarih,
            guncelleme_tarihi=bitis_tarihi or tarih,
            kapanma_tarihi=bitis_tarihi
        )
        db.session.add(talep)
        db.session.flush()

        # Talep Geçmişi
        gecmis = TalepGecmisi(
            talep_id=talep.id,
            yapan_id=olusturan.id,
            yapan_adi=olusturan.ad_soyad,
            islem_turu='olusturma',
            yeni_durum='acik',
            aciklama='Talep oluşturuldu.',
            tarih=tarih
        )
        db.session.add(gecmis)

        if t['durum'] != 'acik':
            islem_tarihi = tarih + timedelta(hours=random.randint(2, 48))
            islem_yapan = Kullanici.query.filter_by(kullanici_adi='admin').first() or olusturan
            
            gecmis2 = TalepGecmisi(
                talep_id=talep.id,
                yapan_id=islem_yapan.id,
                yapan_adi=islem_yapan.ad_soyad,
                islem_turu='durum_degisikligi',
                eski_durum='acik',
                yeni_durum=t['durum'],
                aciklama=f"Talebin durumu {t['durum']} olarak güncellendi.",
                tarih=islem_tarihi
            )
            db.session.add(gecmis2)

    db.session.flush()
    print('  OK\n')
