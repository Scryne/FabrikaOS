"""
FDYS — E-posta Ayarları Modeli
Faz 5 — E-posta Bildirim Desteği

Admin panelinden yapılandırılabilir SMTP ayarlarını saklar.
Singleton pattern: Veritabanında tek satır olarak tutulur.
"""

from datetime import datetime, timezone
from app.extensions import db


class EpostaAyarlari(db.Model):
    """
    SMTP ve e-posta bildirim ayarları.
    Singleton pattern — her zaman id=1 olan tek satır kullanılır.
    """
    __tablename__ = 'eposta_ayarlari'

    id = db.Column(db.Integer, primary_key=True, default=1)

    # SMTP Sunucu Ayarları
    smtp_host = db.Column(db.String(255), nullable=True, default='')
    smtp_port = db.Column(db.Integer, nullable=True, default=587)
    smtp_kullanici = db.Column(db.String(255), nullable=True, default='')
    smtp_sifre = db.Column(db.String(500), nullable=True, default='')  # Production'da encrypt edilmeli
    ssl_aktif = db.Column(db.Boolean, default=False)
    tls_aktif = db.Column(db.Boolean, default=True)

    # Gönderici Bilgileri
    gonderici_ad = db.Column(db.String(100), nullable=True, default='FDYS Bildirim Sistemi')
    gonderici_eposta = db.Column(db.String(255), nullable=True, default='')

    # Özet Rapor Ayarları
    gunluk_ozet_aktif = db.Column(db.Boolean, default=False)
    haftalik_ozet_aktif = db.Column(db.Boolean, default=False)
    ozet_alici_epostalar = db.Column(db.JSON, default=list)  # ["admin@example.com", ...]

    # Bildirim Tetikleme Ayarları
    kritik_uyari_aktif = db.Column(db.Boolean, default=True)    # Kritik bildirimlerde e-posta gönder
    ariza_uyari_aktif = db.Column(db.Boolean, default=True)     # Arıza bildirimlerinde e-posta gönder
    stok_uyari_aktif = db.Column(db.Boolean, default=False)     # Stok kritik seviyede e-posta gönder

    # Durum
    aktif = db.Column(db.Boolean, default=False)  # E-posta sistemi aktif mi
    test_basarili = db.Column(db.Boolean, default=False)
    son_test_tarihi = db.Column(db.DateTime, nullable=True)
    son_gonderim_tarihi = db.Column(db.DateTime, nullable=True)

    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    @classmethod
    def ayarlari_getir(cls):
        """Singleton instance'ı döner, yoksa oluşturur."""
        ayarlar = cls.query.get(1)
        if not ayarlar:
            ayarlar = cls(id=1)
            db.session.add(ayarlar)
            db.session.commit()
        return ayarlar

    @property
    def yapilandirildi_mi(self):
        """SMTP ayarlarının doldurulup doldurulmadığını kontrol eder."""
        return bool(self.smtp_host and self.smtp_port and self.gonderici_eposta)

    def __repr__(self):
        return f'<EpostaAyarlari aktif={self.aktif} host={self.smtp_host}>'
