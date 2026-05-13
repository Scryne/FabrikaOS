"""
FDYS — İSG (İş Sağlığı ve Güvenliği) Modeli
Faz 4 — Kurumsal Seviye
"""

from datetime import datetime, timezone
from app.extensions import db


class IsKazasi(db.Model):
    __tablename__ = 'is_kazasi'
    __table_args__ = (
        db.Index('ix_kaza_calisan_tarih', 'calisan_id', 'tarih'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    olay_no = db.Column(db.String(50), unique=True, nullable=True, index=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='RESTRICT'), nullable=False)
    tarih = db.Column(db.DateTime, nullable=False, index=True)
    vardiya = db.Column(db.String(20), nullable=True)
    yer = db.Column(db.String(100), nullable=False)
    yaralanma_tipi = db.Column(db.String(100), nullable=False)
    uzuv = db.Column(db.String(100), nullable=True)  # Etkilenen uzuv
    siddet = db.Column(db.String(20), nullable=False)  # hafif|orta|agir|olumcul
    kaza_sekli = db.Column(db.String(100), nullable=True)  # dusme|sikisma|kesilme vb.
    kok_neden = db.Column(db.Text, nullable=True)
    aciklama = db.Column(db.Text, nullable=False)
    duzeltici_faaliyet = db.Column(db.Text, nullable=True)
    kayip_gun = db.Column(db.Integer, default=0)
    ramak_kala = db.Column(db.Boolean, default=False)
    durum = db.Column(db.String(20), default='acik')  # acik|arastiriliyor|kapandi
    bildiren_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    calisan = db.relationship('Calisan', backref='kaza_kayitlari', lazy='joined')
    bildiren = db.relationship('Kullanici', backref='bildirilen_kazalar', lazy='joined')

    def __repr__(self):
        return f'<IsKazasi {self.olay_no or self.id} — {self.siddet}>'


class RiskDegerlendirme(db.Model):
    __tablename__ = 'risk_degerlendirme'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bolum = db.Column(db.String(100), nullable=False)
    faaliyet = db.Column(db.String(150), nullable=True)  # Hangi iş yaparken
    tehlike = db.Column(db.Text, nullable=False)
    risk = db.Column(db.Text, nullable=True)  # Tehlikenin yaratacağı risk
    olasilik = db.Column(db.Integer, nullable=False)  # 1-5 (5x5 matris için)
    siddet = db.Column(db.Integer, nullable=False)  # 1-5
    mevcut_onlem = db.Column(db.Text, nullable=True)
    risk_puani = db.Column(db.Integer, nullable=True)  # olasilik × siddet
    risk_seviyesi = db.Column(db.String(20), nullable=True)  # dusuk|orta|yuksek|kritik
    ek_onlem = db.Column(db.Text, nullable=True)
    sorumlu = db.Column(db.String(100), nullable=True)
    hedef_tarih = db.Column(db.Date, nullable=True)
    durum = db.Column(db.String(20), default='acik')  # acik|devam|kapandi
    gozden_gecirme_tarihi = db.Column(db.Date, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def hesapla_risk(self):
        """Risk puanı = Olasılık × Şiddet (5x5 Matris)."""
        self.risk_puani = self.olasilik * self.siddet
        if self.risk_puani <= 6:
            self.risk_seviyesi = 'dusuk'
        elif self.risk_puani <= 12:
            self.risk_seviyesi = 'orta'
        elif self.risk_puani <= 19:
            self.risk_seviyesi = 'yuksek'
        else:
            self.risk_seviyesi = 'kritik'
        return self.risk_puani

    def __repr__(self):
        return f'<RiskDegerlendirme {self.bolum} — {self.risk_seviyesi}>'


class IsgEgitimi(db.Model):
    __tablename__ = 'isg_egitimi'
    __table_args__ = (
        db.Index('ix_egitim_calisan_tarih', 'calisan_id', 'egitim_tarihi'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False)
    egitim_kategorisi = db.Column(db.String(50), nullable=True)  # temel_isg|ilkyardim|yangin|mesleki
    egitim_adi = db.Column(db.String(200), nullable=False)
    egitim_suresi = db.Column(db.Numeric(4, 1), nullable=True)  # Saat cinsinden
    egitim_tarihi = db.Column(db.Date, nullable=False)
    gecerlilik_bitis = db.Column(db.Date, nullable=True)
    sertifika_no = db.Column(db.String(50), nullable=True)
    egitmen = db.Column(db.String(100), nullable=True)
    durum = db.Column(db.String(20), default='gecerli')  # gecerli|suresi_doldu|iptal
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    calisan = db.relationship('Calisan', backref='isg_egitimleri', lazy='joined')

    def __repr__(self):
        return f'<IsgEgitimi {self.egitim_adi}>'
