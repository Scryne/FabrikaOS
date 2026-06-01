"""
FDYS — Satın Alma Modülü Modeli
Faz 7 — Satın Alma Yönetimi (Basic)

Satın alma talebi, sipariş ve teklif karşılaştırma tablolarını içerir.
Stok modülüyle (Tedarikci) entegre çalışır.
"""

from datetime import datetime, timezone
from app.extensions import db


class SatinAlmaTalebi(db.Model):
    """
    Satın alma talepleri.

    Akış: Talep → Onay → Teklif Toplama → Sipariş → Teslim Alma
    Durumlar:
        - bekliyor: Onay bekliyor
        - onaylandi: Onaylandı, teklif/sipariş aşamasına geçebilir
        - reddedildi: Reddedildi
        - siparis_verildi: Sipariş oluşturuldu
        - teslim_alindi: Malzeme/hizmet teslim alındı
        - iptal: İptal edildi
    """
    __tablename__ = 'satin_alma_talebi'
    __table_args__ = (
        db.Index('ix_sa_talep_durum', 'durum'),
        db.Index('ix_sa_talep_tarih', 'olusturma_tarihi'),
        db.Index('ix_sa_talep_eden', 'talep_eden_id'),
    )

    # ── Malzeme/Hizmet Sabitleri ──
    TUR_MALZEME = 'malzeme'
    TUR_HIZMET = 'hizmet'

    TURLER = {
        TUR_MALZEME: 'Malzeme',
        TUR_HIZMET: 'Hizmet',
    }

    # ── Aciliyet Sabitleri ──
    ACILIYET_NORMAL = 'normal'
    ACILIYET_ACIL = 'acil'

    ACILIYETLER = {
        ACILIYET_NORMAL: 'Normal',
        ACILIYET_ACIL: 'Acil',
    }

    # ── Durum Sabitleri ──
    DURUM_BEKLIYOR = 'bekliyor'
    DURUM_ONAYLANDI = 'onaylandi'
    DURUM_REDDEDILDI = 'reddedildi'
    DURUM_SIPARIS_VERILDI = 'siparis_verildi'
    DURUM_TESLIM_ALINDI = 'teslim_alindi'
    DURUM_IPTAL = 'iptal'

    DURUMLAR = {
        DURUM_BEKLIYOR: 'Onay Bekliyor',
        DURUM_ONAYLANDI: 'Onaylandı',
        DURUM_REDDEDILDI: 'Reddedildi',
        DURUM_SIPARIS_VERILDI: 'Sipariş Verildi',
        DURUM_TESLIM_ALINDI: 'Teslim Alındı',
        DURUM_IPTAL: 'İptal',
    }

    # ── Birim Sabitleri ──
    BIRIMLER = {
        'adet': 'Adet',
        'kg': 'Kilogram',
        'litre': 'Litre',
        'metre': 'Metre',
        'paket': 'Paket',
        'kutu': 'Kutu',
        'ton': 'Ton',
        'set': 'Set',
        'takım': 'Takım',
        'diger': 'Diğer',
    }

    # ── Durum Renkleri ──
    DURUM_RENKLERI = {
        DURUM_BEKLIYOR: '#f59e0b',
        DURUM_ONAYLANDI: '#10b981',
        DURUM_REDDEDILDI: '#ef4444',
        DURUM_SIPARIS_VERILDI: '#3b82f6',
        DURUM_TESLIM_ALINDI: '#8b5cf6',
        DURUM_IPTAL: '#6b7280',
    }

    DURUM_IKONLARI = {
        DURUM_BEKLIYOR: 'bi-hourglass-split',
        DURUM_ONAYLANDI: 'bi-check-circle',
        DURUM_REDDEDILDI: 'bi-x-circle',
        DURUM_SIPARIS_VERILDI: 'bi-truck',
        DURUM_TESLIM_ALINDI: 'bi-box-seam',
        DURUM_IPTAL: 'bi-dash-circle',
    }

    DURUM_BADGE = {
        DURUM_BEKLIYOR: 'bg-warning text-dark',
        DURUM_ONAYLANDI: 'bg-success',
        DURUM_REDDEDILDI: 'bg-danger',
        DURUM_SIPARIS_VERILDI: 'bg-primary',
        DURUM_TESLIM_ALINDI: 'bg-info',
        DURUM_IPTAL: 'bg-secondary',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    talep_no = db.Column(db.String(30), unique=True, nullable=False, index=True)

    # Talep eden
    talep_eden_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    # Malzeme/Hizmet bilgileri
    malzeme_hizmet = db.Column(db.String(20), nullable=False, default=TUR_MALZEME)
    kalem_adi = db.Column(db.String(300), nullable=False)
    miktar = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    birim = db.Column(db.String(20), nullable=False, default='adet')
    tahmini_birim_fiyat = db.Column(db.Numeric(12, 2), nullable=True)

    # Açıklama
    aciklama = db.Column(db.Text, nullable=True)
    gerekce = db.Column(db.Text, nullable=True)

    # Öncelik / Aciliyet
    aciliyet = db.Column(db.String(20), nullable=False, default=ACILIYET_NORMAL)

    # Durum
    durum = db.Column(db.String(30), nullable=False, default=DURUM_BEKLIYOR)

    # Onay
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onay_tarihi = db.Column(db.DateTime, nullable=True)
    red_nedeni = db.Column(db.Text, nullable=True)

    # Tedarikçi (opsiyonel — talep aşamasında belirlenmiş olabilir)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id', ondelete='SET NULL'), nullable=True)

    # Departman
    departman = db.Column(db.String(100), nullable=True)

    # İstenen teslim tarihi
    istenen_teslim_tarihi = db.Column(db.Date, nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    talep_eden = db.relationship('Kullanici', foreign_keys=[talep_eden_id],
                                  backref='satin_alma_talepleri', lazy='joined')
    onaylayan = db.relationship('Kullanici', foreign_keys=[onaylayan_id],
                                 backref='satin_alma_onaylari', lazy='joined')
    tedarikci = db.relationship('Tedarikci', backref='satin_alma_talepleri', lazy='joined')
    siparisler = db.relationship('SatinAlmaSiparis', backref='talep', lazy='dynamic',
                                  cascade='all, delete-orphan', passive_deletes=True)
    teklifler = db.relationship('TeklifKarsilastirma', backref='talep', lazy='dynamic',
                                 cascade='all, delete-orphan', passive_deletes=True)

    @property
    def tur_adi(self):
        return self.TURLER.get(self.malzeme_hizmet, self.malzeme_hizmet)

    @property
    def aciliyet_adi(self):
        return self.ACILIYETLER.get(self.aciliyet, self.aciliyet)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def durum_rengi(self):
        return self.DURUM_RENKLERI.get(self.durum, '#6b7280')

    @property
    def durum_ikonu(self):
        return self.DURUM_IKONLARI.get(self.durum, 'bi-circle')

    @property
    def durum_badge(self):
        return self.DURUM_BADGE.get(self.durum, 'bg-secondary')

    @property
    def birim_adi(self):
        return self.BIRIMLER.get(self.birim, self.birim)

    @property
    def tahmini_toplam(self):
        """Tahmini toplam tutar."""
        if self.tahmini_birim_fiyat and self.miktar:
            return float(self.tahmini_birim_fiyat) * float(self.miktar)
        return None

    @property
    def teklif_sayisi(self):
        """Bu talep için toplanan teklif sayısı."""
        return self.teklifler.count()

    @property
    def secilen_teklif(self):
        """Seçilmiş teklif."""
        return self.teklifler.filter_by(secildi_mi=True).first()

    @property
    def onay_bekliyor_mu(self):
        return self.durum == self.DURUM_BEKLIYOR

    @property
    def siparis_olusturulabilir_mi(self):
        """Sipariş oluşturulabilir durumda mı?"""
        return self.durum == self.DURUM_ONAYLANDI

    @staticmethod
    def talep_no_olustur():
        """Sıradaki talep numarasını oluşturur: SA-2026-00001 formatı."""
        yil = datetime.now().year
        son = SatinAlmaTalebi.query.filter(
            SatinAlmaTalebi.talep_no.like(f'SA-{yil}-%')
        ).order_by(SatinAlmaTalebi.id.desc()).first()

        if son:
            try:
                son_no = int(son.talep_no.split('-')[-1])
            except (ValueError, IndexError):
                son_no = 0
        else:
            son_no = 0

        return f'SA-{yil}-{son_no + 1:05d}'

    def __repr__(self):
        return f'<SatinAlmaTalebi {self.talep_no} — {self.kalem_adi[:30]}>'


class SatinAlmaSiparis(db.Model):
    """
    Satın alma siparişleri.
    Onaylanmış bir talepten oluşturulur.

    Durumlar:
        - siparis_verildi: Tedarikçiye sipariş gönderildi
        - kargo: Kargoda / Yolda
        - teslim_alindi: Teslim alındı ve stok girişi yapıldı
        - iade: İade edildi
        - iptal: İptal edildi
    """
    __tablename__ = 'satin_alma_siparis'
    __table_args__ = (
        db.Index('ix_sa_siparis_durum', 'durum'),
        db.Index('ix_sa_siparis_tarih', 'siparis_tarihi'),
    )

    # ── Durum Sabitleri ──
    DURUM_SIPARIS_VERILDI = 'siparis_verildi'
    DURUM_KARGO = 'kargo'
    DURUM_TESLIM_ALINDI = 'teslim_alindi'
    DURUM_IADE = 'iade'
    DURUM_IPTAL = 'iptal'

    DURUMLAR = {
        DURUM_SIPARIS_VERILDI: 'Sipariş Verildi',
        DURUM_KARGO: 'Kargoda',
        DURUM_TESLIM_ALINDI: 'Teslim Alındı',
        DURUM_IADE: 'İade Edildi',
        DURUM_IPTAL: 'İptal',
    }

    DURUM_RENKLERI = {
        DURUM_SIPARIS_VERILDI: '#3b82f6',
        DURUM_KARGO: '#f59e0b',
        DURUM_TESLIM_ALINDI: '#10b981',
        DURUM_IADE: '#ef4444',
        DURUM_IPTAL: '#6b7280',
    }

    DURUM_BADGE = {
        DURUM_SIPARIS_VERILDI: 'bg-primary',
        DURUM_KARGO: 'bg-warning text-dark',
        DURUM_TESLIM_ALINDI: 'bg-success',
        DURUM_IADE: 'bg-danger',
        DURUM_IPTAL: 'bg-secondary',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siparis_no = db.Column(db.String(30), unique=True, nullable=False, index=True)

    # Talep bağlantısı
    talep_id = db.Column(db.Integer, db.ForeignKey('satin_alma_talebi.id', ondelete='CASCADE'), nullable=False, index=True)

    # Tedarikçi
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id', ondelete='SET NULL'), nullable=True)

    # Fiyat bilgileri
    birim_fiyat = db.Column(db.Numeric(12, 2), nullable=True)
    miktar = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    toplam_tutar = db.Column(db.Numeric(14, 2), nullable=True)
    kdv_orani = db.Column(db.Numeric(5, 2), nullable=True, default=20)
    genel_toplam = db.Column(db.Numeric(14, 2), nullable=True)

    # Tarihler
    siparis_tarihi = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    beklenen_teslim = db.Column(db.Date, nullable=True)
    gercek_teslim = db.Column(db.Date, nullable=True)

    # Fatura
    fatura_no = db.Column(db.String(50), nullable=True)

    # Durum
    durum = db.Column(db.String(30), nullable=False, default=DURUM_SIPARIS_VERILDI)

    # Sipariş veren
    olusturan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    # Teslim alan
    teslim_alan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    tedarikci = db.relationship('Tedarikci', backref='satin_alma_siparisleri', lazy='joined')
    olusturan = db.relationship('Kullanici', foreign_keys=[olusturan_id],
                                 backref='olusturulan_siparisler', lazy='joined')
    teslim_alan = db.relationship('Kullanici', foreign_keys=[teslim_alan_id],
                                   backref='teslim_alinan_siparisler', lazy='joined')

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def durum_rengi(self):
        return self.DURUM_RENKLERI.get(self.durum, '#6b7280')

    @property
    def durum_badge(self):
        return self.DURUM_BADGE.get(self.durum, 'bg-secondary')

    @property
    def gecikme_var_mi(self):
        """Beklenen teslim tarihini geçmiş mi?"""
        if self.beklenen_teslim and not self.gercek_teslim:
            return datetime.now(timezone.utc).date() > self.beklenen_teslim
        return False

    @property
    def gecikme_gun(self):
        """Kaç gün gecikmiş?"""
        if self.gecikme_var_mi:
            return (datetime.now(timezone.utc).date() - self.beklenen_teslim).days
        return 0

    @staticmethod
    def siparis_no_olustur():
        """Sıradaki sipariş numarasını oluşturur: SAS-2026-00001 formatı."""
        yil = datetime.now().year
        son = SatinAlmaSiparis.query.filter(
            SatinAlmaSiparis.siparis_no.like(f'SAS-{yil}-%')
        ).order_by(SatinAlmaSiparis.id.desc()).first()

        if son:
            try:
                son_no = int(son.siparis_no.split('-')[-1])
            except (ValueError, IndexError):
                son_no = 0
        else:
            son_no = 0

        return f'SAS-{yil}-{son_no + 1:05d}'

    def __repr__(self):
        return f'<SatinAlmaSiparis {self.siparis_no}>'


class TeklifKarsilastirma(db.Model):
    """
    Satın alma talebi için toplanan tedarikçi tekliflerinin karşılaştırması.
    Her satır bir tedarikçiden alınan bir teklifi temsil eder.
    """
    __tablename__ = 'teklif_karsilastirma'
    __table_args__ = (
        db.Index('ix_teklif_talep', 'talep_id'),
        db.Index('ix_teklif_tedarikci', 'tedarikci_id'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Talep bağlantısı
    talep_id = db.Column(db.Integer, db.ForeignKey('satin_alma_talebi.id', ondelete='CASCADE'), nullable=False, index=True)

    # Tedarikçi
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id', ondelete='SET NULL'), nullable=True)

    # Fiyat bilgileri
    birim_fiyat = db.Column(db.Numeric(12, 2), nullable=True)
    toplam_fiyat = db.Column(db.Numeric(14, 2), nullable=True)

    # Teslimat ve garanti
    teslimat_suresi = db.Column(db.Integer, nullable=True)         # Gün cinsinden
    garanti_suresi = db.Column(db.Integer, nullable=True)          # Ay cinsinden

    # Notlar ve seçim
    notlar = db.Column(db.Text, nullable=True)
    secildi_mi = db.Column(db.Boolean, default=False, nullable=False)

    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    tedarikci = db.relationship('Tedarikci', backref='teklifler', lazy='joined')

    @property
    def tedarikci_adi(self):
        return self.tedarikci.ad if self.tedarikci else '—'

    @property
    def fiyat_avantaj_rengi(self):
        """En düşük fiyat yeşil, diğerleri kırmızımsı."""
        if not self.talep_id:
            return '#6b7280'
        en_dusuk = TeklifKarsilastirma.query.filter_by(
            talep_id=self.talep_id
        ).order_by(TeklifKarsilastirma.toplam_fiyat.asc()).first()
        if en_dusuk and en_dusuk.id == self.id:
            return '#10b981'
        return '#ef4444'

    def __repr__(self):
        return f'<TeklifKarsilastirma Talep:{self.talep_id} Tedarikci:{self.tedarikci_adi}>'
