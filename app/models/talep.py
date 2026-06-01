"""
FDYS — Talep & İş Takip Modeli
Faz 4 — Talep & İş Takip + Dış Kullanıcı Paneli

Modeller:
    - Talep: Dahili + dış kullanıcılardan gelen talep/şikayet/istek
    - TalepGecmisi: Talep üzerindeki tüm işlem geçmişi (timeline)

Sanayi sitesi / OSB yönetimi için tasarlanmıştır.
"""

from datetime import datetime, timezone
from app.extensions import db


class Talep(db.Model):
    """
    Dahili + dış kullanıcılardan gelen talep / şikayet / istek.

    Talep Akışı:
        Açık → Yönlendirildi → Devam → Tamamlandı → Kapandı
        Her aşamada SMS / e-posta bildirim gönderilebilir.

    Talep No Formatı: TLP-YYYY-NNNNN (örn: TLP-2026-00042)
    """
    __tablename__ = 'talep'
    __table_args__ = (
        db.Index('ix_talep_durum_oncelik', 'durum', 'oncelik'),
        db.Index('ix_talep_kategori', 'kategori'),
        db.Index('ix_talep_atanan', 'atanan_id', 'durum'),
        db.Index('ix_talep_tarih', 'olusturma_tarihi'),
    )

    # ── Talep Eden Tipi Sabitleri ──
    TIP_DAHILI = 'dahili'
    TIP_ORTAK = 'ortak'
    TIP_FIRMA = 'firma'
    TIP_DIS_KULLANICI = 'dis_kullanici'

    TALEP_EDEN_TIPLERI = {
        TIP_DAHILI: 'Dahili Kullanıcı',
        TIP_ORTAK: 'Ortak',
        TIP_FIRMA: 'Firma',
        TIP_DIS_KULLANICI: 'Dış Kullanıcı',
    }

    # ── Kategori Sabitleri ──
    KAT_TEKNIK = 'teknik_hizmet'
    KAT_GUVENLIK = 'guvenlik'
    KAT_IDARI = 'idari'
    KAT_TEMIZLIK = 'temizlik'
    KAT_OTOPARK = 'otopark'
    KAT_ORTAK_ALAN = 'ortak_alan'
    KAT_ELEKTRIK = 'elektrik'
    KAT_MEKANIK = 'mekanik'
    KAT_DIGER = 'diger'

    KATEGORILER = {
        KAT_TEKNIK: 'Teknik Hizmet',
        KAT_GUVENLIK: 'Güvenlik',
        KAT_IDARI: 'İdari İşler',
        KAT_TEMIZLIK: 'Temizlik',
        KAT_OTOPARK: 'Otopark',
        KAT_ORTAK_ALAN: 'Ortak Alan',
        KAT_ELEKTRIK: 'Elektrik',
        KAT_MEKANIK: 'Mekanik / Tesisat',
        KAT_DIGER: 'Diğer',
    }

    # ── Öncelik Sabitleri ──
    ONCELIK_DUSUK = 'dusuk'
    ONCELIK_NORMAL = 'normal'
    ONCELIK_YUKSEK = 'yuksek'
    ONCELIK_ACIL = 'acil'

    ONCELIKLER = {
        ONCELIK_DUSUK: 'Düşük',
        ONCELIK_NORMAL: 'Normal',
        ONCELIK_YUKSEK: 'Yüksek',
        ONCELIK_ACIL: 'Acil',
    }

    # ── Durum Sabitleri ──
    DURUM_ACIK = 'acik'
    DURUM_YONLENDIRILDI = 'yonlendirildi'
    DURUM_DEVAM = 'devam'
    DURUM_TAMAMLANDI = 'tamamlandi'
    DURUM_KAPANDI = 'kapandi'
    DURUM_REDDEDILDI = 'reddedildi'

    DURUMLAR = {
        DURUM_ACIK: 'Açık',
        DURUM_YONLENDIRILDI: 'Yönlendirildi',
        DURUM_DEVAM: 'Devam Ediyor',
        DURUM_TAMAMLANDI: 'Tamamlandı',
        DURUM_KAPANDI: 'Kapandı',
        DURUM_REDDEDILDI: 'Reddedildi',
    }

    # ── Geçerli Durum Geçişleri ──
    GECERLI_GECISLER = {
        DURUM_ACIK: [DURUM_YONLENDIRILDI, DURUM_DEVAM, DURUM_REDDEDILDI],
        DURUM_YONLENDIRILDI: [DURUM_DEVAM, DURUM_REDDEDILDI],
        DURUM_DEVAM: [DURUM_TAMAMLANDI, DURUM_YONLENDIRILDI],
        DURUM_TAMAMLANDI: [DURUM_KAPANDI, DURUM_DEVAM],
        DURUM_KAPANDI: [],
        DURUM_REDDEDILDI: [DURUM_ACIK],
    }

    # ── Departman Sabitleri ──
    DEPT_TEKNIK = 'teknik'
    DEPT_GUVENLIK = 'guvenlik'
    DEPT_IDARI = 'idari'
    DEPT_YONETIM = 'yonetim'

    DEPARTMANLAR = {
        DEPT_TEKNIK: 'Teknik',
        DEPT_GUVENLIK: 'Güvenlik',
        DEPT_IDARI: 'İdari',
        DEPT_YONETIM: 'Yönetim',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    talep_no = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Talep eden (polimorfik)
    talep_eden_tip = db.Column(db.String(20), nullable=False, default=TIP_DAHILI)
    talep_eden_id = db.Column(db.Integer, nullable=True)
    talep_eden_adi = db.Column(db.String(100), nullable=False)  # Denormalize (hız için)

    # Kategori & içerik
    kategori = db.Column(db.String(30), nullable=False, default=KAT_DIGER)
    alt_kategori = db.Column(db.String(100), nullable=True)
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)

    # Öncelik & Durum
    oncelik = db.Column(db.String(20), nullable=False, default=ONCELIK_NORMAL)
    durum = db.Column(db.String(20), nullable=False, default=DURUM_ACIK)

    # Atama
    atanan_departman = db.Column(db.String(30), nullable=True)
    atanan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    # İş emri dönüşümü
    is_emri_id = db.Column(db.Integer, db.ForeignKey('is_emri.id', ondelete='SET NULL'), nullable=True)

    # Çözüm
    cozum_notu = db.Column(db.Text, nullable=True)
    memnuniyet_puani = db.Column(db.Integer, nullable=True)  # 1-5

    # Bildirim tercihleri
    sms_bildirim = db.Column(db.Boolean, default=False, nullable=False)
    eposta_bildirim = db.Column(db.Boolean, default=True, nullable=False)

    # Konum
    konum_bilgi = db.Column(db.String(200), nullable=True)  # Blok, kat, daire

    # Zaman damgaları
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))
    kapanma_tarihi = db.Column(db.DateTime, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)

    # İlişkiler
    atanan = db.relationship('Kullanici', foreign_keys=[atanan_id],
                              backref='atanan_talepler', lazy='joined')
    is_emri = db.relationship('IsEmri', foreign_keys=[is_emri_id],
                               backref='kaynak_talep', lazy='joined')
    gecmis = db.relationship('TalepGecmisi', backref='talep', lazy='dynamic',
                              cascade='all, delete-orphan',
                              order_by='TalepGecmisi.tarih.desc()')

    def gecis_gecerli_mi(self, yeni_durum):
        """Durum geçişinin geçerli olup olmadığını kontrol eder."""
        return yeni_durum in self.GECERLI_GECISLER.get(self.durum, [])

    @property
    def kategori_adi(self):
        return self.KATEGORILER.get(self.kategori, self.kategori)

    @property
    def oncelik_adi(self):
        return self.ONCELIKLER.get(self.oncelik, self.oncelik)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def departman_adi(self):
        return self.DEPARTMANLAR.get(self.atanan_departman, self.atanan_departman or '—')

    @property
    def talep_eden_tip_adi(self):
        return self.TALEP_EDEN_TIPLERI.get(self.talep_eden_tip, self.talep_eden_tip)

    @property
    def oncelik_sinif(self):
        """Bootstrap renk sınıfı."""
        return {
            'acil': 'danger',
            'yuksek': 'warning',
            'normal': 'primary',
            'dusuk': 'secondary',
        }.get(self.oncelik, 'secondary')

    @property
    def durum_sinif(self):
        """Durum badge renk sınıfı."""
        return {
            'acik': 'info',
            'yonlendirildi': 'primary',
            'devam': 'warning',
            'tamamlandi': 'success',
            'kapandi': 'secondary',
            'reddedildi': 'danger',
        }.get(self.durum, 'secondary')

    @property
    def durum_icon(self):
        """Durum simgesi."""
        return {
            'acik': 'bi-circle',
            'yonlendirildi': 'bi-arrow-right-circle',
            'devam': 'bi-play-circle',
            'tamamlandi': 'bi-check-circle',
            'kapandi': 'bi-x-circle',
            'reddedildi': 'bi-slash-circle',
        }.get(self.durum, 'bi-circle')

    @property
    def cozum_suresi_dk(self):
        """Talebin açılışından kapanışına kadar geçen süre (dakika)."""
        if not self.kapanma_tarihi:
            return None
        olusturma = self.olusturma_tarihi.replace(tzinfo=timezone.utc) if self.olusturma_tarihi.tzinfo is None else self.olusturma_tarihi
        kapanma = self.kapanma_tarihi.replace(tzinfo=timezone.utc) if self.kapanma_tarihi.tzinfo is None else self.kapanma_tarihi
        diff = kapanma - olusturma
        return int(diff.total_seconds() / 60)

    @property
    def gecen_sure_str(self):
        """Talebin üzerinden geçen süre (okunabilir format)."""
        now = datetime.now(timezone.utc)
        olusturma = self.olusturma_tarihi.replace(tzinfo=timezone.utc) if self.olusturma_tarihi.tzinfo is None else self.olusturma_tarihi
        diff = now - olusturma
        dakika = int(diff.total_seconds() / 60)
        if dakika < 60:
            return f'{dakika} dk'
        saat = dakika // 60
        if saat < 24:
            return f'{saat} saat'
        gun = saat // 24
        return f'{gun} gün'

    def __repr__(self):
        return f'<Talep {self.talep_no} — {self.durum}>'


class TalepGecmisi(db.Model):
    """
    Talep üzerindeki tüm işlem geçmişi (timeline).
    Her durum değişikliği, yönlendirme, yorum ve bildirim loglanır.
    """
    __tablename__ = 'talep_gecmisi'
    __table_args__ = (
        db.Index('ix_talep_gecmisi_talep', 'talep_id'),
        db.Index('ix_talep_gecmisi_tarih', 'tarih'),
    )

    # ── İşlem Türü Sabitleri ──
    ISLEM_OLUSTURMA = 'olusturma'
    ISLEM_DURUM_DEGISIKLIGI = 'durum_degisikligi'
    ISLEM_YONLENDIRME = 'yonlendirme'
    ISLEM_YORUM = 'yorum'
    ISLEM_SMS = 'sms_bildirim'
    ISLEM_EPOSTA = 'eposta_bildirim'
    ISLEM_IS_EMRI = 'is_emri_donusumu'
    ISLEM_MEMNUNIYET = 'memnuniyet_puani'

    ISLEM_TURLERI = {
        ISLEM_OLUSTURMA: 'Oluşturma',
        ISLEM_DURUM_DEGISIKLIGI: 'Durum Değişikliği',
        ISLEM_YONLENDIRME: 'Yönlendirme',
        ISLEM_YORUM: 'Yorum',
        ISLEM_SMS: 'SMS Bildirim',
        ISLEM_EPOSTA: 'E-posta Bildirim',
        ISLEM_IS_EMRI: 'İş Emri Dönüşümü',
        ISLEM_MEMNUNIYET: 'Memnuniyet Puanı',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    talep_id = db.Column(db.Integer, db.ForeignKey('talep.id', ondelete='CASCADE'), nullable=False, index=True)

    islem_turu = db.Column(db.String(30), nullable=False, default=ISLEM_OLUSTURMA)
    yapan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    yapan_adi = db.Column(db.String(100), nullable=True)
    aciklama = db.Column(db.Text, nullable=True)

    eski_durum = db.Column(db.String(20), nullable=True)
    yeni_durum = db.Column(db.String(20), nullable=True)

    tarih = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    yapan = db.relationship('Kullanici', foreign_keys=[yapan_id],
                             backref='talep_islemleri', lazy='joined')

    @property
    def islem_turu_adi(self):
        return self.ISLEM_TURLERI.get(self.islem_turu, self.islem_turu)

    @property
    def islem_icon(self):
        """İşlem simgesi (timeline görünümü için)."""
        return {
            'olusturma': 'bi-plus-circle text-success',
            'durum_degisikligi': 'bi-arrow-repeat text-primary',
            'yonlendirme': 'bi-arrow-right-circle text-info',
            'yorum': 'bi-chat-dots text-warning',
            'sms_bildirim': 'bi-phone text-success',
            'eposta_bildirim': 'bi-envelope text-primary',
            'is_emri_donusumu': 'bi-clipboard2-check text-danger',
            'memnuniyet_puani': 'bi-star text-warning',
        }.get(self.islem_turu, 'bi-circle text-secondary')

    def __repr__(self):
        return f'<TalepGecmisi T:{self.talep_id} — {self.islem_turu}>'
