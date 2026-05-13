"""
FDYS — Bildirim Sistemi Modeli (Faz 3 — Uyumlu)
"""

from datetime import datetime, timezone
from app.extensions import db


class Bildirim(db.Model):
    __tablename__ = 'bildirim'
    __table_args__ = (
        db.Index('ix_bildirim_kullanici_okundu', 'kullanici_id', 'okundu_mu'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='CASCADE'), nullable=False, index=True)
    baslik = db.Column(db.String(200), nullable=False)
    mesaj = db.Column(db.Text, nullable=False)
    seviye = db.Column(db.String(20), nullable=False, default='bilgi')  # bilgi|uyari|kritik|guvenlik
    modul = db.Column(db.String(50), nullable=True)  # Kaynak modül
    url = db.Column(db.String(255), nullable=True)  # İlgili sayfaya link
    okundu_mu = db.Column(db.Boolean, default=False)
    okunma_tarihi = db.Column(db.DateTime, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    kullanici = db.relationship('Kullanici', backref='bildirimler', lazy='joined')

    def okundu_isaretle(self):
        """Bildirimi okundu olarak işaretler."""
        self.okundu_mu = True
        self.okunma_tarihi = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<Bildirim [{self.seviye}] {self.baslik}>'
