"""
FDYS — İş Emri ve Görev Yönetimi Modeli
Kategori 6 — İş Akışı Otomasyonu

Modeller:
    - IsEmri: Merkezi iş emri tablosu (SLA takibi, durum akışı, atama)
    - IsEmriYorum: İş emirlerine yorum/not akışı
"""

from datetime import datetime, timedelta, timezone
from app.extensions import db


class IsEmri(db.Model):
    """
    Merkezi İş Emri modeli.

    Tüm modüllerden tetiklenen iş emirlerini tek bir tabloda yönetir.
    Durum Akışı: Açık → Atandı → Devam → Tamamlandı → Onaylandı
    SLA takibi ile hedef süre kontrolü sağlar.
    """
    __tablename__ = 'is_emri'
    __table_args__ = (
        db.Index('ix_is_emri_durum_oncelik', 'durum', 'oncelik'),
        db.Index('ix_is_emri_atanan', 'atanan_id', 'durum'),
    )

    # Sabitler
    DURUM_ACIK = 'acik'
    DURUM_ATANDI = 'atandi'
    DURUM_DEVAM = 'devam'
    DURUM_TAMAMLANDI = 'tamamlandi'
    DURUM_ONAYLANDI = 'onaylandi'
    DURUM_IPTAL = 'iptal'

    ONCELIK_KRITIK = 'kritik'
    ONCELIK_YUKSEK = 'yuksek'
    ONCELIK_NORMAL = 'normal'
    ONCELIK_DUSUK = 'dusuk'

    KATEGORI_ARIZA = 'ariza'
    KATEGORI_BAKIM = 'bakim'
    KATEGORI_SATIN_ALMA = 'satin_alma'
    KATEGORI_EGITIM = 'egitim'
    KATEGORI_GENEL = 'genel'

    # Geçerli durum geçişleri
    GECERLI_GECISLER = {
        DURUM_ACIK: [DURUM_ATANDI, DURUM_DEVAM, DURUM_IPTAL],
        DURUM_ATANDI: [DURUM_DEVAM, DURUM_IPTAL],
        DURUM_DEVAM: [DURUM_TAMAMLANDI, DURUM_IPTAL],
        DURUM_TAMAMLANDI: [DURUM_ONAYLANDI, DURUM_DEVAM],  # Red → Devam'a geri
        DURUM_ONAYLANDI: [],
        DURUM_IPTAL: [],
    }

    # Öncelik → Varsayılan SLA süresi (saat)
    VARSAYILAN_SLA = {
        ONCELIK_KRITIK: 4,
        ONCELIK_YUKSEK: 8,
        ONCELIK_NORMAL: 24,
        ONCELIK_DUSUK: 72,
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_emri_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)
    kaynak_modul = db.Column(db.String(50), nullable=False, default='manuel')  # makine|stok|isg|bakim|manuel
    kaynak_id = db.Column(db.Integer, nullable=True)  # Tetikleyen kaydın ID'si
    kategori = db.Column(db.String(50), nullable=False, default='genel')  # ariza|bakim|satin_alma|egitim|genel
    oncelik = db.Column(db.String(20), nullable=False, default='normal')  # kritik|yuksek|normal|dusuk
    durum = db.Column(db.String(20), nullable=False, default='acik')  # acik|atandi|devam|tamamlandi|onaylandi|iptal

    # Atama ilişkileri
    olusturan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    atanan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    # SLA takibi
    sla_saat = db.Column(db.Integer, nullable=True)
    sla_bitis = db.Column(db.DateTime, nullable=True)
    sla_asildi_mi = db.Column(db.Boolean, default=False)

    # Zaman takibi
    baslama_zamani = db.Column(db.DateTime, nullable=True)
    tamamlanma_zamani = db.Column(db.DateTime, nullable=True)
    onay_zamani = db.Column(db.DateTime, nullable=True)
    gercek_sure_dk = db.Column(db.Integer, nullable=True)

    # Notlar
    notlar = db.Column(db.Text, nullable=True)
    cozum_notu = db.Column(db.Text, nullable=True)

    # Zaman damgaları
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    olusturan = db.relationship('Kullanici', foreign_keys=[olusturan_id],
                                 backref='olusturulan_is_emirleri', lazy='joined')
    atanan = db.relationship('Kullanici', foreign_keys=[atanan_id],
                              backref='atanan_is_emirleri', lazy='joined')
    onaylayan = db.relationship('Kullanici', foreign_keys=[onaylayan_id],
                                 backref='onaylanan_is_emirleri', lazy='joined')
    yorumlar = db.relationship('IsEmriYorum', backref='is_emri', lazy='dynamic',
                                cascade='all, delete-orphan',
                                order_by='IsEmriYorum.olusturma_tarihi.asc()')

    def gecis_gecerli_mi(self, yeni_durum):
        """Durum geçişinin geçerli olup olmadığını kontrol eder."""
        return yeni_durum in self.GECERLI_GECISLER.get(self.durum, [])

    def sla_hesapla(self):
        """SLA bitiş zamanını hesaplar ve atar."""
        if self.sla_saat is None:
            self.sla_saat = self.VARSAYILAN_SLA.get(self.oncelik, 24)
        self.sla_bitis = self.olusturma_tarihi + timedelta(hours=self.sla_saat)

    def sla_kontrol(self):
        """SLA durumunu kontrol eder ve aşıldıysa işaretler."""
        if self.sla_bitis and self.durum not in (self.DURUM_TAMAMLANDI, self.DURUM_ONAYLANDI, self.DURUM_IPTAL):
            if datetime.now(timezone.utc) > self.sla_bitis.replace(tzinfo=timezone.utc) if self.sla_bitis.tzinfo is None else self.sla_bitis:
                self.sla_asildi_mi = True
                return True
        return False

    @property
    def sla_kalan_dk(self):
        """SLA bitiş zamanına kalan dakika. Negatifse SLA aşılmış demektir."""
        if not self.sla_bitis:
            return None
        sla_bitis = self.sla_bitis.replace(tzinfo=timezone.utc) if self.sla_bitis.tzinfo is None else self.sla_bitis
        diff = sla_bitis - datetime.now(timezone.utc)
        return int(diff.total_seconds() / 60)

    @property
    def sla_yuzde(self):
        """SLA süresinin yüzde kaçının geçtiğini döner (0-100+)."""
        if not self.sla_bitis or not self.sla_saat:
            return 0
        toplam_dk = self.sla_saat * 60
        kalan = self.sla_kalan_dk
        if kalan is None:
            return 0
        gecen = toplam_dk - kalan
        return min(round((gecen / toplam_dk) * 100, 1), 100) if toplam_dk > 0 else 0

    @property
    def sla_kalan_yuzde(self):
        """SLA süresinin yüzde kaçının kaldığını döner (100-0)."""
        return max(0, 100 - self.sla_yuzde)

    @property
    def oncelik_sinif(self):
        """Bootstrap renk sınıfı: badge/alert için."""
        return {
            'kritik': 'danger',
            'yuksek': 'warning',
            'normal': 'primary',
            'dusuk': 'secondary',
        }.get(self.oncelik, 'secondary')

    @property
    def durum_sinif(self):
        """Durum badge renk sınıfı."""
        return {
            'acik': 'info',
            'atandi': 'primary',
            'devam': 'warning',
            'tamamlandi': 'success',
            'onaylandi': 'success',
            'iptal': 'secondary',
        }.get(self.durum, 'secondary')

    @property
    def durum_etiket(self):
        """Türkçe durum etiketi."""
        return {
            'acik': 'Açık',
            'atandi': 'Atandı',
            'devam': 'Devam Ediyor',
            'tamamlandi': 'Tamamlandı',
            'onaylandi': 'Onaylandı',
            'iptal': 'İptal',
        }.get(self.durum, self.durum)

    @property
    def oncelik_etiket(self):
        """Türkçe öncelik etiketi."""
        return {
            'kritik': 'Kritik',
            'yuksek': 'Yüksek',
            'normal': 'Normal',
            'dusuk': 'Düşük',
        }.get(self.oncelik, self.oncelik)

    @property
    def kategori_etiket(self):
        """Türkçe kategori etiketi."""
        return {
            'ariza': 'Arıza',
            'bakim': 'Bakım',
            'satin_alma': 'Satın Alma',
            'egitim': 'Eğitim',
            'genel': 'Genel',
        }.get(self.kategori, self.kategori)

    @property
    def kaynak_modul_etiket(self):
        """Türkçe kaynak modül etiketi."""
        return {
            'makine': 'Makine & Üretim',
            'stok': 'Stok Yönetimi',
            'isg': 'İSG',
            'bakim': 'Bakım',
            'manuel': 'Manuel',
        }.get(self.kaynak_modul, self.kaynak_modul)

    def __repr__(self):
        return f'<IsEmri {self.is_emri_no} — {self.durum}>'


class IsEmriYorum(db.Model):
    """
    İş emri yorum/not akışı.
    Her iş emrine bağlı kronolojik yorum listesi sağlar.
    """
    __tablename__ = 'is_emri_yorum'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_emri_id = db.Column(db.Integer, db.ForeignKey('is_emri.id', ondelete='CASCADE'), nullable=False, index=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    icerik = db.Column(db.Text, nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    kullanici = db.relationship('Kullanici', backref='is_emri_yorumlari', lazy='joined')

    def __repr__(self):
        return f'<IsEmriYorum IE:{self.is_emri_id} — {self.kullanici_id}>'
