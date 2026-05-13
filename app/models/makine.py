"""
FDYS — Makine ve Üretim Takip Modeli
Faz 3 — Endüstriyel Seviye

Modeller:
    - Makine: Ekipman künyesi, OEE hedefleri, bakım periyodları
    - UretimVerisi: Vardiya bazlı üretim verileri ve OEE hesaplama
    - ArizaKaydi: Arıza bildirimi, müdahale takibi
    - BakimKaydi: Periyodik/korektif bakım kayıtları
    - DurusKaydi: Altı Büyük Kayıp bazlı duruş kategorileri
"""

from datetime import datetime, timedelta, timezone
from app.extensions import db


class Makine(db.Model):
    __tablename__ = 'makine'
    __table_args__ = (
        db.Index('ix_makine_aktif_durum', 'aktif', 'durum'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(50), unique=True, nullable=False, index=True)
    model = db.Column(db.String(100), nullable=True)
    marka = db.Column(db.String(100), nullable=True)
    teorik_kapasite = db.Column(db.Integer, nullable=False)
    hedef_oee = db.Column(db.Numeric(5, 2), default=85.00)
    satin_alma_tarihi = db.Column(db.Date, nullable=False)
    garantisi_bitis = db.Column(db.Date, nullable=True)
    son_bakim_tarihi = db.Column(db.Date, nullable=True)
    periyodik_bakim_gun = db.Column(db.Integer, default=90)
    lokasyon = db.Column(db.String(100), nullable=True)
    durum = db.Column(db.String(20), default='aktif')
    # Fabrika haritası konumlandırma alanları
    konum_x = db.Column(db.Float, nullable=True, default=None)
    konum_y = db.Column(db.Float, nullable=True, default=None)
    konum_w = db.Column(db.Float, nullable=True, default=80)
    konum_h = db.Column(db.Float, nullable=True, default=60)
    # Maliyet merkezi analizi alanları
    satin_alma_fiyati = db.Column(db.Numeric(14, 2), nullable=True)
    birim_satis_fiyati = db.Column(db.Numeric(10, 2), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    uretim_verileri = db.relationship('UretimVerisi', backref='makine', lazy='dynamic',
                                      cascade='all, delete-orphan', passive_deletes=True)
    ariza_kayitlari = db.relationship('ArizaKaydi', backref='makine', lazy='dynamic',
                                      cascade='all, delete-orphan', passive_deletes=True)
    bakim_kayitlari = db.relationship('BakimKaydi', backref='makine', lazy='dynamic',
                                      cascade='all, delete-orphan', passive_deletes=True)
    durus_kayitlari = db.relationship('DurusKaydi', backref='makine', lazy='dynamic',
                                      cascade='all, delete-orphan', passive_deletes=True)

    @property
    def garanti_durumu(self):
        """Garanti süresinin aktif olup olmadığını kontrol eder."""
        if self.garantisi_bitis:
            return self.garantisi_bitis >= datetime.now(timezone.utc).date()
        return False

    @property
    def sonraki_bakim_tarihi(self):
        """Bir sonraki bakım tarihini hesaplar."""
        if self.son_bakim_tarihi and self.periyodik_bakim_gun:
            return self.son_bakim_tarihi + timedelta(days=self.periyodik_bakim_gun)
        return None

    @property
    def bakim_gecikti_mi(self):
        """Bakım tarihi geçtiyse True döner."""
        sonraki = self.sonraki_bakim_tarihi
        if sonraki:
            return sonraki < datetime.now(timezone.utc).date()
        return False

    @property
    def toplam_bakim_maliyeti(self):
        """Toplam bakım maliyetini hesaplar."""
        from sqlalchemy import func
        sonuc = db.session.query(func.sum(BakimKaydi.maliyet))\
            .filter(BakimKaydi.makine_id == self.id).scalar()
        return float(sonuc) if sonuc else 0

    def __repr__(self):
        return f'<Makine {self.kod} — {self.ad}>'


class UretimVerisi(db.Model):
    __tablename__ = 'uretim_verisi'
    __table_args__ = (
        db.Index('ix_uretim_makine_tarih', 'makine_id', 'tarih'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id', ondelete='CASCADE'), nullable=False, index=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='SET NULL'), nullable=True)
    vardiya = db.Column(db.String(20), nullable=False)
    tarih = db.Column(db.Date, nullable=False, index=True)
    planlanan_sure_dk = db.Column(db.Integer, nullable=False)
    gercek_calisma_dk = db.Column(db.Integer, nullable=False)
    gercek_uretim = db.Column(db.Integer, nullable=False)
    hatali_uretim = db.Column(db.Integer, default=0)
    oee_yuzde = db.Column(db.Numeric(5, 2), nullable=True)
    kullanilabilirlik = db.Column(db.Numeric(5, 2), nullable=True)
    performans = db.Column(db.Numeric(5, 2), nullable=True)
    kalite = db.Column(db.Numeric(5, 2), nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    calisan = db.relationship('Calisan', backref='uretim_verileri', lazy='joined')

    def hesapla_oee(self, teorik_kapasite):
        """OEE = Kullanılabilirlik × Performans × Kalite"""
        if self.planlanan_sure_dk == 0 or teorik_kapasite == 0:
            return 0
        k = self.gercek_calisma_dk / self.planlanan_sure_dk
        p = self.gercek_uretim / (teorik_kapasite * (self.gercek_calisma_dk / 60)) if self.gercek_calisma_dk > 0 else 0
        q = (self.gercek_uretim - self.hatali_uretim) / self.gercek_uretim if self.gercek_uretim > 0 else 0
        oee = k * p * q * 100

        self.kullanilabilirlik = round(min(k * 100, 100), 2)
        self.performans = round(min(p * 100, 100), 2)
        self.kalite = round(min(q * 100, 100), 2)
        self.oee_yuzde = round(min(oee, 100), 2)
        return self.oee_yuzde

    @property
    def iyi_uretim(self):
        """Hatasız üretim adedi."""
        return self.gercek_uretim - self.hatali_uretim

    def __repr__(self):
        return f'<UretimVerisi {self.tarih} — OEE: {self.oee_yuzde}%>'


class ArizaKaydi(db.Model):
    __tablename__ = 'ariza_kaydi'
    __table_args__ = (
        db.Index('ix_ariza_durum_oncelik', 'durum', 'oncelik'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id', ondelete='CASCADE'), nullable=False, index=True)
    bildiren_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    atanan_teknisyen_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    baslangic_zamani = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    bitis_zamani = db.Column(db.DateTime, nullable=True)
    ariza_turu = db.Column(db.String(50), nullable=False)
    aciklama = db.Column(db.Text, nullable=False)
    cozum = db.Column(db.Text, nullable=True)
    oncelik = db.Column(db.String(20), default='normal')
    durum = db.Column(db.String(20), default='acik')
    mudahale_suresi_dk = db.Column(db.Integer, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bildiren = db.relationship('Kullanici', foreign_keys=[bildiren_id], backref='bildirilen_arizalar', lazy='joined')
    teknisyen = db.relationship('Kullanici', foreign_keys=[atanan_teknisyen_id], backref='atanan_arizalar', lazy='joined')

    @property
    def bekleme_suresi_dk(self):
        """Arızanın açık kaldığı süre (dakika)."""
        bitis = self.bitis_zamani or datetime.now(timezone.utc)

        b_zamani = self.baslangic_zamani
        if b_zamani and b_zamani.tzinfo is None:
            b_zamani = b_zamani.replace(tzinfo=timezone.utc)
        if bitis and bitis.tzinfo is None:
            bitis = bitis.replace(tzinfo=timezone.utc)

        diff = bitis - b_zamani
        return int(diff.total_seconds() / 60)

    def __repr__(self):
        return f'<ArizaKaydi M:{self.makine_id} — {self.durum}>'


class BakimKaydi(db.Model):
    __tablename__ = 'bakim_kaydi'
    __table_args__ = (
        db.Index('ix_bakim_makine_tarih', 'makine_id', 'tarih'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id', ondelete='CASCADE'), nullable=False, index=True)
    bakim_turu = db.Column(db.String(50), nullable=False)
    yapilan_islem = db.Column(db.Text, nullable=False)
    teknisyen_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    tarih = db.Column(db.Date, nullable=False)
    sure_dk = db.Column(db.Integer, nullable=True)
    maliyet = db.Column(db.Numeric(10, 2), nullable=True)
    sonraki_bakim_tarihi = db.Column(db.Date, nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    teknisyen = db.relationship('Kullanici', backref='bakim_kayitlari', lazy='joined')

    def __repr__(self):
        return f'<BakimKaydi M:{self.makine_id} — {self.bakim_turu}>'


class DurusKaydi(db.Model):
    __tablename__ = 'durus_kaydi'
    __table_args__ = (
        db.Index('ix_durus_makine_baslangic', 'makine_id', 'baslangic'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id', ondelete='CASCADE'), nullable=False, index=True)
    uretim_verisi_id = db.Column(db.Integer, db.ForeignKey('uretim_verisi.id', ondelete='SET NULL'), nullable=True)
    baslangic = db.Column(db.DateTime, nullable=False)
    bitis = db.Column(db.DateTime, nullable=True)
    sure_dk = db.Column(db.Integer, nullable=True)
    neden = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def hesapla_sure(self):
        """Duruş süresini hesaplar."""
        if self.baslangic and self.bitis:
            baslangic = self.baslangic.replace(tzinfo=timezone.utc) if self.baslangic.tzinfo is None else self.baslangic
            bitis = self.bitis.replace(tzinfo=timezone.utc) if self.bitis.tzinfo is None else self.bitis
            diff = bitis - baslangic
            self.sure_dk = int(diff.total_seconds() / 60)
        return self.sure_dk

    def __repr__(self):
        return f'<DurusKaydi M:{self.makine_id} — {self.kategori}>'
