"""
FabrikaOS — Kalite Kontrol Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — Hata kayıtları ve düzeltici faaliyetler

- 8 hata kaydı (Ölçüsel, yüzey, montaj, malzeme — gerçek endüstriyel hatalar)
- 5 düzeltici faaliyet (CAPA — 8D süreç yönetimi)
"""
from datetime import datetime, date, timedelta, timezone
from app.extensions import db
from app.models.kalite import HataKaydi, DuzelticiFaaliyet
from app.models.makine import Makine
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[9/12] Kalite kayıtları...')

    makineler = {m.kod: m.id for m in Makine.query.all()}
    calisanlar = {c.sicil_no: c.id for c in Calisan.query.all()}
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    admin_id = admin.id if admin else 1

    hatalar = [
            {
                'urun': 'Krank Mili Ø48',
                'parti': 'LOT-2026-0401',
                'hat': 'A Hattı',
                'hata_turu': 'Çap tolerans aşımı (+0.08mm)',
                'kategori': 'olcusel',
                'kaynak': 'makine',
                'adet': 12,
                'fire': 2.5,
                'vardiya': 'sabah',
                'makine': 'CNC-001',
                'calisan': 'P001',
                'aksiyon': 'tamir',
                'aciklama': 'Krank mili Ø48h7 çap ölçüsünde +0.08mm tolerans aşımı tespit edildi. '
                            'Ball screw backlash değeri 0.015mm üzerine çıkmış. '
                            'Takım aşınması kompanzasyonu güncellenmeli.',
                'gun': 3,
            },
            {
                'urun': 'Motor Kapağı (ABS)',
                'parti': 'LOT-2026-0398',
                'hat': 'B Hattı',
                'hata_turu': 'Yüzey çöküntüsü (sink mark)',
                'kategori': 'yuzey',
                'kaynak': 'malzeme',
                'adet': 18,
                'fire': 4.2,
                'vardiya': 'ogleden_sonra',
                'makine': 'ABK-001',
                'calisan': 'P002',
                'aksiyon': 'hurda',
                'aciklama': 'Büküm esnasında yüzeyde çatlama oluştu. '
                            'Malzeme sertliği beklenen değerin üzerinde.',
                'gun': 8,
            },
            {
                'urun': 'Bağlantı Plakası (St37)',
                'parti': 'LOT-2026-0405',
                'hat': 'C Hattı',
                'hata_turu': 'Delik merkez sapması (0.35mm)',
                'kategori': 'montaj',
                'kaynak': 'metot',
                'adet': 5,
                'fire': 1.3,
                'vardiya': 'sabah',
                'makine': 'PRS-001',
                'calisan': 'P005',
                'aksiyon': 'sartli_kabul',
                'aciklama': 'Bağlantı plakası 4×M8 delik merkezleri nominal değerden 0.35mm kaymış. '
                            'Fikstür referans pimi aşınması tespit edildi. '
                            'Montaj sırasında M8 cıvatalar zorlanarak geçiyor.',
                'gun': 14,
            },
            {
                'urun': 'Kaynaklı Şase Profili',
                'parti': 'LOT-2026-0410',
                'hat': 'D Hattı',
                'hata_turu': 'Kaynak porozitesi',
                'kategori': 'yuzey',
                'kaynak': 'iscilik',
                'adet': 3,
                'fire': 1.8,
                'vardiya': 'gece',
                'makine': 'KYN-001',
                'calisan': 'P011',
                'aksiyon': 'tamir',
                'aciklama': 'MIG kaynak dikişinde porozite (gözeneklilik) tespit edildi. '
                            'Gaz debisi kontrol edildi: CO2/Ar karışım oranı 18/82 olması gerekirken '
                            '12/88 ölçüldü. Operatör gaz ayarını değiştirmiş.',
                'gun': 5,
            },
            {
                'urun': 'Rulman Yatağı (42CrMo4)',
                'parti': 'LOT-2026-0415',
                'hat': 'A Hattı',
                'hata_turu': 'İç çap Ra yüzey pürüzlülüğü',
                'kategori': 'olcusel',
                'kaynak': 'makine',
                'adet': 7,
                'fire': 2.0,
                'vardiya': 'sabah',
                'makine': 'TSL-001',
                'calisan': 'P012',
                'aksiyon': 'hurda',
                'aciklama': 'Rulman yatağı iç çap taşlamasında yüzey pürüzlülüğü Ra 0.8 yerine '
                            'Ra 1.6 ölçüldü. Taşlama taşı dengesizliği ve soğutma sıvısı '
                            'debisi düşüklüğü birlikte etki etmiş.',
                'gun': 2,
            },
            {
                'urun': 'Valf Gövdesi (Alüminyum)',
                'parti': 'LOT-2026-0420',
                'hat': 'A Hattı',
                'hata_turu': 'Talaş kalıntısı (iç kanal)',
                'kategori': 'yuzey',
                'kaynak': 'iscilik',
                'adet': 4,
                'fire': 0.9,
                'vardiya': 'ogleden_sonra',
                'makine': 'CNC-002',
                'calisan': 'P001',
                'aksiyon': 'tamir',
                'aciklama': 'Valf gövdesi iç kanallarında talaş kalıntısı kaldı. '
                            'Basınç testi sırasında kaçak tespit edildi. '
                            'CNC programında talaş kırma döngüsü eksik.',
                'gun': 6,
            },
            {
                'urun': 'Piston Kolu',
                'parti': 'LOT-2026-0425',
                'hat': 'A Hattı',
                'hata_turu': 'Sertlik değeri düşük (HRC 48 vs. spec 52)',
                'kategori': 'malzeme',
                'kaynak': 'malzeme',
                'adet': 10,
                'fire': 3.1,
                'vardiya': 'sabah',
                'makine': 'CNC-001',
                'calisan': 'P001',
                'aksiyon': 'hurda',
                'aciklama': 'Isıl işlem sonrası sertlik ölçümü HRC 48 geldi — '
                            'müşteri spesifikasyonu HRC 52±2. '
                            'Hammadde sertifika kontrolünde C oranı düşük tespit edildi.',
                'gun': 11,
            },
            {
                'urun': 'Flanş Plakası',
                'parti': 'LOT-2026-0430',
                'hat': 'B Hattı',
                'hata_turu': 'Lazer Kesim Çapağı',
                'kategori': 'yuzey',
                'kaynak': 'makine',
                'adet': 25,
                'fire': 5.0,
                'vardiya': 'ogleden_sonra',
                'makine': 'ABK-001',
                'calisan': 'P002',
                'aksiyon': 'tamir',
                'aciklama': 'Alt yüzeyde lazer kesim sonrası çapak oluşumu. '
                            'Lazer odak noktası ayarı bozulmuş.',
                'gun': 1,
            },
        ]

    for h in hatalar:
        tarih = datetime.now(timezone.utc) - timedelta(days=h['gun'])
        makine_id = makineler.get(h['makine'])
        if not makine_id:
            continue

        hk = HataKaydi(
            makine_id=makine_id,
            calisan_id=calisanlar.get(h['calisan']),
            urun_adi=h['urun'],
            parti_no=h['parti'],
            hat=h['hat'],
            hata_turu=h['hata_turu'],
            hata_kategorisi=h['kategori'],
            hata_kaynagi=h['kaynak'],
            adet=h['adet'],
            fire_orani=h['fire'],
            vardiya=h['vardiya'],
            aciklama=h['aciklama'],
            aksiyon_karari=h['aksiyon'],
            tarih=tarih,
            kaydeden_id=admin_id,
        )
        db.session.add(hk)
        print(f'  + Hata: {h["urun"]} — {h["hata_turu"]}')

    db.session.flush()

    # ── DÜZELTİCİ FAALİYETLER (5 adet CAPA) ──
    hata_kayitlari = HataKaydi.query.order_by(HataKaydi.id).all()

    faaliyetler = [
            {
                'idx': 0,  # Krank mili çap tolerans
                'capa': 'CAPA-2026-001',
                'kok': 'CNC-001 X ekseni ball screw backlash değeri 0.015mm üzerine çıkmış. '
                       'Son bakımda backlash ölçümü yapılmış ancak kompanzasyon parametresi '
                       'güncellenmemiş.',
                'kategori': 'makine',
                'faaliyet': '1) Ball screw backlash kompanzasyon parametresi güncellendi.\n'
                            '2) Periyodik bakım kontrol listesine backlash ölçümü eklendi.\n'
                            '3) Her parti başında ilk parça ölçüm zorunluluğu getirildi.',
                'gecici': 'Üretim devam ederken her 20 parçada 1 ölçüm yapılması talimatı verildi.',
                'durum': 'devam',
                'hedef': date.today() + timedelta(days=7),
            },
            {
                'idx': 1,  # Motor kapağı sink mark
                'capa': 'CAPA-2026-002',
                'kok': 'Malzeme sertliği tolerans dışı.',
                'kategori': 'malzeme',
                'faaliyet': '1) Tedarikçiye Kalite Uyarı Raporu (NCR-2026-008) gönderildi.\n',
                'gecici': 'Mevcut parti karantinaya alındı, yeni partiden üretim başlatıldı.',
                'durum': 'dogrulama',
                'hedef': date.today() - timedelta(days=2),
                'tamamlanma': date.today() - timedelta(days=1),
                'dogrulama': 'Yeni partiden numune üretildi. Kontrol OK.',
            },
            {
                'idx': 3,  # Kaynak porozitesi
                'capa': 'CAPA-2026-003',
                'kok': 'Operatör gaz ayarını CO2/Ar oranı 18/82 yerine 12/88 olarak değiştirmiş. '
                       'Gaz debimetre skala işareti silinmiş olduğundan yanlış okuma yapılmış.',
                'kategori': 'insan',
                'faaliyet': '1) Kaynak parametreleri talimatı (WPS-KYN-001 Rev.03) güncellendi.\n'
                            '2) Tüm kaynak operatörlerine 2 saatlik eğitim verildi.\n'
                            '3) Gaz debimetre skalası yenilendi, kilitleme mekanizması eklendi.\n'
                            '4) Vardiya başı parametre onay formu oluşturuldu.',
                'gecici': 'Vardiya başı kalite kontrol mühendisi parametre onayı veriyor.',
                'durum': 'kapandi',
                'hedef': date.today() - timedelta(days=3),
                'tamamlanma': date.today() - timedelta(days=2),
                'dogrulama': 'Son 5 iş gününde toplam 45 kaynaklı parça üretildi. '
                             'NDT (penetrant testi) ile kontrol edildi — 0 porozite.',
            },
            {
                'idx': 4,  # Rulman yatağı yüzey pürüzlülüğü
                'capa': 'CAPA-2026-004',
                'kok': 'Taşlama taşı dinamik dengesi bozulmuş (balans kaybı). Aynı anda '
                       'soğutma sıvısı filtresi tıkanarak debi %40 düşmüş. İki faktör '
                       'birlikte yüzey kalitesini olumsuz etkilemiş.',
                'kategori': 'makine',
                'faaliyet': '1) Taşlama taşı balans ayarı periyodu 30 günden 15 güne düşürüldü.\n'
                            '2) Soğutma sıvısı filtre değişim periyodu 2 haftaya güncellendi.\n'
                            '3) Yüzey pürüzlülüğü ölçüm sıklığı her parti olarak belirlendi.',
                'gecici': 'Taşlama taşı yenisiyle değiştirildi, filtre temizlendi.',
                'durum': 'devam',
                'hedef': date.today() + timedelta(days=14),
            },
            {
                'idx': 6,  # Piston kolu sertlik
                'capa': 'CAPA-2026-005',
                'kok': 'Hammadde sertifikasında C oranı %0.38 — spesifikasyon min %0.42. '
                       'Tedarikçiden gelen çelik partisi uyumsuz. Giriş kontrolünde '
                       'yalnızca ölçüsel kontrol yapılmış, kimyasal analiz atlanmış.',
                'kategori': 'malzeme',
                'faaliyet': '1) Tedarikçiye uygunsuzluk raporu gönderildi (NCR-2026-012).\n'
                            '2) Giriş kalite kontrolüne taşınabilir XRF spektrometre ile '
                            'kimyasal analiz eklendi.\n'
                            '3) Tedarikçi denetim planı oluşturuldu.',
                'gecici': 'Mevcut parti iade edildi, alternatif tedarikçiden acil sipariş verildi.',
                'durum': 'acik',
                'hedef': date.today() + timedelta(days=21),
            },
        ]

    for f in faaliyetler:
        if f['idx'] >= len(hata_kayitlari):
            continue
        df = DuzelticiFaaliyet(
            capa_no=f['capa'],
            hata_kaydi_id=hata_kayitlari[f['idx']].id,
            ekip_lideri_id=admin_id,
            kok_neden=f['kok'],
            neden_kategorisi=f['kategori'],
            faaliyet=f['faaliyet'],
            gecici_onlem=f.get('gecici'),
            sorumlu_id=admin_id,
            hedef_tarih=f['hedef'],
            durum=f['durum'],
            tamamlanma_tarihi=f.get('tamamlanma'),
            dogrulama_notu=f.get('dogrulama'),
            dogrulayan_id=admin_id if f.get('dogrulama') else None,
        )
        db.session.add(df)
        print(f'  + CAPA: {f["capa"]} ({f["durum"]})')

    db.session.flush()
    print('  OK\n')
