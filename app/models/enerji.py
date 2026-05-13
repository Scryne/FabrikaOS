"""
FDYS — Enerji ve Maliyet Takip Modeli
Faz 4 — Kurumsal Seviye

Modeller:
    - EnerjiTuketimi: Detaylı enerji tüketim analizi, karbon ayak izi tahmini
"""

from datetime import datetime, timezone
from app.extensions import db


class EnerjiTuketimi(db.Model):
    __tablename__ = 'enerji_tuketimi'
    __table_args__ = (
        db.Index('ix_enerji_tur_donem', 'enerji_turu', 'donem_baslangic'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id', ondelete='SET NULL'), nullable=True)
    departman = db.Column(db.String(100), nullable=True)  # Tüketimin yapıldığı bölüm
    enerji_turu = db.Column(db.String(20), nullable=False)  # elektrik|dogalgaz|su|buhar|basincli_hava
    miktar = db.Column(db.Numeric(12, 2), nullable=False)
    birim = db.Column(db.String(10), nullable=False)  # kWh|m3|litre|ton
    birim_fiyat = db.Column(db.Numeric(10, 4), nullable=True)
    toplam_maliyet = db.Column(db.Numeric(12, 2), nullable=True)
    karbon_salinimi = db.Column(db.Numeric(10, 2), nullable=True)  # kg CO2 eşdeğeri
    donem_baslangic = db.Column(db.Date, nullable=False)
    donem_bitis = db.Column(db.Date, nullable=False)
    hedef_miktar = db.Column(db.Numeric(12, 2), nullable=True)
    fatura_no = db.Column(db.String(50), nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    kaydeden_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    makine = db.relationship('Makine', backref='enerji_kayitlari', lazy='joined')
    kaydeden = db.relationship('Kullanici', backref='enerji_kayitlari', lazy='joined')

    def hesapla_maliyet_ve_karbon(self):
        """Toplam maliyeti ve tahmini karbon salınımını hesaplar."""
        if self.birim_fiyat and self.miktar:
            self.toplam_maliyet = float(self.birim_fiyat) * float(self.miktar)

        # Basit karbon salınımı katsayıları (temsili)
        katsayilar = {
            'elektrik': 0.453,  # kg CO2 / kWh
            'dogalgaz': 2.02,   # kg CO2 / m3
            'su': 0.344,        # kg CO2 / m3
            'buhar': 0.2,       # kg CO2 / kg
            'basincli_hava': 0.1  # kg CO2 / m3
        }

        if self.enerji_turu in katsayilar and self.miktar:
            self.karbon_salinimi = float(self.miktar) * katsayilar[self.enerji_turu]

        return self.toplam_maliyet

    @property
    def birim_goster(self):
        """Enerji türüne göre birim döner."""
        birimler = {'elektrik': 'kWh', 'dogalgaz': 'm³', 'su': 'm³', 'buhar': 'Ton', 'basincli_hava': 'm³'}
        return birimler.get(self.enerji_turu, self.birim)

    @property
    def hedef_sapma_yuzde(self):
        """Hedef miktardan sapma yüzdesini hesaplar."""
        if self.hedef_miktar and float(self.hedef_miktar) > 0:
            sapma = ((float(self.miktar) - float(self.hedef_miktar)) / float(self.hedef_miktar)) * 100
            return round(sapma, 1)
        return None

    def __repr__(self):
        return f'<EnerjiTuketimi {self.enerji_turu} — {self.miktar} {self.birim}>'
