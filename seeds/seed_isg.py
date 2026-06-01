"""
FabrikaOS — İSG Demo Verisi (v2 — Genişletilmiş)
Kaza, Risk, Eğitim ve Yeni Eklenen Sağlık Muayenesi ile İSG Dokümanları
"""
import random
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi, SaglikMuayenesi, IsgDokumani
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[12/22] İş Sağlığı ve Güvenliği (İSG)...')
    random.seed(3456)

    bugun = date.today()
    calisanlar = Calisan.query.filter_by(aktif=True).all()
    isg_uzmani = Kullanici.query.filter_by(kullanici_adi='selin.aktas').first() or Kullanici.query.first()

    # ── İŞ KAZALARI VE RAMAK KALA (7) ──
    kazalar = [
        # İş Kazaları (3)
        {'yaralanma_tipi': 'Göze cisim batması', 'siddet': 'orta',
         'aciklama': 'CNC-001 tezgahında parça bağlarken koruyucu gözlük kullanılmaması nedeniyle göze talaş kaçtı.',
         'kok_neden': 'KKD kullanılmaması', 'duzeltici_faaliyet': 'Gözlük kullanımı denetimleri artırıldı, uyarı levhaları yenilendi.',
         'kayip_gun': 2, 'gun_once': 45, 'durum': 'kapandi', 'ramak_kala': False, 'uzuv': 'Göz', 'kaza_sekli': 'Cisim sıçraması'},
        {'yaralanma_tipi': 'Ezilme', 'siddet': 'hafif',
         'aciklama': 'Transpalet ile malzeme taşınırken tekerlek çalışanın ayağına çarptı.',
         'kok_neden': 'Dikkatsizlik, yaya yolu ihlali', 'duzeltici_faaliyet': 'Yaya ve araç yolları sarı çizgi ile belirginleştirildi.',
         'kayip_gun': 0, 'gun_once': 12, 'durum': 'acik', 'ramak_kala': False, 'uzuv': 'Ayak', 'kaza_sekli': 'Çarpma'},
        {'yaralanma_tipi': 'Kesik', 'siddet': 'orta',
         'aciklama': 'Abkant tezgahında çalışırken eldiven yırtılması sonucu sağ elde kesik.',
         'kok_neden': 'Uygun eldiven seçilmemesi', 'duzeltici_faaliyet': 'Daha dayanıklı kevlar eldiven tedarik edildi.',
         'kayip_gun': 3, 'gun_once': 85, 'durum': 'kapandi', 'ramak_kala': False, 'uzuv': 'El', 'kaza_sekli': 'Kesici cisimle temas'},

        # Ramak Kala (4)
        {'yaralanma_tipi': 'Yok', 'siddet': 'hafif',
         'aciklama': 'Tavan vinci ile kalıp taşınırken kanca kilit mekanizması tam oturmadı, yük sallandı ancak düşmedi.',
         'kok_neden': 'Kanca emniyet mandalı arızası', 'duzeltici_faaliyet': 'Tüm vinç kancaları kontrol edildi, arızalı olanlar değiştirildi.',
         'kayip_gun': 0, 'gun_once': 25, 'durum': 'kapandi', 'ramak_kala': True, 'uzuv': 'Yok', 'kaza_sekli': 'Yük düşme tehlikesi'},
        {'yaralanma_tipi': 'Yok', 'siddet': 'hafif',
         'aciklama': 'Hidrolik pres önünde dökülen yağ nedeniyle çalışan kaydı, düşmeden tutundu.',
         'kok_neden': 'Yağ sızıntısına anında müdahale edilmemesi', 'duzeltici_faaliyet': 'Döküntü kiti kullanımı eğitimi tazelendi.',
         'kayip_gun': 0, 'gun_once': 5, 'durum': 'acik', 'ramak_kala': True, 'uzuv': 'Yok', 'kaza_sekli': 'Kayma'},
        {'yaralanma_tipi': 'Yok', 'siddet': 'hafif',
         'aciklama': 'Bakım sırasında pano kapağı açılırken kablo temassızlığı kıvılcım çıkardı.',
         'kok_neden': 'Kablo izolasyon hatası', 'duzeltici_faaliyet': 'Panodaki tüm kablolar spiral boru ile izole edildi.',
         'kayip_gun': 0, 'gun_once': 18, 'durum': 'arastiriliyor', 'ramak_kala': True, 'uzuv': 'Yok', 'kaza_sekli': 'Elektrik arkı'},
        {'yaralanma_tipi': 'Yok', 'siddet': 'hafif',
         'aciklama': 'Kör noktada forklift ile personel karşılaştı, ani fren ile çarpışma önlendi.',
         'kok_neden': 'Kör noktada ayna olmaması', 'duzeltici_faaliyet': 'Kesişim noktalarına tümsek ayna monte edildi.',
         'kayip_gun': 0, 'gun_once': 60, 'durum': 'kapandi', 'ramak_kala': True, 'uzuv': 'Yok', 'kaza_sekli': 'Çarpışma tehlikesi'},
    ]

    for i, k in enumerate(kazalar):
        calisan = random.choice(calisanlar)
        kaz = IsKazasi(
            olay_no=f"ISG-{bugun.year}-{i+1000}",
            calisan_id=calisan.id,
            bildiren_id=isg_uzmani.id,
            tarih=datetime.now(timezone.utc) - timedelta(days=k['gun_once']),
            yer=random.choice(['Üretim Alanı', 'Depo', 'Bakım Atölyesi', 'Dış Alan']),
            yaralanma_tipi=k['yaralanma_tipi'],
            siddet=k['siddet'],
            uzuv=k['uzuv'],
            kaza_sekli=k['kaza_sekli'],
            kok_neden=k['kok_neden'],
            aciklama=k['aciklama'],
            duzeltici_faaliyet=k['duzeltici_faaliyet'],
            kayip_gun=k['kayip_gun'],
            durum=k['durum'],
            ramak_kala=k['ramak_kala'],
        )
        db.session.add(kaz)

    db.session.flush()

    # ── RİSK DEĞERLENDİRMESİ (12) ──
    print('[13/22] Risk Değerlendirmeleri...')

    riskler = [
        {'bolum': 'Talaşlı İmalat', 'tehlike': 'Uçuşan talaş parçaları', 'risk': 'Göz yaralanması, kesik', 'olasilik': 3, 'siddet': 3, 'onlem': 'Yan siperlikli koruyucu gözlük kullanımı zorunluluğu.', 'durum': 'acik'},
        {'bolum': 'Sac İşleme', 'tehlike': 'Gürültü', 'risk': 'İşitme kaybı', 'olasilik': 4, 'siddet': 3, 'onlem': 'Kulaklık/tıkaç kullanımı, gürültü haritası çıkarılması.', 'durum': 'devam'},
        {'bolum': 'Kaynak Atölyesi', 'tehlike': 'Kaynak dumanı ve gazı', 'risk': 'Solunum yolu rahatsızlıkları, zehirlenme', 'olasilik': 4, 'siddet': 4, 'onlem': 'Lokal emiş sistemlerinin bakımı, uygun maske kullanımı.', 'durum': 'acik'},
        {'bolum': 'Boyahane', 'tehlike': 'Parlayıcı/patlayıcı kimyasallar', 'risk': 'Yangın, patlama', 'olasilik': 2, 'siddet': 5, 'onlem': 'Ex-proof ekipman kullanımı, statik elektrik topraklaması.', 'durum': 'acik'},
        {'bolum': 'Depo', 'tehlike': 'Yüksekten malzeme düşmesi', 'risk': 'Ezilme, ağır yaralanma', 'olasilik': 3, 'siddet': 4, 'onlem': 'Raf statik hesabı kontrolü, yükseklik limit çizgileri.', 'durum': 'devam'},
        {'bolum': 'Depo', 'tehlike': 'Forklift çarpması', 'risk': 'Ağır yaralanma, ölüm', 'olasilik': 2, 'siddet': 5, 'onlem': 'Mavi spot lamba takılması, hız limitörü (8 km/s).', 'durum': 'kapandi'},
        {'bolum': 'Bakım Atölyesi', 'tehlike': 'Elektrik akımına kapılma', 'risk': 'Ciddi yaralanma, yanık, ölüm', 'olasilik': 2, 'siddet': 5, 'onlem': 'EKED (Etiketle Kilitle Emniyete Al Dene) prosedürü uygulaması.', 'durum': 'acik'},
        {'bolum': 'Genel Üretim', 'tehlike': 'Kaygan zemin', 'risk': 'Düşme, burkulma, kırık', 'olasilik': 3, 'siddet': 2, 'onlem': 'Dökülmelere anında müdahale, kaymaz zemin boyası.', 'durum': 'kapandi'},
        {'bolum': 'Ofisler', 'tehlike': 'Ergonomik olmayan oturuş', 'risk': 'Kas iskelet sistemi hastalıkları', 'olasilik': 4, 'siddet': 2, 'onlem': 'Ergonomi eğitimi, bel destekli koltuk tedariki.', 'durum': 'kapandi'},
        {'bolum': 'Dış Alan', 'tehlike': 'Buzlanma', 'risk': 'Düşme', 'olasilik': 3, 'siddet': 2, 'onlem': 'Tuzlama yapılması, uyarı levhası.', 'durum': 'kapandi'},
        {'bolum': 'Pres Hattı', 'tehlike': 'Uzuv sıkışması', 'risk': 'Amputasyon, ağır yaralanma', 'olasilik': 2, 'siddet': 5, 'onlem': 'Çift el kumanda butonu, ışık perdesi periyodik kontrolü.', 'durum': 'acik'},
        {'bolum': 'Kimyasal Deposu', 'tehlike': 'Kimyasal sızıntı/döküntü', 'risk': 'Zehirlenme, kimyasal yanık', 'olasilik': 2, 'siddet': 4, 'onlem': 'Taşma havuzu, uygun KKD bulundurma.', 'durum': 'devam'},
    ]

    for r in riskler:
        skor = r['olasilik'] * r['siddet']
        seviye = 'kritik' if skor >= 20 else 'yuksek' if skor >= 15 else 'orta' if skor >= 8 else 'dusuk'
        rd = RiskDegerlendirme(
            bolum=r['bolum'],
            tehlike=r['tehlike'],
            risk=r['risk'],
            olasilik=r['olasilik'],
            siddet=r['siddet'],
            risk_puani=skor,
            risk_seviyesi=seviye,
            ek_onlem=r['onlem'],
            sorumlu=isg_uzmani.ad_soyad,
            durum=r['durum'],
            olusturma_tarihi=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 180)),
        )
        db.session.add(rd)

    db.session.flush()

    # ── İSG EĞİTİMLERİ (20) ──
    print('[14/22] İSG Eğitimleri...')

    egitim_konulari = [
        ('Temel İSG Eğitimi', 12, 16),
        ('Yüksekte Çalışma', 24, 8),
        ('Yangın ve Acil Durum', 12, 4),
        ('İlk Yardım Farkındalık', 12, 4),
        ('Ergonomi', 12, 2),
        ('Kimyasallarla Güvenli Çalışma', 12, 4),
        ('KKD Kullanımı', 12, 2),
        ('EKED Prosedürü', 24, 4),
    ]

    for calisan in calisanlar:
        # Her çalışana 1 temel eğitim
        konu, ay, saat = egitim_konulari[0]
        gecmis_gun = random.randint(10, 400)
        tarih = bugun - timedelta(days=gecmis_gun)
        bitis = tarih + timedelta(days=ay * 30)
        durum = 'suresi_doldu' if bitis < bugun else 'gecerli'

        eg = IsgEgitimi(
            calisan_id=calisan.id,
            egitim_adi=konu,
            egitmen='İSG Uzmanı',
            egitim_tarihi=tarih,
            gecerlilik_bitis=bitis,
            egitim_suresi=saat,
            durum=durum,
        )
        db.session.add(eg)

        # Rastgele 1-2 ek eğitim
        for _ in range(random.randint(1, 2)):
            konu, ay, saat = random.choice(egitim_konulari[1:])
            gecmis_gun = random.randint(10, 800)
            tarih = bugun - timedelta(days=gecmis_gun)
            bitis = tarih + timedelta(days=ay * 30)
            durum = 'suresi_doldu' if bitis < bugun else 'gecerli'

            eg = IsgEgitimi(
                calisan_id=calisan.id,
                egitim_adi=konu,
                egitmen='Yetkili OSGB',
                egitim_tarihi=tarih,
                gecerlilik_bitis=bitis,
                egitim_suresi=saat,
                durum=durum,
            )
            db.session.add(eg)

    db.session.flush()

    # ── SAĞLIK MUAYENELERİ (10) ──
    print('[15/22] Sağlık Muayeneleri...')

    muayene_turleri = [
        'ise_giris',
        'periyodik',
        'ozel',
        'ayrilma'
    ]

    for _ in range(10):
        calisan = random.choice(calisanlar)
        tur = random.choice(muayene_turleri)
        gun_once = random.randint(5, 300)
        tarih = bugun - timedelta(days=gun_once)
        sonraki = tarih + timedelta(days=365) # 1 yıl sonra
        sonuc_secenekleri = ['uygun', 'uygun', 'uygun', 'sinirli_uygun', 'uygun_degil']
        sonuc = random.choice(sonuc_secenekleri)

        muayene = SaglikMuayenesi(
            calisan_id=calisan.id,
            muayene_tarihi=tarih,
            muayene_turu=tur,
            doktor_adi='Dr. Hakan Yılmaz (İşyeri Hekimi)',
            sonuc=sonuc,
            sonraki_muayene_tarihi=sonraki,
            notlar='Yıllık periyodik sağlık taraması.' if tur == 'periyodik' else None,
        )
        db.session.add(muayene)

    db.session.flush()

    # ── İSG DOKÜMANLARI (8) ──
    print('[16/22] İSG Dokümanları...')

    dokumanlar = [
        {'adi': 'Acil Durum Eylem Planı', 'tur': 'prosedur', 'rev': 3},
        {'adi': 'İSG Risk Değerlendirme Raporu', 'tur': 'saha_raporu', 'rev': 5},
        {'adi': 'İş Kazası Bildirim Formu', 'tur': 'form', 'rev': 2},
        {'adi': 'Yüksekte Çalışma Talimatı', 'tur': 'talimat', 'rev': 1},
        {'adi': 'KKD Teslim Tutanağı', 'tur': 'form', 'rev': 4},
        {'adi': 'Kimyasal Madde Döküntü Talimatı', 'tur': 'talimat', 'rev': 2},
        {'adi': 'Forklift Kullanma Prosedürü', 'tur': 'prosedur', 'rev': 1},
        {'adi': 'Aylık İSG Kurul Tutanağı', 'tur': 'tutanak', 'rev': 1},
    ]

    for d in dokumanlar:
        tarih = bugun - timedelta(days=random.randint(10, 200))
        gecerlilik = tarih + timedelta(days=365)
        dok = IsgDokumani(
            baslik=d['adi'],
            kategori=d['tur'],
            versiyon=d['rev'],
            gecerlilik_tarihi=gecerlilik,
            sorumlu_id=isg_uzmani.id,
            onay_durumu='onaylandi' if random.random() > 0.2 else 'onay_bekliyor',
        )
        db.session.add(dok)

    db.session.flush()
    print('  OK\n')
