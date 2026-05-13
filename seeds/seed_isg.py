"""
FabrikaOS — İSG (İş Sağlığı ve Güvenliği) Demo Verisi
Senaryo: AnadoluTech Metal Sanayi

- 5 kaza/ramak kala olayı (çeşitli şiddet seviyeleri)
- 8 risk değerlendirme (5×5 matris, çeşitli bölümler)
- 12 İSG eğitimi (tüm kategoriler, geçerli + süresi dolmuş)
"""
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[11/12] İSG kayıtları...')

    calisanlar = {c.sicil_no: c.id for c in Calisan.query.all()}
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    admin_id = admin.id if admin else 1

    # ══════════════════════════════════════════════════════════════
    # İŞ KAZALARI & RAMAK KALA (5 olay)
    # ══════════════════════════════════════════════════════════════
    kazalar = [
        {
            'olay_no': 'KZ-2026-001',
            'calisan': 'P005',
            'vardiya': 'sabah',
            'yer': 'C Hattı — Pres Bölgesi',
            'yaralanma': 'Ezilme yaralanması',
            'uzuv': 'Sağ el 3. ve 4. parmak',
            'siddet': 'orta',
            'sekil': 'sikisma',
            'gun_once': 48,
            'kok': 'Kalıp değişimi sırasında güvenlik bariyeri devre dışı bırakılmış. '
                   'Operatör kalıp pozisyonunu elle ayarlarken pres otomatik kapanma yapmış.',
            'aciklama': 'Pres makinesi PRS-001 kalıp değişimi sırasında çift el kumanda '
                        'bypass edilmiş durumda. Operatör kalıp hizalama yaparken pres '
                        'ani kapanma yaptı. 2. derece ezilme, kırık yok. '
                        'Acil servise sevk edildi, 5 gün istirahat.',
            'duzeltici': '1) Çift el kumanda bypass önleme kilidi takıldı.\n'
                         '2) Kalıp değişimi prosedürü güncellendi (Lockout/Tagout zorunlu).\n'
                         '3) Tüm pres operatörlerine güvenlik eğitimi verildi.',
            'kayip_gun': 5,
            'ramak': False,
            'durum': 'kapandi',
        },
        {
            'olay_no': 'KZ-2026-002',
            'calisan': 'P009',
            'vardiya': 'ogleden_sonra',
            'yer': 'A Hattı — CNC Talaşlı İmalat',
            'yaralanma': 'Kesik',
            'uzuv': 'Sol el bileği iç kısım',
            'siddet': 'hafif',
            'sekil': 'kesilme',
            'gun_once': 22,
            'kok': 'CNC tezgah talaş temizliği sırasında kesimci eldiven giyilmemiş. '
                   'Spiral şekilli çelik talaş elden kayarak bileği kesmiş.',
            'aciklama': 'CNC-001 tezgahında talaş temizliği yaparken çelik talaş sol '
                        'bilekte 3cm kesik oluşturdu. İlk yardım ünitesinde müdahale '
                        'edildi. Dikilme gerekmedi. 1 gün istirahat.',
            'duzeltici': '1) Talaş temizlik prosedürü güncellendi — eldiven zorunlu.\n'
                         '2) KKD denetim sıklığı haftada 2\'ye çıkarıldı.\n'
                         '3) Talaş temizliği için özel kanca alet temin edildi.',
            'kayip_gun': 1,
            'ramak': False,
            'durum': 'kapandi',
        },
        {
            'olay_no': 'RK-2026-001',
            'calisan': 'P008',
            'vardiya': 'sabah',
            'yer': 'Depo Alanı — Hammadde Bölümü',
            'yaralanma': 'Yok (Ramak Kala)',
            'uzuv': None,
            'siddet': 'hafif',
            'sekil': 'dusme',
            'gun_once': 12,
            'kok': 'Depo zemin temizliği sonrası ıslak zemin uyarı levhası konmamış. '
                   'Forklift geçişinden sıçrayan su ile zemin kayganlaşmış.',
            'aciklama': 'Depo sorumlusu ıslak zeminde kaydı, düşme olmadı ancak '
                        'dengesini son anda korudu. Yaralanma yok. Uyarı levhası '
                        'eksikliği tespit edildi.',
            'duzeltici': '1) Depo alanına 4 adet ıslak zemin uyarı standı temin edildi.\n'
                         '2) Anti-slip zemin kaplaması (3M Safety Walk) sipariş edildi.\n'
                         '3) Temizlik sonrası kontrol listesi oluşturuldu.',
            'kayip_gun': 0,
            'ramak': True,
            'durum': 'kapandi',
        },
        {
            'olay_no': 'RK-2026-002',
            'calisan': 'P007',
            'vardiya': 'gece',
            'yer': 'B Hattı — Enjeksiyon Alanı',
            'yaralanma': 'Yok (Ramak Kala)',
            'uzuv': None,
            'siddet': 'hafif',
            'sekil': 'dusme',
            'gun_once': 6,
            'kok': 'Forklift geçiş yolu ile yaya geçiş yolu ayrımı yetersiz. '
                   'Gece vardiyasında aydınlatma düşük.',
            'aciklama': 'Vardiya amiri B hattından depoya yürürken forklift ile '
                        'çarpışmaya ramak kaldı. Forklift operatörü son anda fren yaptı. '
                        'Mesafe yaklaşık 1 metre. Yaralanma yok.',
            'duzeltici': '1) Forklift güzergahı sarı bant ile yeniden çizildi.\n'
                         '2) Kavşak noktalarına konveks ayna yerleştirildi.\n'
                         '3) Gece vardiyası aydınlatması güçlendirildi (ek LED armatür).',
            'kayip_gun': 0,
            'ramak': True,
            'durum': 'arastiriliyor',
        },
        {
            'olay_no': 'RK-2026-003',
            'calisan': 'P011',
            'vardiya': 'sabah',
            'yer': 'D Hattı — Kaynak Bölgesi',
            'yaralanma': 'Yok (Ramak Kala)',
            'uzuv': None,
            'siddet': 'hafif',
            'sekil': 'dusme',
            'gun_once': 3,
            'kok': 'Kaynak kıvılcımı ile zemine düşen yağ lekesi tutuştu. '
                   'Küçük alev hemen söndürüldü.',
            'aciklama': 'Kaynak operasyonu sırasında kıvılcım zemine sıçradı. '
                        'Zemindeki hidrolik yağ lekesi kısa süreli alev aldı. '
                        'Yakındaki yangın söndürücü ile müdahale edildi. Hasar yok.',
            'duzeltici': '1) Kaynak öncesi alan temizlik kontrolü zorunlu hale getirildi.\n'
                         '2) Kaynak perdeleri yenilendi (alev geciktirici malzeme).\n'
                         '3) Yağ dökülme kiti (spill kit) kaynak alanına konuldu.',
            'kayip_gun': 0,
            'ramak': True,
            'durum': 'arastiriliyor',
        },
    ]

    for k in kazalar:
        tarih = datetime.now(timezone.utc) - timedelta(days=k['gun_once'])
        kaza = IsKazasi(
            olay_no=k['olay_no'],
            calisan_id=calisanlar.get(k['calisan'], 1),
            tarih=tarih,
            vardiya=k['vardiya'],
            yer=k['yer'],
            yaralanma_tipi=k['yaralanma'],
            uzuv=k['uzuv'],
            siddet=k['siddet'],
            kaza_sekli=k['sekil'],
            kok_neden=k['kok'],
            aciklama=k['aciklama'],
            duzeltici_faaliyet=k['duzeltici'],
            kayip_gun=k['kayip_gun'],
            ramak_kala=k['ramak'],
            durum=k['durum'],
            bildiren_id=admin_id,
        )
        db.session.add(kaza)
        tip = 'Ramak Kala' if k['ramak'] else 'İş Kazası'
        print(f'  + {tip}: {k["olay_no"]} — {k["siddet"]}')

    db.session.flush()

    # ══════════════════════════════════════════════════════════════
    # RİSK DEĞERLENDİRMELERİ (5×5 matris — 8 adet)
    # ══════════════════════════════════════════════════════════════
    riskler = [
        {
            'bolum': 'Pres Bölgesi (C Hattı)',
            'faaliyet': 'Kalıp değişimi ve ayar',
            'tehlike': 'Pres kapanma alanında el-kol sıkışması',
            'risk': 'Uzuv ezilmesi, kırık, kalıcı sakatlık',
            'olasilik': 3, 'siddet': 5,
            'mevcut': 'Çift el kumanda, mekanik güvenlik bariyeri, Lockout/Tagout prosedürü',
            'ek': 'Optik ışık perdesi (light curtain) montajı planlanıyor',
            'sorumlu': 'Mehmet Kaya',
            'hedef': date.today() + timedelta(days=30),
            'durum': 'acik',
        },
        {
            'bolum': 'CNC Bölgesi (A Hattı)',
            'faaliyet': 'Talaş temizliği ve bakım',
            'tehlike': 'Keskin çelik talaş ile temas',
            'risk': 'Kesik, batma yaralanması, göz yaralanması',
            'olasilik': 4, 'siddet': 2,
            'mevcut': 'Kesim dirençli eldiven, koruyucu gözlük, talaş kancası',
            'ek': 'Otomatik talaş konveyör sistemi araştırılıyor',
            'sorumlu': 'Selin Aktaş',
            'hedef': date.today() + timedelta(days=60),
            'durum': 'devam',
        },
        {
            'bolum': 'Depo Alanı',
            'faaliyet': 'Malzeme taşıma ve istifleme',
            'tehlike': 'Forklift — yaya çarpışması',
            'risk': 'Ciddi yaralanma, ölüm',
            'olasilik': 2, 'siddet': 5,
            'mevcut': 'Hız limiti (10 km/h), sarı zemin çizgileri, sesli uyarı',
            'ek': 'Yaya-forklift geçiş ayrımı, konveks ayna montajı tamamlandı',
            'sorumlu': 'Selin Aktaş',
            'hedef': date.today() - timedelta(days=5),
            'durum': 'kapandi',
        },
        {
            'bolum': 'Kaynak Bölgesi (D Hattı)',
            'faaliyet': 'MIG/MAG kaynak operasyonu',
            'tehlike': 'UV radyasyonu ve kaynak dumanı maruziyeti',
            'risk': 'Göz hasarı (ark gözü), solunum yolu hastalıkları',
            'olasilik': 3, 'siddet': 3,
            'mevcut': 'Otomatik kararan kaynak maskesi, lokal emme aspirasyonu',
            'ek': 'Merkezi havalandırma/aspirasyon sistemi projesi başlatıldı',
            'sorumlu': 'Ayşe Özkan',
            'hedef': date.today() + timedelta(days=90),
            'durum': 'acik',
        },
        {
            'bolum': 'Genel Üretim Alanı',
            'faaliyet': 'Tüm üretim faaliyetleri',
            'tehlike': '85 dB üzeri sürekli gürültü maruziyeti',
            'risk': 'Kalıcı işitme kaybı, tinnitus',
            'olasilik': 4, 'siddet': 3,
            'mevcut': 'Kulak tıkacı (SNR 33 dB) dağıtımı, uyarı tabelaları',
            'ek': 'Gürültü haritası çıkarılacak, makine bazlı akustik izolasyon planı',
            'sorumlu': 'Selin Aktaş',
            'hedef': date.today() + timedelta(days=45),
            'durum': 'acik',
        },
        {
            'bolum': 'Enjeksiyon Bölgesi (B Hattı)',
            'faaliyet': 'Kalıp sıcak yüzey teması',
            'tehlike': 'Sıcak kalıp ve eriyik plastik ile yanık',
            'risk': '2.-3. derece yanık',
            'olasilik': 3, 'siddet': 4,
            'mevcut': 'Isıya dayanıklı eldiven, "Sıcak Yüzey" uyarı etiketleri',
            'ek': 'Kalıp koruma bariyeri tasarımı devam ediyor',
            'sorumlu': 'Mehmet Kaya',
            'hedef': date.today() + timedelta(days=45),
            'durum': 'devam',
        },
        {
            'bolum': 'Elektrik Panoları',
            'faaliyet': 'Elektrik bakım/onarım',
            'tehlike': 'Elektrik çarpması (400V AC)',
            'risk': 'Ölüm, ciddi yanık',
            'olasilik': 2, 'siddet': 5,
            'mevcut': 'Yalıtımlı alet, iş izni sistemi, LOTO prosedürü',
            'ek': 'Arc flash analizi yaptırılacak, kişisel arc flash PPE temin edilecek',
            'sorumlu': 'Ayşe Özkan',
            'hedef': date.today() + timedelta(days=75),
            'durum': 'acik',
        },
        {
            'bolum': 'Kimyasal Depolama',
            'faaliyet': 'Yağ, soğutma sıvısı depolama',
            'tehlike': 'Kimyasal dökülme, göz/cilt teması',
            'risk': 'Kimyasal yanık, çevre kirliliği',
            'olasilik': 2, 'siddet': 3,
            'mevcut': 'MSDS dosyaları, dökülme kiti, göz duşu',
            'ek': 'Sızdırmaz toplama paletleri temin edilecek',
            'sorumlu': 'Elif Yıldız',
            'hedef': date.today() + timedelta(days=30),
            'durum': 'devam',
        },
    ]

    for r in riskler:
        rd = RiskDegerlendirme(
            bolum=r['bolum'],
            faaliyet=r['faaliyet'],
            tehlike=r['tehlike'],
            risk=r['risk'],
            olasilik=r['olasilik'],
            siddet=r['siddet'],
            mevcut_onlem=r['mevcut'],
            ek_onlem=r['ek'],
            sorumlu=r['sorumlu'],
            hedef_tarih=r['hedef'],
            durum=r['durum'],
        )
        rd.hesapla_risk()
        db.session.add(rd)
        print(f'  + Risk: {r["bolum"]} — {rd.risk_seviyesi} ({rd.risk_puani})')

    db.session.flush()

    # ══════════════════════════════════════════════════════════════
    # İSG EĞİTİMLERİ (12 adet — tüm kategoriler)
    # ══════════════════════════════════════════════════════════════
    egitimler = [
        # Temel İSG
        {'calisan': 'P001', 'kat': 'temel_isg', 'ad': 'Temel İSG Eğitimi (16 saat)',
         'sure': 16, 'tarih': date(2025, 6, 15), 'bitis': date(2026, 6, 15),
         'sertifika': 'ISG-2025-0412', 'egitmen': 'OSGB — Dr. Hakan Yılmaz'},
        {'calisan': 'P002', 'kat': 'temel_isg', 'ad': 'Temel İSG Eğitimi (16 saat)',
         'sure': 16, 'tarih': date(2025, 6, 15), 'bitis': date(2026, 6, 15),
         'sertifika': 'ISG-2025-0413', 'egitmen': 'OSGB — Dr. Hakan Yılmaz'},
        {'calisan': 'P005', 'kat': 'temel_isg', 'ad': 'Temel İSG Eğitimi (16 saat)',
         'sure': 16, 'tarih': date(2025, 9, 10), 'bitis': date(2026, 9, 10),
         'sertifika': 'ISG-2025-0501', 'egitmen': 'OSGB — Dr. Hakan Yılmaz'},

        # İlk yardım
        {'calisan': 'P003', 'kat': 'ilkyardim', 'ad': 'İlk Yardımcı Sertifika Eğitimi',
         'sure': 24, 'tarih': date(2025, 3, 10), 'bitis': date(2028, 3, 10),
         'sertifika': 'ILK-2025-0087', 'egitmen': 'Kızılay İlk Yardım Eğitim Merkezi'},
        {'calisan': 'P010', 'kat': 'ilkyardim', 'ad': 'İlk Yardımcı Sertifika Eğitimi',
         'sure': 24, 'tarih': date(2024, 11, 5), 'bitis': date(2027, 11, 5),
         'sertifika': 'ILK-2024-0301', 'egitmen': 'Kızılay İlk Yardım Eğitim Merkezi'},

        # Mesleki güvenlik
        {'calisan': 'P005', 'kat': 'mesleki', 'ad': 'Pres Operatörü Güvenlik Eğitimi',
         'sure': 8, 'tarih': date(2025, 9, 20), 'bitis': date(2026, 9, 20),
         'sertifika': 'MSL-2025-0201', 'egitmen': 'Schuler Türkiye Teknik Ekibi'},
        {'calisan': 'P004', 'kat': 'mesleki',
         'ad': 'Elektrik Tesislerinde Güvenlik (Yüksek Gerilim)',
         'sure': 16, 'tarih': date(2025, 8, 1), 'bitis': date(2026, 8, 1),
         'sertifika': 'ELK-2025-0301', 'egitmen': 'TEİAŞ Eğitim Merkezi'},
        {'calisan': 'P011', 'kat': 'mesleki', 'ad': 'Kaynak Operatörü Güvenlik Eğitimi',
         'sure': 8, 'tarih': date(2025, 10, 15), 'bitis': date(2026, 10, 15),
         'sertifika': 'MSL-2025-0245', 'egitmen': 'FANUC Türkiye'},

        # Yangın
        {'calisan': 'P007', 'kat': 'yangin',
         'ad': 'Yangın Söndürme ve Acil Tahliye Eğitimi',
         'sure': 8, 'tarih': date(2025, 11, 5), 'bitis': date(2026, 11, 5),
         'sertifika': 'YNG-2025-0055', 'egitmen': 'İtfaiye Müdürlüğü'},
        {'calisan': 'P008', 'kat': 'yangin',
         'ad': 'Yangın Söndürme ve Acil Tahliye Eğitimi',
         'sure': 8, 'tarih': date(2025, 11, 5), 'bitis': date(2026, 11, 5),
         'sertifika': 'YNG-2025-0056', 'egitmen': 'İtfaiye Müdürlüğü'},

        # İSG Uzmanı yenileme — süresi DOLMUŞ
        {'calisan': 'P010', 'kat': 'temel_isg',
         'ad': 'İSG Uzmanı C Sınıfı Yenileme Eğitimi',
         'sure': 40, 'tarih': date(2025, 1, 15), 'bitis': date(2026, 1, 15),
         'sertifika': 'ISG-UZM-2025-001', 'egitmen': 'ÇASGEM'},

        # Ek eğitim — süresi DOLMUŞ
        {'calisan': 'P009', 'kat': 'ilkyardim', 'ad': 'Temel İlk Yardım Eğitimi',
         'sure': 16, 'tarih': date(2025, 4, 10), 'bitis': date(2026, 4, 10),
         'sertifika': 'ILK-2025-0145', 'egitmen': 'Kızılay'},
    ]

    for e in egitimler:
        durum = 'gecerli'
        if e['bitis'] < date.today():
            durum = 'suresi_doldu'

        eg = IsgEgitimi(
            calisan_id=calisanlar.get(e['calisan'], 1),
            egitim_kategorisi=e['kat'],
            egitim_adi=e['ad'],
            egitim_suresi=e['sure'],
            egitim_tarihi=e['tarih'],
            gecerlilik_bitis=e['bitis'],
            sertifika_no=e['sertifika'],
            egitmen=e['egitmen'],
            durum=durum,
        )
        db.session.add(eg)
        print(f'  + Eğitim: {e["calisan"]} — {e["ad"][:40]}... ({durum})')

    db.session.flush()
    print('  OK\n')
