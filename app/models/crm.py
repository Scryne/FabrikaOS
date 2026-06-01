"""
FDYS — CRM (Müşteri İlişkileri) Modeli
Faz 2 — Ortak & Firma Yönetimi

Ortak (sanayi sitesi ortağı/daire sahibi), Firma (işletme),
Firma Yetkilisi ve İletişim Geçmişi tablolarını içerir.
Sanayi sitesi/OSB yönetimi için tasarlanmıştır.
"""

from datetime import datetime, timezone
from app.extensions import db


class Ortak(db.Model):
    """
    Sanayi sitesi ortağı (daire/işyeri sahibi).

    Ortak Tipleri:
        - malik: Mülk sahibi
        - kiraci: Kiracı
        - yetkili: Vekâletname ile yetkili kişi
        - vekil: Vekil
    """
    __tablename__ = 'ortak'
    __table_args__ = (
        db.Index('ix_ortak_blok_daire', 'blok', 'daire_no'),
        db.Index('ix_ortak_durum', 'durum'),
    )

    # ── Ortak Tipi Sabitleri ──
    TIP_MALIK = 'malik'
    TIP_KIRACI = 'kiraci'
    TIP_YETKILI = 'yetkili'
    TIP_VEKIL = 'vekil'

    ORTAK_TIPLERI = {
        TIP_MALIK: 'Malik',
        TIP_KIRACI: 'Kiracı',
        TIP_YETKILI: 'Yetkili',
        TIP_VEKIL: 'Vekil',
    }

    # ── Durum Sabitleri ──
    DURUM_AKTIF = 'aktif'
    DURUM_PASIF = 'pasif'
    DURUM_CIKIS = 'cikis_yapti'

    DURUMLAR = {
        DURUM_AKTIF: 'Aktif',
        DURUM_PASIF: 'Pasif',
        DURUM_CIKIS: 'Çıkış Yaptı',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ortak_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    ad_soyad = db.Column(db.String(150), nullable=False)
    tc_kimlik = db.Column(db.String(11), unique=True, nullable=True)
    telefon = db.Column(db.String(20), nullable=True)
    telefon2 = db.Column(db.String(20), nullable=True)
    eposta = db.Column(db.String(120), nullable=True)
    adres = db.Column(db.Text, nullable=True)

    # Blok & Daire bilgileri
    blok = db.Column(db.String(50), nullable=True)           # "A", "B", "C" veya "101"
    daire_no = db.Column(db.String(20), nullable=True)       # "1", "2", "3" veya "101-1"

    ortak_tipi = db.Column(db.String(20), nullable=False, default=TIP_MALIK)
    hisse_orani = db.Column(db.Numeric(5, 2), nullable=True)   # Mülkiyet payı (%)
    m2 = db.Column(db.Numeric(8, 2), nullable=True)            # Alan (m²)
    milliyet = db.Column(db.String(50), nullable=True, default='T.C.')
    durum = db.Column(db.String(20), nullable=False, default=DURUM_AKTIF)
    fotograf = db.Column(db.String(255), nullable=True)         # Profil fotoğrafı dosya yolu
    notlar = db.Column(db.Text, nullable=True)

    # GPS koordinatları (harita için)
    harita_enlem = db.Column(db.Float, nullable=True)
    harita_boylam = db.Column(db.Float, nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    iletisim_gecmisi = db.relationship('CrmIletisimGecmisi',
                                        primaryjoin="and_(CrmIletisimGecmisi.ilgili_tip=='ortak', "
                                                    "foreign(CrmIletisimGecmisi.ilgili_id)==Ortak.id)",
                                        backref='ilgili_ortak', lazy='dynamic', viewonly=True)

    @property
    def ortak_tipi_adi(self):
        return self.ORTAK_TIPLERI.get(self.ortak_tipi, self.ortak_tipi)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def konum_bilgi(self):
        """Blok ve daire no birleşik gösterimi."""
        parts = []
        if self.blok:
            parts.append(f'Blok {self.blok}')
        if self.daire_no:
            parts.append(f'No {self.daire_no}')
        return ' - '.join(parts) if parts else '—'

    @property
    def baslangic_harfler(self):
        """Ad soyadın baş harfleri (avatar için)."""
        parcalar = self.ad_soyad.split()
        if len(parcalar) >= 2:
            return (parcalar[0][0] + parcalar[-1][0]).upper()
        return self.ad_soyad[:2].upper()

    def __repr__(self):
        return f'<Ortak {self.ortak_no} — {self.ad_soyad}>'


class Firma(db.Model):
    """
    Sanayi sitesindeki firma/işletme.

    Durumlar:
        - aktif: Aktif faaliyet
        - pasif: Geçici pasif
        - kapandi: Kapalı/tasfiye
    """
    __tablename__ = 'firma'
    __table_args__ = (
        db.Index('ix_firma_blok_daire', 'blok', 'daire_no'),
        db.Index('ix_firma_durum', 'durum'),
    )

    # ── Durum Sabitleri ──
    DURUM_AKTIF = 'aktif'
    DURUM_PASIF = 'pasif'
    DURUM_KAPANDI = 'kapandi'

    DURUMLAR = {
        DURUM_AKTIF: 'Aktif',
        DURUM_PASIF: 'Pasif',
        DURUM_KAPANDI: 'Kapandı',
    }

    # ── Sektör Sabitleri ──
    SEKTORLER = {
        'uretim': 'Üretim',
        'hizmet': 'Hizmet',
        'ticaret': 'Ticaret',
        'lojistik': 'Lojistik',
        'gida': 'Gıda',
        'insaat': 'İnşaat',
        'tekstil': 'Tekstil',
        'metal': 'Metal İşleme',
        'kimya': 'Kimya',
        'plastik': 'Plastik',
        'enerji': 'Enerji',
        'bilisim': 'Bilişim',
        'otomotiv': 'Otomotiv',
        'diger': 'Diğer',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firma_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    unvan = db.Column(db.String(300), nullable=False)
    vergi_no = db.Column(db.String(20), unique=True, nullable=True)
    vergi_dairesi = db.Column(db.String(100), nullable=True)
    sektor = db.Column(db.String(50), nullable=True, default='diger')
    faaliyet_alani = db.Column(db.String(200), nullable=True)

    yetkili_kisi = db.Column(db.String(150), nullable=True)   # Ana yetkili kişi
    telefon = db.Column(db.String(20), nullable=True)
    eposta = db.Column(db.String(120), nullable=True)
    web_sitesi = db.Column(db.String(200), nullable=True)
    adres = db.Column(db.Text, nullable=True)

    # Blok & Daire bilgileri
    blok = db.Column(db.String(50), nullable=True)
    daire_no = db.Column(db.String(20), nullable=True)

    m2 = db.Column(db.Numeric(8, 2), nullable=True)           # İşyeri alanı
    calisan_sayisi = db.Column(db.Integer, nullable=True)
    logo = db.Column(db.String(255), nullable=True)            # Logo dosya yolu
    durum = db.Column(db.String(20), nullable=False, default=DURUM_AKTIF)
    notlar = db.Column(db.Text, nullable=True)

    # GPS koordinatları (harita için)
    harita_enlem = db.Column(db.Float, nullable=True)
    harita_boylam = db.Column(db.Float, nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    yetkililer = db.relationship('FirmaYetkilisi', backref='firma', lazy='dynamic',
                                 cascade='all, delete-orphan', passive_deletes=True)
    iletisim_gecmisi = db.relationship('CrmIletisimGecmisi',
                                        primaryjoin="and_(CrmIletisimGecmisi.ilgili_tip=='firma', "
                                                    "foreign(CrmIletisimGecmisi.ilgili_id)==Firma.id)",
                                        backref='ilgili_firma', lazy='dynamic', viewonly=True)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def sektor_adi(self):
        return self.SEKTORLER.get(self.sektor, self.sektor or '—')

    @property
    def konum_bilgi(self):
        """Blok ve daire no birleşik gösterimi."""
        parts = []
        if self.blok:
            parts.append(f'Blok {self.blok}')
        if self.daire_no:
            parts.append(f'No {self.daire_no}')
        return ' - '.join(parts) if parts else '—'

    @property
    def baslangic_harfler(self):
        """Ünvan baş harfleri (avatar için)."""
        parcalar = self.unvan.split()
        if len(parcalar) >= 2:
            return (parcalar[0][0] + parcalar[1][0]).upper()
        return self.unvan[:2].upper()

    def __repr__(self):
        return f'<Firma {self.firma_no} — {self.unvan}>'


class FirmaYetkilisi(db.Model):
    """
    Firmanın yetkili kişileri.
    Bir firmanın birden fazla yetkilisi olabilir.
    """
    __tablename__ = 'firma_yetkilisi'
    __table_args__ = (
        db.Index('ix_yetkili_firma', 'firma_id'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firma_id = db.Column(db.Integer, db.ForeignKey('firma.id', ondelete='CASCADE'), nullable=False, index=True)
    ad_soyad = db.Column(db.String(150), nullable=False)
    gorev = db.Column(db.String(100), nullable=True)           # Genel Müdür, Finans Müdürü vb.
    telefon = db.Column(db.String(20), nullable=True)
    eposta = db.Column(db.String(120), nullable=True)
    tc_kimlik = db.Column(db.String(11), nullable=True)
    yetki_belgesi = db.Column(db.String(255), nullable=True)   # Yetki belgesi dosya yolu
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def baslangic_harfler(self):
        """Ad soyadın baş harfleri."""
        parcalar = self.ad_soyad.split()
        if len(parcalar) >= 2:
            return (parcalar[0][0] + parcalar[-1][0]).upper()
        return self.ad_soyad[:2].upper()

    def __repr__(self):
        return f'<FirmaYetkilisi {self.ad_soyad} — {self.gorev}>'


class CrmIletisimGecmisi(db.Model):
    """
    Ortak/firma ile yapılan iletişim geçmişi.
    Polimorfik ilişki: ilgili_tip (ortak|firma) + ilgili_id.
    """
    __tablename__ = 'crm_iletisim_gecmisi'
    __table_args__ = (
        db.Index('ix_iletisim_ilgili', 'ilgili_tip', 'ilgili_id'),
        db.Index('ix_iletisim_tarih', 'tarih'),
    )

    # ── İletişim Türü Sabitleri ──
    ILETISIM_TELEFON = 'telefon'
    ILETISIM_EPOSTA = 'eposta'
    ILETISIM_YUZ_YUZE = 'yuz_yuze'
    ILETISIM_MEKTUP = 'mektup'
    ILETISIM_SMS = 'sms'

    ILETISIM_TURLERI = {
        ILETISIM_TELEFON: 'Telefon',
        ILETISIM_EPOSTA: 'E-posta',
        ILETISIM_YUZ_YUZE: 'Yüz Yüze',
        ILETISIM_MEKTUP: 'Mektup / Yazışma',
        ILETISIM_SMS: 'SMS',
    }

    # ── İlgili Tip Sabitleri ──
    TIP_ORTAK = 'ortak'
    TIP_FIRMA = 'firma'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ilgili_tip = db.Column(db.String(10), nullable=False)      # ortak | firma
    ilgili_id = db.Column(db.Integer, nullable=False)
    iletisim_turu = db.Column(db.String(20), nullable=False, default=ILETISIM_TELEFON)
    konu = db.Column(db.String(200), nullable=False)
    detay = db.Column(db.Text, nullable=True)
    sonuc = db.Column(db.Text, nullable=True)
    yapan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    tarih = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    yapan = db.relationship('Kullanici', foreign_keys=[yapan_id],
                            backref='crm_iletisim_kayitlari', lazy='joined')

    @property
    def iletisim_turu_adi(self):
        return self.ILETISIM_TURLERI.get(self.iletisim_turu, self.iletisim_turu)

    @property
    def ilgili_tip_adi(self):
        return 'Ortak' if self.ilgili_tip == self.TIP_ORTAK else 'Firma'

    def __repr__(self):
        return f'<CrmIletisimGecmisi {self.iletisim_turu} — {self.konu[:30]}>'
