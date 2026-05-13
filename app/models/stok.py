"""
FDYS — Stok ve Malzeme Yönetimi Modeli
"""

from datetime import datetime, timezone
from app.extensions import db


class Malzeme(db.Model):
    __tablename__ = 'malzeme'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad = db.Column(db.String(150), nullable=False)
    kod = db.Column(db.String(50), unique=True, nullable=False, index=True)
    birim = db.Column(db.String(20), nullable=False)  # adet|kg|litre|metre
    kategori = db.Column(db.String(100), nullable=True)
    lokasyon = db.Column(db.String(100), nullable=True)  # raf/dolap konumu
    birim_fiyat = db.Column(db.Numeric(10, 2), nullable=True)
    mevcut_miktar = db.Column(db.Numeric(12, 2), default=0)
    minimum_stok = db.Column(db.Numeric(12, 2), default=0)  # Uyarı eşiği
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    hareketler = db.relationship('StokHareketi', backref='malzeme', lazy='dynamic',
                                 cascade='all, delete-orphan', passive_deletes=True)

    def stok_kritik_mi(self):
        """Mevcut stok minimum eşiğin altında mı?"""
        return self.mevcut_miktar <= self.minimum_stok

    def __repr__(self):
        return f'<Malzeme {self.kod} — {self.ad}>'


class StokHareketi(db.Model):
    __tablename__ = 'stok_hareketi'
    __table_args__ = (
        db.Index('ix_stok_hareket_malzeme_tarih', 'malzeme_id', 'tarih'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    malzeme_id = db.Column(db.Integer, db.ForeignKey('malzeme.id', ondelete='CASCADE'), nullable=False, index=True)
    hareket_turu = db.Column(db.String(10), nullable=False)  # giris|cikis
    miktar = db.Column(db.Numeric(12, 2), nullable=False)
    birim_fiyat = db.Column(db.Numeric(10, 2), nullable=True)
    fatura_no = db.Column(db.String(50), nullable=True)
    neden = db.Column(db.String(200), nullable=True)
    islem_yapan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    tarih = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    islem_yapan = db.relationship('Kullanici', backref='stok_islemleri', lazy='joined')

    def __repr__(self):
        return f'<StokHareketi {self.hareket_turu} — {self.miktar}>'


class Tedarikci(db.Model):
    __tablename__ = 'tedarikci'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad = db.Column(db.String(150), nullable=False)
    yetkili_kisi = db.Column(db.String(100), nullable=True)
    telefon = db.Column(db.String(20), nullable=True)
    eposta = db.Column(db.String(120), nullable=True)
    adres = db.Column(db.Text, nullable=True)
    ortalama_teslimat_gun = db.Column(db.Integer, nullable=True)
    performans_puani = db.Column(db.Numeric(3, 1), nullable=True)  # 1-5
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    malzemeler = db.relationship('Malzeme', backref='tedarikci', lazy='dynamic')

    def __repr__(self):
        return f'<Tedarikci {self.ad}>'
