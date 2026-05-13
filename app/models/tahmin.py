"""
FDYS — AI Tahminleme Motoru Modeli
Kategori 1 — Yapay Zeka Destekli Tahminleme

Model:
    - TahminKaydi: Tüm AI tahminlerinin merkezi kaydı
      (kestirimci bakım, OEE tahmini, stok tükenme, anomali)
"""

from datetime import datetime, timezone
from app.extensions import db
import json


class TahminKaydi(db.Model):
    __tablename__ = 'tahmin_kaydi'
    __table_args__ = (
        db.Index('ix_tahmin_tur_kaynak', 'tahmin_turu', 'kaynak_turu', 'kaynak_id'),
        db.Index('ix_tahmin_risk', 'risk_skoru'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Tahmin türü: bakim, oee, stok, anomali
    tahmin_turu = db.Column(db.String(50), nullable=False, index=True)

    # Kaynak bilgisi
    kaynak_turu = db.Column(db.String(50), nullable=False)  # makine, malzeme, enerji, kalite
    kaynak_id = db.Column(db.Integer, nullable=False)
    kaynak_adi = db.Column(db.String(200), nullable=True)  # Kolay referans için

    # Tahmin içeriği
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)
    risk_skoru = db.Column(db.Numeric(5, 2), nullable=False, default=0)  # 0-100

    # Tahmin detayları
    tahmin_tarihi = db.Column(db.Date, nullable=True)  # Olayın tahmini gerçekleşme tarihi
    tahmini_gun = db.Column(db.Integer, nullable=True)  # Kaç gün sonra
    oneri = db.Column(db.Text, nullable=True)  # AI önerisi

    # Doğrulama
    gerceklesti_mi = db.Column(db.Boolean, nullable=True, default=None)
    model_versiyonu = db.Column(db.String(20), default='v1.0')

    # Ek veri (JSON)
    meta_veri = db.Column(db.Text, nullable=True)

    # Zaman damgaları
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def risk_seviyesi(self):
        """Risk skoruna göre seviye döner."""
        skor = float(self.risk_skoru) if self.risk_skoru else 0
        if skor >= 75:
            return 'kritik'
        elif skor >= 50:
            return 'yuksek'
        elif skor >= 25:
            return 'orta'
        return 'dusuk'

    @property
    def risk_renk(self):
        """Risk seviyesine göre CSS renk sınıfı döner."""
        seviye = self.risk_seviyesi
        return {
            'kritik': 'danger',
            'yuksek': 'warning',
            'orta': 'info',
            'dusuk': 'success'
        }.get(seviye, 'secondary')

    @property
    def meta(self):
        """meta_veri JSON stringini dict olarak döner."""
        if self.meta_veri:
            try:
                return json.loads(self.meta_veri)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @meta.setter
    def meta(self, value):
        """Dict'i JSON string olarak saklar."""
        self.meta_veri = json.dumps(value, ensure_ascii=False) if value else None

    def __repr__(self):
        return f'<TahminKaydi [{self.tahmin_turu}] {self.baslik} — Risk: {self.risk_skoru}>'
