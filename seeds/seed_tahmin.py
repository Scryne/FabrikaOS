"""
FabrikaOS — AI Tahminleme Demo Verisi (v2)
Makine arıza tahminleri, kalite trendleri vb.
"""
from datetime import datetime, timedelta, timezone, date
import json
from app.extensions import db
from app.models.tahmin import TahminKaydi
from app.models.makine import Makine


def seed():
    print('[21/22] AI Tahminleri...')

    makineler = Makine.query.filter_by(aktif=True).all()
    bugun = date.today()

    # Arıza Tahminleri
    for m in makineler:
        if m.durum in ['arizali', 'bakimda']:
            continue
        
        # Sadece CNC, Pres ve Lazer için tahmin üret
        if any(kod in m.kod for kod in ['CNC', 'PRS', 'LZR']):
            olasilik = 85.0 if 'CNC-001' in m.kod else 45.0 if 'PRS' in m.kod else 15.0
            tahmini_gun = 2 if olasilik > 80 else 10 if olasilik > 40 else 45
            hedef_tarih = bugun + timedelta(days=tahmini_gun)
            
            t = TahminKaydi(
                tahmin_turu='bakim',
                kaynak_turu='makine',
                kaynak_id=m.id,
                kaynak_adi=m.kod,
                baslik=f"{m.kod} Olası Arıza Riski",
                aciklama="Sensör verilerine göre yakın zamanda arıza bekleniyor.",
                risk_skoru=olasilik,
                tahmin_tarihi=hedef_tarih,
                tahmini_gun=tahmini_gun,
                oneri='Rulman aşınması veya yağlama eksikliği. Planlı bakım öne alınmalı.',
                model_versiyonu='predictive_maintenance_v2',
                meta_veri=json.dumps({
                    'sensorler': ['Titresim_Z_Ekseni', 'Motor_Sicakligi'],
                    'sapma_oranlari': [15.2, 8.4]
                })
            )
            db.session.add(t)
            
    # OEE Tahmini (Fabrika Geneli)
    t_oee = TahminKaydi(
        tahmin_turu='oee',
        kaynak_turu='fabrika',
        kaynak_id=0,
        kaynak_adi='Tüm Tesis',
        baslik='Gelecek Hafta OEE Düşüş Trendi',
        aciklama='Gelecek haftaki planlı bakım duruşları nedeniyle OEE düşüşü bekleniyor.',
        risk_skoru=92.5,
        tahmin_tarihi=bugun + timedelta(days=7),
        tahmini_gun=7,
        oneri='Üretim planlamasını Cuma gününe yoğunlaştırın.',
        model_versiyonu='oee_forecast_lstm',
        meta_veri=json.dumps({
            'beklenen_oee': 82.5,
        })
    )
    db.session.add(t_oee)

    db.session.flush()
    print('  + AI Tahminleri eklendi\n')
