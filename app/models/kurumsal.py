"""
FDYS — Kurumsal Ayarlar Modeli

Sistemin müşteri tarafından özelleştirilebilmesi (White-Labeling) için
gerekli şirket adı, logo ve tema renklerini tutan singleton model.
"""

from app.extensions import db

class KurumsalAyarlar(db.Model):
    """
    Sistemin marka ve tema ayarlarını tutan model.
    Veritabanında her zaman tek bir kaydı olmalıdır (Singleton).
    """
    __tablename__ = 'kurumsal_ayarlar'

    id = db.Column(db.Integer, primary_key=True)
    sirket_adi = db.Column(db.String(100), default='FabrikaOS')
    logo_path = db.Column(db.String(255), nullable=True) # static/img/custom_logo.png
    ana_renk = db.Column(db.String(20), nullable=True) # #0d6efd
    ikincil_renk = db.Column(db.String(20), nullable=True)
    
    @classmethod
    def ayarlari_getir(cls):
        """Sistemdeki tek ayar kaydını getirir veya oluşturur."""
        ayarlar = cls.query.first()
        if not ayarlar:
            ayarlar = cls(
                sirket_adi='FabrikaOS',
                ana_renk='#0d6efd',
            )
            db.session.add(ayarlar)
            db.session.commit()
        return ayarlar

    def __repr__(self):
        return f'<KurumsalAyarlar {self.sirket_adi}>'
