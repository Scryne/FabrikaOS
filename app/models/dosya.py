"""
FDYS — Dosya Eki Modeli
Faz 5 — Dosya Yönetimi

Her kayda (makine, arıza, bakım, kalite, isg, iş emri vb.)
dosya/fotoğraf ekleme desteği sağlar.
Polimorfik yapıda: kaynak_tablo + kaynak_id ile ilişkilendirilir.
"""

from datetime import datetime, timezone
from app.extensions import db


class DosyaEki(db.Model):
    """
    Polimorfik dosya eki modeli.

    kaynak_tablo: İlişkili tablonun adı (makine, ariza_kaydi, bakim_kaydi vb.)
    kaynak_id: İlişkili kaydın ID'si
    """
    __tablename__ = 'dosya_eki'
    __table_args__ = (
        db.Index('ix_dosya_kaynak', 'kaynak_tablo', 'kaynak_id'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dosya_adi = db.Column(db.String(255), nullable=False)       # Sunucuda saklanan dosya adı (UUID prefix)
    orijinal_adi = db.Column(db.String(255), nullable=False)    # Kullanıcının yüklediği orijinal dosya adı
    dosya_tipi = db.Column(db.String(20), nullable=False)       # image, pdf, document, spreadsheet
    mime_type = db.Column(db.String(100), nullable=True)
    dosya_boyutu = db.Column(db.Integer, nullable=True)         # Byte cinsinden
    kaynak_tablo = db.Column(db.String(50), nullable=False)     # makine, ariza_kaydi, bakim_kaydi, is_emri vb.
    kaynak_id = db.Column(db.Integer, nullable=False)
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    aciklama = db.Column(db.String(500), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # İlişki
    yukleyen = db.relationship('Kullanici', backref='yuklenen_dosyalar', lazy='joined')

    # Desteklenen dosya türleri ve uzantı eşlemesi
    DOSYA_TIPI_ESLESME = {
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image',
        'pdf': 'pdf',
        'doc': 'document', 'docx': 'document',
        'xls': 'spreadsheet', 'xlsx': 'spreadsheet', 'csv': 'spreadsheet',
    }

    DOSYA_TIPI_IKON = {
        'image': 'bi-file-earmark-image',
        'pdf': 'bi-file-earmark-pdf',
        'document': 'bi-file-earmark-word',
        'spreadsheet': 'bi-file-earmark-spreadsheet',
    }

    @classmethod
    def dosya_tipi_bul(cls, dosya_adi):
        """Dosya uzantısından tip belirler."""
        uzanti = dosya_adi.rsplit('.', 1)[-1].lower() if '.' in dosya_adi else ''
        return cls.DOSYA_TIPI_ESLESME.get(uzanti, 'document')

    @property
    def ikon_sinifi(self):
        """Bootstrap icon CSS sınıfı."""
        return self.DOSYA_TIPI_IKON.get(self.dosya_tipi, 'bi-file-earmark')

    @property
    def resim_mi(self):
        """Dosya bir resim mi?"""
        return self.dosya_tipi == 'image'

    @property
    def boyut_formatli(self):
        """Dosya boyutunu okunabilir formatta döner (KB, MB)."""
        if not self.dosya_boyutu:
            return '—'
        if self.dosya_boyutu < 1024:
            return f'{self.dosya_boyutu} B'
        elif self.dosya_boyutu < 1024 * 1024:
            return f'{self.dosya_boyutu / 1024:.1f} KB'
        else:
            return f'{self.dosya_boyutu / (1024 * 1024):.1f} MB'

    def __repr__(self):
        return f'<DosyaEki {self.kaynak_tablo}#{self.kaynak_id} — {self.orijinal_adi}>'
