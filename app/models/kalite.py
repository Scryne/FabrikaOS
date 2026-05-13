"""
FDYS — Kalite Kontrol Modeli
Faz 4 — Kurumsal Seviye

Modeller:
    - HataKaydi: Üretim hata kayıtları, hurda/fire oranları, parti/lot takibi
    - DuzelticiFaaliyet: 8D / CAPA süreç yönetimi detaylı takip
"""

from datetime import datetime, timezone
from app.extensions import db


class HataKaydi(db.Model):
    __tablename__ = 'hata_kaydi'
    __table_args__ = (
        db.Index('ix_hata_makine_tarih', 'makine_id', 'tarih'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id', ondelete='SET NULL'), nullable=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='SET NULL'), nullable=True)
    urun_adi = db.Column(db.String(150), nullable=False)
    parti_no = db.Column(db.String(50), nullable=True, index=True)
    hat = db.Column(db.String(50), nullable=True)
    hata_turu = db.Column(db.String(100), nullable=False)
    hata_kategorisi = db.Column(db.String(50), nullable=False)  # olcusel|yuzey|montaj|malzeme|diger
    hata_kaynagi = db.Column(db.String(50), nullable=True)  # iscilik|makine|malzeme|metot
    adet = db.Column(db.Integer, default=1)
    fire_orani = db.Column(db.Numeric(5, 2), nullable=True)  # Yüzdelik fire
    vardiya = db.Column(db.String(20), nullable=True)
    aciklama = db.Column(db.Text, nullable=True)
    aksiyon_karari = db.Column(db.String(50), nullable=True)  # hurda|tamir|sartli_kabul
    tarih = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    kaydeden_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    makine = db.relationship('Makine', backref='hata_kayitlari', lazy='joined')
    calisan = db.relationship('Calisan', backref='hata_kayitlari', lazy='joined')
    kaydeden = db.relationship('Kullanici', backref='kaydettigi_hatalar', lazy='joined')
    duzelticiler = db.relationship('DuzelticiFaaliyet', backref='hata_kaydi', lazy='dynamic',
                                   cascade='all, delete-orphan', passive_deletes=True)

    @property
    def duzeltici_faaliyet_durumu(self):
        """Düzeltici faaliyet başlatıldı mı kontrol eder."""
        return self.duzelticiler.count() > 0

    def __repr__(self):
        return f'<HataKaydi {self.hata_turu} — {self.adet} adet>'


class DuzelticiFaaliyet(db.Model):
    __tablename__ = 'duzeltici_faaliyet'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    capa_no = db.Column(db.String(50), unique=True, nullable=True, index=True)
    hata_kaydi_id = db.Column(db.Integer, db.ForeignKey('hata_kaydi.id', ondelete='CASCADE'), nullable=False)
    ekip_lideri_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    kok_neden = db.Column(db.Text, nullable=False)
    neden_kategorisi = db.Column(db.String(50), nullable=True)  # insan|makine|malzeme|metot|cevre
    faaliyet = db.Column(db.Text, nullable=False)
    gecici_onlem = db.Column(db.Text, nullable=True)
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    hedef_tarih = db.Column(db.Date, nullable=True)
    tamamlanma_tarihi = db.Column(db.Date, nullable=True)
    durum = db.Column(db.String(20), default='acik')  # acik|devam|dogrulama|kapandi|iptal
    dogrulama_notu = db.Column(db.Text, nullable=True)
    dogrulayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sorumlu = db.relationship('Kullanici', foreign_keys=[sorumlu_id], backref='sorumlu_oldugu_df', lazy='joined')
    ekip_lideri = db.relationship('Kullanici', foreign_keys=[ekip_lideri_id], backref='lider_oldugu_df', lazy='joined')
    dogrulayan = db.relationship('Kullanici', foreign_keys=[dogrulayan_id], backref='dogruladigi_df', lazy='joined')

    @property
    def gecikme_gun(self):
        """Hedef tarihten kaç gün geçtiğini hesaplar."""
        if self.hedef_tarih and self.durum not in ('dogrulama', 'kapandi', 'iptal'):
            bugun = datetime.now(timezone.utc).date()
            if bugun > self.hedef_tarih:
                return (bugun - self.hedef_tarih).days
        return 0

    def __repr__(self):
        return f'<DuzelticiFaaliyet {self.capa_no or self.id} - {self.durum}>'
