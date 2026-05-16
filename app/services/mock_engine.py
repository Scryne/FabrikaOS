import random
import time
import eventlet
from datetime import datetime, timezone, date
from app.extensions import db, socketio
from flask import current_app

class MockDataEngine:
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.sleep_interval = 3  # saniyede bir canli_veri_guncelle eventi
        self.db_update_interval = 15 # her 15 saniyede veritabanına yansıt (DB lock önlemek için)
        self.last_db_update = time.time()
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            # Eventlet arka plan thread'i başlat
            eventlet.spawn(self._run_loop)
            self.app.logger.info("Mock Data Engine (Dinamik Veri Simülatörü) başlatıldı.")

    def stop(self):
        self.is_running = False

    def _run_loop(self):
        """Sürekli çalışan arka plan döngüsü."""
        while self.is_running:
            try:
                self._tick()
            except Exception as e:
                self.app.logger.error(f"Mock Data Engine Hatası: {str(e)}")
            eventlet.sleep(self.sleep_interval)

    def _tick(self):
        """Her tick'te yapılacak işlemler."""
        with self.app.app_context():
            from app.models.makine import Makine, UretimVerisi
            from sqlalchemy import func
            
            # 1. Makine üretim rakamlarını ufak ufak artır
            bugun = date.today()
            makineler = Makine.query.filter_by(aktif=True, durum='aktif').all()
            
            now_ts = time.time()
            update_db = (now_ts - self.last_db_update) >= self.db_update_interval
            
            toplam_canli_uretim = 0
            
            for makine in makineler:
                # Bugünün üretim verisini bul
                uretim = UretimVerisi.query.filter_by(
                    makine_id=makine.id, 
                    tarih=bugun
                ).first()
                
                if uretim:
                    # Rastgele üretim artışı (0 ile 3 adet arası)
                    artis = random.randint(0, 3)
                    uretim.gerceklesen_miktar += artis
                    
                    # OEE'yi hafifçe dalgalandır
                    if uretim.planlanan_miktar > 0:
                        performans = min(100.0, (uretim.gerceklesen_miktar / uretim.planlanan_miktar) * 100)
                        uretim.performans_orani = performans
                        # Kullanılabilirlik ve Kaliteyi varsayılan/rastgele tutarak OEE hesapla
                        uretim.oee_orani = (uretim.kullanilabilirlik_orani * performans * uretim.kalite_orani) / 10000.0
                    
                    toplam_canli_uretim += uretim.gerceklesen_miktar
                else:
                    # Yoksa bir tane oluşturalım ki simülasyon başlasın
                    # Basitçe geçiyoruz, DB seed edilmiş olmalı
                    pass
            
            if update_db and makineler:
                db.session.commit()
                self.last_db_update = now_ts
                
            # 2. SocketIO ile tüm client'lara canlı sayaç bilgisini gönder
            # Toplam günlük üretimi al (tüm makineler için)
            toplam_bugun = db.session.query(func.sum(UretimVerisi.gerceklesen_miktar)).filter(
                UretimVerisi.tarih == bugun
            ).scalar() or 0
            
            ort_oee = db.session.query(func.avg(UretimVerisi.oee_orani)).filter(
                UretimVerisi.tarih == bugun
            ).scalar() or 0
            
            socketio.emit('canli_veri_guncelle', {
                'bugun_uretim': int(toplam_bugun),
                'ort_oee': round(ort_oee, 1)
            })
            
            # 3. Rastgele olaylar (Düşük olasılıkla arıza, bildirim)
            self._trigger_random_events()
            
    def _trigger_random_events(self):
        """Çok düşük ihtimalle rastgele olaylar fırlatarak demoyu canlı tutar."""
        # %1 ihtimalle bir bildirim düşür
        if random.random() < 0.01:
            from app.models.makine import Makine
            from sqlalchemy.sql.expression import func
            
            makine = Makine.query.filter_by(aktif=True).order_by(func.random()).first()
            makine_kodu = makine.kod if makine else 'SİSTEM'
            
            stok_adi = 'Alüminyum Kütük'
            
            olaylar = [
                {'baslik': 'Sıcaklık Uyarısı', 'mesaj': f'{makine_kodu} Motor sıcaklığı limit değerlere yaklaşıyor.', 'seviye': 'uyari', 'modul': 'makine'},
                {'baslik': 'Stok Kritik Seviye', 'mesaj': f'{stok_adi} stoğu minimum seviyenin altına düştü!', 'seviye': 'kritik', 'modul': 'stok'},
                {'baslik': 'Kalite Anormalliği', 'mesaj': f'{makine_kodu} istasyonunda üst üste 3 hatalı ürün tespit edildi.', 'seviye': 'uyari', 'modul': 'kalite'}
            ]
            olay = random.choice(olaylar)
            
            from app.services.bildirim_motoru import bildirim_gonder
            bildirim_gonder(
                baslik=olay['baslik'],
                mesaj=olay['mesaj'],
                seviye=olay['seviye'],
                hedef_roller=['yonetici', 'operator', 'teknisyen'],
                modul=olay['modul'],
                url='#'
            )
