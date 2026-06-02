import os
import sys
import random
from datetime import datetime, timedelta, timezone
from faker import Faker

# Proje kök dizinini Python yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.crm import Firma, FirmaYetkilisi, CrmIletisimGecmisi, Ortak
from app.models.sozlesme import Sozlesme, KiraKontrat, SigortaPolice
from app.models.kullanici import Kullanici
from app.models.talep import Talep
from app.models.dis_kullanici import DisKullanici

fake = Faker('tr_TR')

def get_random_date(days_back=365):
    return datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_back))

def run_seed():
    app = create_app()
    with app.app_context():
        print("Ekstra Demo Verisi (Pazarlama İçin) Oluşturuluyor...")
        bugun = datetime.now(timezone.utc)
        
        # Kullanıcı/Admin bulalım
        admin = Kullanici.query.filter_by(rol='yonetici').first() or Kullanici.query.first()
        admin_id = admin.id if admin else None

        # 1. ORTAKLAR (Sanayi Sitesi Üyeleri/Dükkan Sahipleri) - 50 adet
        print("1. Ortaklar oluşturuluyor...")
        bloklar = ['A', 'B', 'C', 'D', 'E', 'F']
        ortaklar = []
        for i in range(50):
            blok = random.choice(bloklar)
            daire_no = str(random.randint(1, 150))
            ortak = Ortak(
                ortak_no=f"ORT-{bugun.year}-{i+2000}",
                ad_soyad=fake.name(),
                tc_kimlik=str(fake.random_number(digits=11, fix_len=True)),
                telefon=fake.phone_number(),
                eposta=fake.email(),
                adres=fake.address(),
                blok=blok,
                daire_no=daire_no,
                ortak_tipi=random.choice([Ortak.TIP_MALIK, Ortak.TIP_KIRACI]),
                hisse_orani=random.choice([100.0, 50.0, 25.0]),
                m2=random.uniform(50.0, 1000.0),
                harita_enlem=40.85 + random.uniform(-0.01, 0.01), # Gebze tarafları yaklaşık
                harita_boylam=29.40 + random.uniform(-0.01, 0.01),
                olusturma_tarihi=get_random_date(700)
            )
            db.session.add(ortak)
            ortaklar.append(ortak)
        db.session.flush()

        # 2. FİRMALAR (İşletmeler) - 80 adet
        print("2. Firmalar oluşturuluyor...")
        firmalar = []
        sektorler = list(Firma.SEKTORLER.keys())
        for i in range(80):
            blok = random.choice(bloklar)
            daire_no = str(random.randint(1, 150))
            firma = Firma(
                firma_no=f"FRM-{bugun.year}-{i+2000}",
                unvan=f"{fake.company()} {random.choice(['Sanayi', 'Ticaret', 'Lojistik', 'Üretim'])} A.Ş.",
                vergi_no=str(fake.random_number(digits=10, fix_len=True)),
                vergi_dairesi=fake.city() + ' V.D.',
                sektor=random.choice(sektorler),
                telefon=fake.phone_number(),
                eposta=fake.company_email(),
                adres=fake.address(),
                blok=blok,
                daire_no=daire_no,
                m2=random.uniform(100.0, 5000.0),
                calisan_sayisi=random.randint(5, 500),
                harita_enlem=40.85 + random.uniform(-0.01, 0.01),
                harita_boylam=29.40 + random.uniform(-0.01, 0.01),
                olusturma_tarihi=get_random_date(1000)
            )
            db.session.add(firma)
            firmalar.append(firma)
        db.session.flush()

        # 3. İLETİŞİM GEÇMİŞİ (CRM Etkileşimleri) - 200 adet
        print("3. CRM İletişim Geçmişi oluşturuluyor...")
        konular = ['Fiyat Teklifi', 'Şikayet Çözümü', 'Yıllık Ziyaret', 'Fatura İtirazı', 'Yeni Ürün Tanıtımı', 'Sözleşme Yenileme', 'Genel Memnuniyet Araması']
        for _ in range(200):
            ilgili = random.choice([('ortak', random.choice(ortaklar).id), ('firma', random.choice(firmalar).id)])
            tarih = get_random_date(60)
            kayit = CrmIletisimGecmisi(
                ilgili_tip=ilgili[0],
                ilgili_id=ilgili[1],
                yapan_id=admin_id,
                iletisim_turu=random.choice(list(CrmIletisimGecmisi.ILETISIM_TURLERI.keys())),
                konu=random.choice(konular),
                detay=fake.text(max_nb_chars=150),
                sonuc=random.choice(['Olumlu', 'Olumsuz', 'Beklemede', 'Çözüldü', 'İleri Tarihe Ertelendi']),
                tarih=tarih,
                olusturma_tarihi=tarih
            )
            db.session.add(kayit)

        # 4. SÖZLEŞMELER - 100 adet (Genel, Kira, Sigorta)
        print("4. Sözleşmeler oluşturuluyor...")
        soz_turleri = ['bakim', 'hizmet', 'diger', 'kira', 'sigorta']
        durumlar = ['aktif', 'aktif', 'aktif', 'sona_erdi', 'iptal'] # Ağırlıklı aktif
        for i in range(100):
            tur = random.choice(soz_turleri)
            taraf = random.choice(firmalar)
            baslangic = get_random_date(500)
            sure_ay = random.choice([12, 24, 36])
            bitis = baslangic + timedelta(days=sure_ay * 30)
            durum = random.choice(durumlar)
            if bitis < bugun and durum == 'aktif':
                durum = 'sona_erdi' # Geçmişte bitmişse sona erdi

            soz = Sozlesme(
                sozlesme_no=f"SZL-EX-{i+1000}",
                baslik=f"{fake.company()} - {tur.capitalize()} Sözleşmesi",
                tur=tur,
                taraf_tip=Sozlesme.TARAF_FIRMA,
                taraf_id=taraf.id,
                baslangic_tarihi=baslangic,
                bitis_tarihi=bitis,
                tutar=random.uniform(5000.0, 500000.0),
                para_birimi=random.choice(['TL', 'USD', 'EUR']),
                durum=durum,
                olusturma_tarihi=baslangic
            )
            db.session.add(soz)
            db.session.flush()

            if tur == 'kira':
                ks = KiraKontrat(
                    sozlesme_id=soz.id,
                    blok=taraf.blok,
                    kira_tutari=soz.tutar,
                    artis_turu='tufe',
                    artis_orani=random.uniform(25.0, 80.0)
                )
                db.session.add(ks)
            elif tur == 'sigorta':
                pol = SigortaPolice(
                    sozlesme_id=soz.id,
                    police_no=f"POL-{fake.random_number(digits=8)}",
                    sigorta_sirketi=random.choice(['Allianz', 'Anadolu', 'Axa', 'Mapfre', 'Ak Sigorta']),
                    sigorta_turu=random.choice(['yangin', 'kasko', 'genel_sorumluluk', 'dask']),
                    police_baslangic=baslangic,
                    police_bitis=bitis,
                    teminat_tutari=soz.tutar * 100,
                    prim_tutari=soz.tutar,
                    durum='aktif' if bitis > bugun and durum != 'iptal' else 'suresi_doldu'
                )
                db.session.add(pol)

        # 5. TALEPLER - 50 Açık, 50 Kapalı (Harita ve Talep Takip için)
        print("5. Talepler oluşturuluyor...")
        kategoriler = [Talep.KAT_TEKNIK, Talep.KAT_IDARI, Talep.KAT_GUVENLIK, Talep.KAT_ELEKTRIK, Talep.KAT_MEKANIK]
        for i in range(100):
            taraf = random.choice(firmalar)
            tarih = get_random_date(100)
            durum = Talep.DURUM_ACIK if i < 50 else random.choice([Talep.DURUM_TAMAMLANDI, Talep.DURUM_KAPANDI, Talep.DURUM_REDDEDILDI])
            
            talep = Talep(
                talep_no=f"TLP-EX-{i+1000}",
                talep_eden_tip=Talep.TIP_FIRMA,
                talep_eden_id=taraf.id,
                talep_eden_adi=taraf.unvan,
                baslik=random.choice(['Elektrik Kesintisi', 'Su Sızıntısı', 'Güvenlik Zafiyeti', 'Yol Bozukluğu', 'İnternet Sorunu']),
                aciklama=fake.text(),
                kategori=random.choice(kategoriler),
                oncelik=random.choice([Talep.ONCELIK_DUSUK, Talep.ONCELIK_NORMAL, Talep.ONCELIK_YUKSEK, Talep.ONCELIK_ACIL]),
                durum=durum,
                olusturma_tarihi=tarih
            )
            db.session.add(talep)

        # Commit everything
        db.session.commit()
        print("✅ Ekstra demo verileri başarıyla oluşturuldu ve veritabanına kaydedildi.")

if __name__ == '__main__':
    run_seed()
