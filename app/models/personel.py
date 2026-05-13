"""
FDYS — Personel Yönetimi Modeli

Çalışan, vardiya planı ve izin talebi tablolarını içerir.
Yetkinlik matrisi JSON formatında saklanır.
"""

from datetime import datetime, timezone
from app.extensions import db


class Calisan(db.Model):
    """
    Çalışan profil kartı.
    Sicil no, departman, pozisyon, makine yetkinlikleri ve iletişim bilgilerini içerir.
    """
    __tablename__ = 'calisan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True, unique=True)
    sicil_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    departman = db.Column(db.String(100), nullable=False)
    pozisyon = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20), nullable=True)
    eposta = db.Column(db.String(120), nullable=True)
    ise_baslama = db.Column(db.Date, nullable=False)
    ucret = db.Column(db.Numeric(10, 2), nullable=True)  # Opsiyonel maaş kaydı
    beceri_json = db.Column(db.JSON, default=list)  # Makine yetkinlik listesi [{makine_id, puan}]
    fotograf = db.Column(db.String(255), nullable=True)  # Profil fotoğrafı dosya yolu
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    vardiya_planlari = db.relationship('VardiyaPlani', backref='calisan', lazy='dynamic',
                                       cascade='all, delete-orphan', passive_deletes=True)
    izin_talepleri = db.relationship('IzinTalebi', backref='calisan', lazy='dynamic',
                                     cascade='all, delete-orphan', passive_deletes=True)

    def yetkinlik_puani(self, makine_id):
        """Belirtilen makine için çalışanın yetkinlik puanını döner (1-5)."""
        if not self.beceri_json:
            return 0
        for beceri in self.beceri_json:
            if beceri.get('makine_id') == makine_id:
                return beceri.get('puan', 0)
        return 0

    def __repr__(self):
        return f'<Calisan {self.sicil_no} — {self.ad_soyad}>'


class VardiyaPlani(db.Model):
    """
    Haftalık vardiya çizelgesi.
    Her çalışan için günlük vardiya ataması yapılır.
    """
    __tablename__ = 'vardiya_plani'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    tarih = db.Column(db.Date, nullable=False, index=True)
    vardiya_turu = db.Column(db.String(20), nullable=False)  # sabah|ogleden_sonra|gece|off
    baslangic = db.Column(db.Time, nullable=False)
    bitis = db.Column(db.Time, nullable=False)
    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Bileşik unique constraint: aynı çalışan, aynı gün, aynı vardiya
    __table_args__ = (
        db.UniqueConstraint('calisan_id', 'tarih', 'vardiya_turu',
                           name='uq_vardiya_calisan_tarih_tur'),
    )

    def __repr__(self):
        return f'<VardiyaPlani {self.tarih} — {self.vardiya_turu}>'


class IzinTalebi(db.Model):
    """
    İzin talebi ve onay akışı.
    Çalışan talepte bulunur, yönetici onaylar veya reddeder.
    """
    __tablename__ = 'izin_talebi'
    __table_args__ = (
        db.Index('ix_izin_calisan_durum', 'calisan_id', 'durum'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    baslangic_tarihi = db.Column(db.Date, nullable=False)
    bitis_tarihi = db.Column(db.Date, nullable=False)
    tur = db.Column(db.String(20), nullable=False)  # yillik|mazeret|saglik|ucretsiz
    aciklama = db.Column(db.Text, nullable=True)
    durum = db.Column(db.String(20), default='bekliyor')  # bekliyor|onaylandi|reddedildi
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onay_tarihi = db.Column(db.DateTime, nullable=True)
    red_nedeni = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişki
    onaylayan = db.relationship('Kullanici', foreign_keys=[onaylayan_id],
                                backref='onaylanan_izinler', lazy='joined')

    def __repr__(self):
        return f'<IzinTalebi {self.tur} — {self.durum}>'
