import pytest
import time
from app.models.makine import UretimVerisi, Makine
from datetime import datetime, timedelta
import random

@pytest.fixture
def performans_verisi(session, temel_veriler):
    """Veritabanına performans testi için 5000 mock üretim kaydı ekler."""
    m1_id = temel_veriler['makine_id']
    c1_id = temel_veriler['calisan_id']
    
    # 5000 kayıt ekle
    kayitlar = []
    baslangic = datetime.now() - timedelta(days=365)
    
    for i in range(5000):
        tarih = baslangic + timedelta(hours=i*8)
        kayit = UretimVerisi(
            makine_id=m1_id,
            calisan_id=c1_id,
            tarih=tarih,
            vardiya=random.choice(['sabah', 'aksam', 'gece']),
            planlanan_sure_dk=480,
            gercek_calisma_dk=random.randint(400, 480),
            gercek_uretim=random.randint(800, 1000),
            hatali_uretim=random.randint(0, 50)
        )
        kayit.hesapla_oee(200) # OEE hesapla
        kayitlar.append(kayit)
        
        if len(kayitlar) >= 1000:
            session.bulk_save_objects(kayitlar)
            kayitlar = []
            
    if kayitlar:
        session.bulk_save_objects(kayitlar)
    session.commit()

def test_dashboard_performansi(auth_client_yonetici, performans_verisi):
    """Dashboard'un 5000+ veri ile 1 saniyenin altında yüklenmesi testi."""
    baslama_zamani = time.time()
    
    response = auth_client_yonetici.get('/dashboard/')
    
    bitis_zamani = time.time()
    gecen_sure = bitis_zamani - baslama_zamani
    
    assert response.status_code == 200
    assert gecen_sure < 1.0, f"Performans hatası: Sayfa {gecen_sure:.2f} saniyede yüklendi (Hedef: < 1.0s)"

def test_rapor_excel_performansi(auth_client_yonetici, performans_verisi):
    """Excel çıktısının kabul edilebilir sürede (örn. <2 saniye) üretilmesi."""
    baslama_zamani = time.time()
    
    response = auth_client_yonetici.get('/rapor/excel/uretim')
    
    bitis_zamani = time.time()
    gecen_sure = bitis_zamani - baslama_zamani
    
    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert gecen_sure < 2.0, f"Excel dışa aktarım hızı düşük: {gecen_sure:.2f} sn"
