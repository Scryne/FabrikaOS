"""
FDYS — Dış Kullanıcı & Borç/Tahsilat Modeli
Faz 4 — Talep & İş Takip + Dış Kullanıcı Paneli

Modeller:
    - DisKullanici: Dış kullanıcı (ortak/kiracı) paneli hesabı
    - Borc: Ortak/firma borç-alacak takibi
    - Tahsilat: Ödeme kayıtları

Sanayi sitesi ortakları ve firmalarına dış erişim paneli sağlar.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db, bcrypt


class DisKullanici(UserMixin, db.Model):
    """
    Dış kullanıcı (ortak / kiracı / firma yetkilisi) paneli hesabı.
    Ayrı bir login mekanizması kullanır (dahili kullanıcılardan bağımsız).

    İlk giriş:
        - Yönetici tarafından oluşturulan geçici şifre ile giriş yapılır.
        - gecici_sifre = True ise kullanıcı şifre değiştirmeye zorlanır.
    """
    __tablename__ = 'dis_kullanici'
    __table_args__ = (
        db.Index('ix_dis_kullanici_ortak', 'ortak_id'),
        db.Index('ix_dis_kullanici_firma', 'firma_id'),
    )

    # ── Durum Sabitleri ──
    DURUM_AKTIF = 'aktif'
    DURUM_PASIF = 'pasif'
    DURUM_ASKIDA = 'askida'

    DURUMLAR = {
        DURUM_AKTIF: 'Aktif',
        DURUM_PASIF: 'Pasif',
        DURUM_ASKIDA: 'Askıda',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ortak_id = db.Column(db.Integer, db.ForeignKey('ortak.id', ondelete='SET NULL'), nullable=True)
    firma_id = db.Column(db.Integer, db.ForeignKey('firma.id', ondelete='SET NULL'), nullable=True)

    kullanici_adi = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sifre_hash = db.Column(db.String(255), nullable=False)
    ad_soyad = db.Column(db.String(150), nullable=False)
    telefon = db.Column(db.String(20), nullable=True)
    eposta = db.Column(db.String(120), nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    son_giris = db.Column(db.DateTime, nullable=True)
    gecici_sifre = db.Column(db.Boolean, default=True, nullable=False)

    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    ortak = db.relationship('Ortak', foreign_keys=[ortak_id],
                             backref='dis_kullanicilar', lazy='joined')
    firma = db.relationship('Firma', foreign_keys=[firma_id],
                             backref='dis_kullanicilar', lazy='joined')

    def sifre_belirle(self, sifre):
        """Şifreyi bcrypt ile hash'leyerek kaydeder."""
        self.sifre_hash = bcrypt.generate_password_hash(sifre).decode('utf-8')

    def sifre_dogrula(self, sifre):
        """Girilen şifreyi kaydedilmiş hash ile doğrular."""
        return bcrypt.check_password_hash(self.sifre_hash, sifre)

    def giris_basarili(self):
        """Başarılı giriş sonrası son giriş zamanını günceller."""
        self.son_giris = datetime.now(timezone.utc)

    @property
    def bagli_isim(self):
        """Bağlı ortak veya firma adını döner."""
        if self.ortak:
            return self.ortak.ad_soyad
        if self.firma:
            return self.firma.unvan
        return self.ad_soyad

    @property
    def bagli_tip(self):
        """Bağlı tip: ortak veya firma."""
        if self.ortak_id:
            return 'ortak'
        if self.firma_id:
            return 'firma'
        return 'bagimsiz'

    @property
    def baslangic_harfler(self):
        """Ad soyadın baş harfleri (avatar için)."""
        parcalar = self.ad_soyad.split()
        if len(parcalar) >= 2:
            return (parcalar[0][0] + parcalar[-1][0]).upper()
        return self.ad_soyad[:2].upper()

    def __repr__(self):
        return f'<DisKullanici {self.kullanici_adi} — {self.ad_soyad}>'


class Borc(db.Model):
    """
    Ortak / firma borç-alacak takibi.

    Borç Türleri:
        - aidat: Aylık aidat
        - kira: Kira ödemesi
        - ceza: Ceza / idari yaptırım
        - bakim: Bakım ücreti
        - diger: Diğer
    """
    __tablename__ = 'borc'
    __table_args__ = (
        db.Index('ix_borc_ilgili', 'ilgili_tip', 'ilgili_id'),
        db.Index('ix_borc_durum', 'durum'),
        db.Index('ix_borc_son_odeme', 'son_odeme_tarihi'),
    )

    # ── Borç Türü Sabitleri ──
    TUR_AIDAT = 'aidat'
    TUR_KIRA = 'kira'
    TUR_CEZA = 'ceza'
    TUR_BAKIM = 'bakim'
    TUR_DIGER = 'diger'

    BORC_TURLERI = {
        TUR_AIDAT: 'Aidat',
        TUR_KIRA: 'Kira',
        TUR_CEZA: 'Ceza',
        TUR_BAKIM: 'Bakım Ücreti',
        TUR_DIGER: 'Diğer',
    }

    # ── Durum Sabitleri ──
    DURUM_ODENMEDI = 'odenmedi'
    DURUM_KISMI = 'kismi_odendi'
    DURUM_ODENDI = 'odendi'
    DURUM_GECIKTI = 'gecikti'

    DURUMLAR = {
        DURUM_ODENMEDI: 'Ödenmedi',
        DURUM_KISMI: 'Kısmi Ödendi',
        DURUM_ODENDI: 'Ödendi',
        DURUM_GECIKTI: 'Gecikti',
    }

    # ── İlgili Tip Sabitleri ──
    TIP_ORTAK = 'ortak'
    TIP_FIRMA = 'firma'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ilgili_tip = db.Column(db.String(10), nullable=False)  # ortak | firma
    ilgili_id = db.Column(db.Integer, nullable=False)

    borc_turu = db.Column(db.String(20), nullable=False, default=TUR_DIGER)
    aciklama = db.Column(db.String(300), nullable=True)
    donem = db.Column(db.String(20), nullable=True)  # "2026-05" gibi ay-yıl

    tutar = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    odenen_tutar = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    son_odeme_tarihi = db.Column(db.Date, nullable=True)

    durum = db.Column(db.String(20), nullable=False, default=DURUM_ODENMEDI)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    tahsilatlar = db.relationship('Tahsilat', backref='borc', lazy='dynamic',
                                   cascade='all, delete-orphan')

    @property
    def borc_turu_adi(self):
        return self.BORC_TURLERI.get(self.borc_turu, self.borc_turu)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def kalan_tutar(self):
        """Kalan borç tutarı."""
        return float(self.tutar) - float(self.odenen_tutar)

    @property
    def odeme_yuzde(self):
        """Ödeme yüzdesi."""
        if float(self.tutar) == 0:
            return 0
        return min(round(float(self.odenen_tutar) / float(self.tutar) * 100, 1), 100)

    @property
    def durum_sinif(self):
        """Bootstrap renk sınıfı."""
        return {
            'odenmedi': 'danger',
            'kismi_odendi': 'warning',
            'odendi': 'success',
            'gecikti': 'danger',
        }.get(self.durum, 'secondary')

    @property
    def gecikme_gunu(self):
        """Son ödeme tarihinden kaç gün geçtiğini hesaplar."""
        if not self.son_odeme_tarihi:
            return 0
        from datetime import date
        bugun = date.today()
        if bugun > self.son_odeme_tarihi:
            return (bugun - self.son_odeme_tarihi).days
        return 0

    def durum_guncelle(self):
        """Ödeme durumuna göre borç durumunu otomatik günceller."""
        from datetime import date
        if float(self.odenen_tutar) >= float(self.tutar):
            self.durum = self.DURUM_ODENDI
        elif float(self.odenen_tutar) > 0:
            self.durum = self.DURUM_KISMI
        elif self.son_odeme_tarihi and date.today() > self.son_odeme_tarihi:
            self.durum = self.DURUM_GECIKTI
        else:
            self.durum = self.DURUM_ODENMEDI

    def __repr__(self):
        return f'<Borc {self.ilgili_tip}:{self.ilgili_id} — {self.tutar} TL — {self.durum}>'


class Tahsilat(db.Model):
    """
    Ödeme kayıtları.
    Her borç için yapılan ödeme hareketlerini takip eder.
    """
    __tablename__ = 'tahsilat'
    __table_args__ = (
        db.Index('ix_tahsilat_borc', 'borc_id'),
        db.Index('ix_tahsilat_tarih', 'islem_tarihi'),
    )

    # ── Ödeme Türü Sabitleri ──
    TUR_NAKIT = 'nakit'
    TUR_HAVALE = 'havale'
    TUR_KREDI_KARTI = 'kredi_karti'
    TUR_POS = 'pos'
    TUR_CEVRIMICI = 'cevrimici'

    ODEME_TURLERI = {
        TUR_NAKIT: 'Nakit',
        TUR_HAVALE: 'Havale / EFT',
        TUR_KREDI_KARTI: 'Kredi Kartı',
        TUR_POS: 'POS',
        TUR_CEVRIMICI: 'Çevrimiçi Ödeme',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    borc_id = db.Column(db.Integer, db.ForeignKey('borc.id', ondelete='CASCADE'), nullable=False, index=True)

    tutar = db.Column(db.Numeric(14, 2), nullable=False)
    odeme_turu = db.Column(db.String(20), nullable=False, default=TUR_NAKIT)
    makbuz_no = db.Column(db.String(50), nullable=True)
    aciklama = db.Column(db.String(300), nullable=True)

    islem_tarihi = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    kaydeden_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    kaydeden = db.relationship('Kullanici', foreign_keys=[kaydeden_id],
                                backref='kaydedilen_tahsilatlar', lazy='joined')

    @property
    def odeme_turu_adi(self):
        return self.ODEME_TURLERI.get(self.odeme_turu, self.odeme_turu)

    def __repr__(self):
        return f'<Tahsilat B:{self.borc_id} — {self.tutar} TL — {self.odeme_turu}>'
