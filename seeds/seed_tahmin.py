"""
FabrikaOS — AI Tahminleme Demo Verisi
Senaryo: AnadoluTech Metal Sanayi A.Ş.

AI Tahminleme modülünün dört alt bileşeni için gerçekçi tahmin kayıtları:
- Kestirimci Bakım: Makine bazlı arıza olasılıkları
- OEE Tahmini: Gelecek dönem OEE trend tahminleri
- Stok Tükenme: Malzeme bazlı stok tükenme tahminleri
- Anomali Tespiti: Üretim/enerji/kalite anomalileri
"""
import json
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.tahmin import TahminKaydi
from app.models.makine import Makine
from app.models.stok import Malzeme


def seed():
    print('[12/12] AI Tahmin kayıtları...')

    makineler = {m.kod: m for m in Makine.query.all()}
    malzemeler = {m.kod: m for m in Malzeme.query.all()}
    bugun = date.today()

    tahminler = []

    # ══════════════════════════════════════════════════════════════
    # KESİTİRİMCİ BAKIM TAHMİNLERİ
    # ══════════════════════════════════════════════════════════════
    if 'PRS-001' in makineler:
        m = makineler['PRS-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='bakim',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='Hidrolik Silindir Keçe Yenileme Gerekli',
            aciklama='Son 15 günde basınç kaybı trendi analiz edildi. '
                     'Hidrolik silindir rod keçesi aşınma belirtileri gösteriyor. '
                     'Mevcut basınç: 145 bar (nominal: 180 bar). '
                     'Keçe değişimi yapılmazsa 7-10 gün içinde tam durma riski.',
            risk_skoru=88.5,
            tahmin_tarihi=bugun + timedelta(days=8),
            tahmini_gun=8,
            oneri='1) Acil keçe siparişi verilmeli (Schuler OEM parça no: HSR-200-KS)\n'
                  '2) Planlı duruş organize edilerek keçe değişimi yapılmalı\n'
                  '3) Hidrolik yağ filtresi de aynı anda değiştirilmeli',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'basinc_trendi': [178, 172, 165, 158, 150, 145],
                'olcum_gunleri': 6,
                'tahmini_maliyet': 12500,
                'oncelik': 'kritik'
            }, ensure_ascii=False),
        ))

    if 'CNC-001' in makineler:
        m = makineler['CNC-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='bakim',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='Spindle Rulman Ömrü Dolmak Üzere',
            aciklama='Spindle titreşim verileri son 30 günde %18 artış gösterdi. '
                     'Frekans analizi rulman iç bilezik hasarı sinyali veriyor. '
                     'Tahmini kalan ömür: 25-35 gün.',
            risk_skoru=72.0,
            tahmin_tarihi=bugun + timedelta(days=30),
            tahmini_gun=30,
            oneri='1) Bir sonraki periyodik bakımda spindle rulman değişimi planlanmalı\n'
                  '2) SKF 7210 BEP rulman (2 adet) sipariş edilmeli\n'
                  '3) Titreşim izleme sıklığı günlük yapılmalı',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'titresim_rms': [1.2, 1.4, 1.6, 1.8, 2.1, 2.5],
                'esik_deger': 4.0,
                'rulman_tipi': 'SKF 7210 BEP',
                'tahmini_maliyet': 8500
            }, ensure_ascii=False),
        ))

    if 'ENJ-001' in makineler:
        m = makineler['ENJ-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='bakim',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='Toggle Mekanizması Acil Bakım Gerekli',
            aciklama='Kilitleme kuvveti verileri son hafta %12 düştü. '
                     'Toggle pin aşınması hızlanıyor. Ürünlerde çapak oluşumu arttı. '
                     '48 saat içinde müdahale edilmezse üretim durabilir.',
            risk_skoru=92.0,
            tahmin_tarihi=bugun + timedelta(days=2),
            tahmini_gun=2,
            oneri='1) ACİL: Toggle pin seti sipariş edilmeli (Arburg P/N: TG-570-PIN)\n'
                  '2) Hafta sonu planlı duruşta değişim yapılmalı\n'
                  '3) Kilitleme kuvveti kalibrasyonu sonrası doğrulama',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'kilitleme_kuvveti_trend': [570, 555, 540, 520, 505],
                'nominal_kuvvet': 570,
                'asınma_orani_pct': 11.4,
                'tahmini_maliyet': 22000
            }, ensure_ascii=False),
        ))

    if 'KYN-001' in makineler:
        m = makineler['KYN-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='bakim',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='J2 Eksen Reducer Yağ Değişimi Yaklaşıyor',
            aciklama='Son bakımdan bu yana 28 gün geçti (periyot: 30 gün). '
                     'Reducer sıcaklık trendi normal seviyede ancak yağlama '
                     'periyodu dolmak üzere.',
            risk_skoru=35.0,
            tahmin_tarihi=bugun + timedelta(days=2),
            tahmini_gun=2,
            oneri='1) Nabtesco RV reducer yağı hazırlanmalı (0.6 litre)\n'
                  '2) Hafta sonu bakım planına dahil edilmeli',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'son_bakim_gunu': 28,
                'periyot': 30,
                'sicaklik_trend': [42, 43, 43, 44, 44],
                'tahmini_maliyet': 1200
            }, ensure_ascii=False),
        ))

    if 'TSL-001' in makineler:
        m = makineler['TSL-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='bakim',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='Taşlama Taşı Ömrü %15 Kaldı',
            aciklama='Taşlama taşı çap ölçümü nominal 400mm → mevcut 348mm. '
                     'Minimum kullanılabilir çap 340mm. Tahmini kalan ömür: 12-18 iş günü.',
            risk_skoru=55.0,
            tahmin_tarihi=bugun + timedelta(days=15),
            tahmini_gun=15,
            oneri='1) Norton 46 grit taşlama taşı sipariş edilmeli\n'
                  '2) Değişim sonrası balans ayarı planlanmalı\n'
                  '3) Soğutma sıvısı filtresi de kontrol edilmeli',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'cap_trendi': [400, 390, 378, 365, 355, 348],
                'minimum_cap': 340,
                'kalan_yuzde': 15,
                'tahmini_maliyet': 3200
            }, ensure_ascii=False),
        ))

    # ══════════════════════════════════════════════════════════════
    # OEE TAHMİNLERİ
    # ══════════════════════════════════════════════════════════════
    if 'CNC-002' in makineler:
        m = makineler['CNC-002']
        tahminler.append(TahminKaydi(
            tahmin_turu='oee',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='OEE Düşüş Trendi: Sonraki 7 Gün %74-78 Bekleniyor',
            aciklama='Son 14 günlük OEE ortalaması %76.2 ile hedef %82\'nin altında. '
                     'Performans bileşeni düşük: takım değişim süreleri artmış. '
                     'Gelecek hafta sipariş yoğunluğu düşünüldüğünde iyileşme fırsatı.',
            risk_skoru=62.0,
            tahmin_tarihi=bugun + timedelta(days=7),
            tahmini_gun=7,
            oneri='1) ATC gripper pençelerinin durumu kontrol edilmeli\n'
                  '2) Takım ön ayar istasyonu kullanımı artırılmalı\n'
                  '3) Setup sürelerini azaltmak için SMED uygulanmalı',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'son_14gun_oee': [78.5, 74.2, 76.8, 73.1, 79.0, 75.4, 72.9,
                                  77.3, 74.8, 76.5, 73.7, 78.2, 75.0, 74.6],
                'hedef_oee': 82.0,
                'tahmin_oee': [75.5, 76.0, 74.8, 77.2, 76.5, 75.8, 78.0],
                'en_zayif_bilesen': 'performans'
            }, ensure_ascii=False),
        ))

    if 'CNC-001' in makineler:
        m = makineler['CNC-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='oee',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='OEE Stabil: Sonraki 7 Gün %83-87 Bekleniyor',
            aciklama='Son 14 günlük OEE ortalaması %84.7 ile hedef %85\'e yakın. '
                     'Tüm bileşenler dengeli. Bakım sonrası performans iyileşmesi '
                     'gözlemleniyor.',
            risk_skoru=22.0,
            tahmin_tarihi=bugun + timedelta(days=7),
            tahmini_gun=7,
            oneri='Mevcut performans hedef seviyesinde. İzlemeye devam edilmeli.',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'son_14gun_oee': [83.5, 85.2, 86.1, 84.3, 85.8, 83.9, 87.0,
                                  84.5, 86.3, 85.0, 83.7, 84.8, 85.5, 84.2],
                'hedef_oee': 85.0,
                'tahmin_oee': [84.5, 85.0, 84.8, 86.2, 85.5, 84.8, 85.5],
                'en_zayif_bilesen': None
            }, ensure_ascii=False),
        ))

    # ══════════════════════════════════════════════════════════════
    # STOK TÜKENME TAHMİNLERİ
    # ══════════════════════════════════════════════════════════════
    stok_tahminleri = [
        {
            'kod': 'MLZ-006',
            'baslik': 'KRİTİK: Kesim Dirençli Eldiven 5 Gün İçinde Tükenecek',
            'aciklama': 'Mevcut stok: 12 adet. Günlük ortalama tüketim: 2.4 adet. '
                        'Minimum stok seviyesi: 40 adet. Stok zaten kritik seviyenin altında! '
                        'Tedarikçi teslimat süresi: 5-7 iş günü.',
            'risk': 95.0,
            'gun': 5,
            'oneri': '1) ACİL sipariş verilmeli (min. 200 adet)\n'
                     '2) Alternatif tedarikçiden acil temin araştırılmalı\n'
                     '3) Dağıtım kontrol altına alınmalı',
        },
        {
            'kod': 'MLZ-004',
            'baslik': 'MIG Kaynak Teli 18 Gün İçinde Tükenecek',
            'aciklama': 'Mevcut stok: 42 kg. Haftalık ortalama tüketim: 16 kg. '
                        'Minimum stok: 25 kg. Mevcut tüketim hızıyla 2.5 haftada '
                        'minimum stok seviyesine düşecek.',
            'risk': 58.0,
            'gun': 18,
            'oneri': '1) Haftalık sipariş planına 20 kg eklenmeli\n'
                     '2) Kaynak robotu tüketim verimi kontrol edilmeli',
        },
        {
            'kod': 'MLZ-007',
            'baslik': 'CNC Soğutma Sıvısı Stoku Azalıyor',
            'aciklama': 'Mevcut stok: 95 litre. Aylık ortalama tüketim: 45 litre. '
                        'Minimum stok: 50 litre. 30 gün sonra minimum stok seviyesine '
                        'yaklaşacak.',
            'risk': 42.0,
            'gun': 30,
            'oneri': '1) Aylık rutin siparişe dahil edilmeli\n'
                     '2) Konsantrasyon ölçümü ile verimlilik artırılabilir',
        },
        {
            'kod': 'MLZ-001',
            'baslik': 'CNC Kesici Uç Stoku Yeterli Ancak İzlenmeli',
            'aciklama': 'Mevcut stok: 145 adet. Haftalık ortalama tüketim: 12 adet. '
                        'Minimum stok: 50 adet. Yaklaşık 8 haftalık stok mevcut.',
            'risk': 15.0,
            'gun': 56,
            'oneri': 'Mevcut stok seviyesi yeterli. Standart sipariş planı yeterli.',
        },
    ]

    for st in stok_tahminleri:
        malzeme = malzemeler.get(st['kod'])
        if not malzeme:
            continue
        tahminler.append(TahminKaydi(
            tahmin_turu='stok',
            kaynak_turu='malzeme',
            kaynak_id=malzeme.id,
            kaynak_adi=f'{malzeme.ad} ({malzeme.kod})',
            baslik=st['baslik'],
            aciklama=st['aciklama'],
            risk_skoru=st['risk'],
            tahmin_tarihi=bugun + timedelta(days=st['gun']),
            tahmini_gun=st['gun'],
            oneri=st['oneri'],
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'mevcut_stok': float(malzeme.mevcut_miktar),
                'minimum_stok': float(malzeme.minimum_stok),
                'tahmini_tukenme_gun': st['gun'],
            }, ensure_ascii=False),
        ))

    # ══════════════════════════════════════════════════════════════
    # ANOMALİ TESPİTLERİ
    # ══════════════════════════════════════════════════════════════
    if 'ENJ-001' in makineler:
        m = makineler['ENJ-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='anomali',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='Anormal Enerji Tüketim Artışı Tespit Edildi',
            aciklama='Son 7 günde enjeksiyon makinesinin saat başı enerji tüketimi '
                     'ortalamanın %23 üzerine çıktı. Kovan ısıtıcı bantlardan birinin '
                     'aşırı akım çekiyor olması muhtemel. Termal kamera ile kontrol önerilir.',
            risk_skoru=68.0,
            tahmin_tarihi=bugun,
            tahmini_gun=0,
            oneri='1) Termal kamera ile ısıtıcı bantlar kontrol edilmeli\n'
                  '2) Her bant bölgesinin amperi ayrı ölçülmeli\n'
                  '3) Arızalı bant tespit edilirse hemen değiştirilmeli',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'anomali_tipi': 'enerji_tuketim',
                'sapma_yuzde': 23.4,
                'normal_tuketim_kwh': 18.5,
                'guncel_tuketim_kwh': 22.8,
                'tespit_tarihi': bugun.isoformat()
            }, ensure_ascii=False),
        ))

    if 'CNC-001' in makineler:
        m = makineler['CNC-001']
        tahminler.append(TahminKaydi(
            tahmin_turu='anomali',
            kaynak_turu='makine',
            kaynak_id=m.id,
            kaynak_adi=f'{m.ad} ({m.kod})',
            baslik='Kalite Anomalisi: Hatalı Üretim Oranı Artışı',
            aciklama='Son 5 iş gününde CNC-001 hatalı üretim oranı %1.2 → %3.8 '
                     'yükseldi. Ball screw backlash kompanzasyonu güncellendikten sonra '
                     'belirli parça tiplerinde tolerans aşımı devam ediyor.',
            risk_skoru=52.0,
            tahmin_tarihi=bugun,
            tahmini_gun=0,
            oneri='1) X ekseni backlash değeri lazer interferometre ile doğrulanmalı\n'
                  '2) Etkilenen parti numaraları kalite kontrole bildirilmeli\n'
                  '3) Gerekirse iş parçası bağlama fikstürü kontrol edilmeli',
            model_versiyonu='v2.1',
            meta_veri=json.dumps({
                'anomali_tipi': 'kalite',
                'hata_orani_trend': [1.2, 1.5, 2.1, 3.0, 3.8],
                'normal_hata_orani': 1.5,
                'etkilenen_urun': 'Krank Mili Ø48'
            }, ensure_ascii=False),
        ))

    tahminler.append(TahminKaydi(
        tahmin_turu='anomali',
        kaynak_turu='enerji',
        kaynak_id=0,
        kaynak_adi='Genel Fabrika',
        baslik='Gece Vardiyası Enerji Tüketimi Normalin Üzerinde',
        aciklama='Son 10 günde gece vardiyası elektrik tüketimi gündüz vardiyasına oranla '
                 'normalden %15 daha yüksek. Olası nedenler: aydınlatma sistemi düzenlenmemiş '
                 'olabilir veya bazı makineler boşta çalışıyor olabilir.',
        risk_skoru=38.0,
        tahmin_tarihi=bugun,
        tahmini_gun=0,
        oneri='1) Gece vardiyası enerji sayaç logları incelenmeli\n'
              '2) Boşta çalışan makine kontrol edilmeli\n'
              '3) Aydınlatma sistemi hareket sensörlü yapılabilir',
        model_versiyonu='v2.1',
        meta_veri=json.dumps({
            'anomali_tipi': 'enerji_pattern',
            'gece_gunduz_oran': 1.15,
            'normal_oran': 0.85,
            'potansiyel_tasarruf_tl': 4200
        }, ensure_ascii=False),
    ))

    # Kayıtları ekle
    for t in tahminler:
        t.olusturma_tarihi = datetime.now(timezone.utc) - timedelta(hours=2)
        db.session.add(t)

    db.session.flush()
    print(f'  + {len(tahminler)} AI tahmin kaydı oluşturuldu')
    print('    - Kestirimci Bakım: 5 tahmin')
    print('    - OEE Tahmini: 2 tahmin')
    print('    - Stok Tükenme: 4 tahmin')
    print('    - Anomali Tespiti: 3 tahmin')
    print('  OK\n')
