"""
FDYS — İSG (İş Sağlığı ve Güvenliği) Modeli
Faz 4 — Kurumsal Seviye
"""

from datetime import datetime, timezone
from app.extensions import db


class IsKazasi(db.Model):
    __tablename__ = 'is_kazasi'
    __table_args__ = (
        db.Index('ix_kaza_calisan_tarih', 'calisan_id', 'tarih'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    olay_no = db.Column(db.String(50), unique=True, nullable=True, index=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='RESTRICT'), nullable=False)
    tarih = db.Column(db.DateTime, nullable=False, index=True)
    vardiya = db.Column(db.String(20), nullable=True)
    yer = db.Column(db.String(100), nullable=False)
    yaralanma_tipi = db.Column(db.String(100), nullable=False)
    uzuv = db.Column(db.String(100), nullable=True)  # Etkilenen uzuv
    siddet = db.Column(db.String(20), nullable=False)  # hafif|orta|agir|olumcul
    kaza_sekli = db.Column(db.String(100), nullable=True)  # dusme|sikisma|kesilme vb.
    kok_neden = db.Column(db.Text, nullable=True)
    aciklama = db.Column(db.Text, nullable=False)
    duzeltici_faaliyet = db.Column(db.Text, nullable=True)
    kayip_gun = db.Column(db.Integer, default=0)
    ramak_kala = db.Column(db.Boolean, default=False)
    durum = db.Column(db.String(20), default='acik')  # acik|arastiriliyor|kapandi
    bildiren_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    calisan = db.relationship('Calisan', backref='kaza_kayitlari', lazy='joined')
    bildiren = db.relationship('Kullanici', backref='bildirilen_kazalar', lazy='joined')

    def __repr__(self):
        return f'<IsKazasi {self.olay_no or self.id} — {self.siddet}>'


class RiskDegerlendirme(db.Model):
    __tablename__ = 'risk_degerlendirme'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bolum = db.Column(db.String(100), nullable=False)
    faaliyet = db.Column(db.String(150), nullable=True)  # Hangi iş yaparken
    tehlike = db.Column(db.Text, nullable=False)
    risk = db.Column(db.Text, nullable=True)  # Tehlikenin yaratacağı risk
    olasilik = db.Column(db.Integer, nullable=False)  # 1-5 (5x5 matris için)
    siddet = db.Column(db.Integer, nullable=False)  # 1-5
    mevcut_onlem = db.Column(db.Text, nullable=True)
    risk_puani = db.Column(db.Integer, nullable=True)  # olasilik × siddet
    risk_seviyesi = db.Column(db.String(20), nullable=True)  # dusuk|orta|yuksek|kritik
    ek_onlem = db.Column(db.Text, nullable=True)
    sorumlu = db.Column(db.String(100), nullable=True)
    hedef_tarih = db.Column(db.Date, nullable=True)
    durum = db.Column(db.String(20), default='acik')  # acik|devam|kapandi
    gozden_gecirme_tarihi = db.Column(db.Date, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def hesapla_risk(self):
        """Risk puanı = Olasılık × Şiddet (5x5 Matris)."""
        self.risk_puani = self.olasilik * self.siddet
        if self.risk_puani <= 6:
            self.risk_seviyesi = 'dusuk'
        elif self.risk_puani <= 12:
            self.risk_seviyesi = 'orta'
        elif self.risk_puani <= 19:
            self.risk_seviyesi = 'yuksek'
        else:
            self.risk_seviyesi = 'kritik'
        return self.risk_puani

    def __repr__(self):
        return f'<RiskDegerlendirme {self.bolum} — {self.risk_seviyesi}>'


class IsgEgitimi(db.Model):
    __tablename__ = 'isg_egitimi'
    __table_args__ = (
        db.Index('ix_egitim_calisan_tarih', 'calisan_id', 'egitim_tarihi'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False)
    egitim_kategorisi = db.Column(db.String(50), nullable=True)  # temel_isg|ilkyardim|yangin|mesleki
    egitim_adi = db.Column(db.String(200), nullable=False)
    egitim_suresi = db.Column(db.Numeric(4, 1), nullable=True)  # Saat cinsinden
    egitim_tarihi = db.Column(db.Date, nullable=False)
    gecerlilik_bitis = db.Column(db.Date, nullable=True)
    sertifika_no = db.Column(db.String(50), nullable=True)
    egitmen = db.Column(db.String(100), nullable=True)
    durum = db.Column(db.String(20), default='gecerli')  # gecerli|suresi_doldu|iptal
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    calisan = db.relationship('Calisan', backref='isg_egitimleri', lazy='joined')

    def __repr__(self):
        return f'<IsgEgitimi {self.egitim_adi}>'


class SaglikMuayenesi(db.Model):
    """
    Çalışan periyodik sağlık muayenesi takibi.

    Muayene türleri:
        - ise_giris: İşe giriş sağlık muayenesi
        - periyodik: Periyodik (yıllık/6 aylık) sağlık kontrolleri
        - ozel: Özel amaçlı muayene (çalışan talebi veya olay sonrası)
        - ayrilma: İşten ayrılış sağlık muayenesi

    Sonuçlar:
        - uygun: Pozisyon için tamamen uygun
        - sinirli_uygun: Kısıtlamalarla uygun
        - uygun_degil: Pozisyon için uygun değil
    """
    __tablename__ = 'saglik_muayenesi'
    __table_args__ = (
        db.Index('ix_muayene_calisan_tarih', 'calisan_id', 'muayene_tarihi'),
    )

    # ── Muayene Türü Sabitleri ──
    TUR_ISE_GIRIS = 'ise_giris'
    TUR_PERIYODIK = 'periyodik'
    TUR_OZEL = 'ozel'
    TUR_AYRILMA = 'ayrilma'

    TURLER = {
        TUR_ISE_GIRIS: 'İşe Giriş Muayenesi',
        TUR_PERIYODIK: 'Periyodik Muayene',
        TUR_OZEL: 'Özel Muayene',
        TUR_AYRILMA: 'İşten Ayrılış Muayenesi',
    }

    # ── Sonuç Sabitleri ──
    SONUC_UYGUN = 'uygun'
    SONUC_SINIRLI = 'sinirli_uygun'
    SONUC_UYGUN_DEGIL = 'uygun_degil'

    SONUCLAR = {
        SONUC_UYGUN: 'Uygun',
        SONUC_SINIRLI: 'Sınırlı Uygun',
        SONUC_UYGUN_DEGIL: 'Uygun Değil',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    muayene_turu = db.Column(db.String(30), nullable=False, default=TUR_PERIYODIK)
    muayene_tarihi = db.Column(db.Date, nullable=False)
    sonraki_muayene_tarihi = db.Column(db.Date, nullable=True)
    hastane_adi = db.Column(db.String(200), nullable=True)
    doktor_adi = db.Column(db.String(150), nullable=True)
    sonuc = db.Column(db.String(30), nullable=False, default=SONUC_UYGUN)
    kisitlamalar = db.Column(db.Text, nullable=True)  # "Gece vardiyasında çalışamaz" vb.
    rapor_dosya_id = db.Column(db.Integer, db.ForeignKey('dosya_eki.id', ondelete='SET NULL'), nullable=True)
    hatirlatma_gun = db.Column(db.Integer, default=30)  # Sonraki muayeneden kaç gün önce uyarı
    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('saglik_muayeneleri', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))
    rapor_dosya = db.relationship('DosyaEki', backref='muayene_kayitlari', lazy='joined')

    @property
    def tur_adi(self):
        return self.TURLER.get(self.muayene_turu, self.muayene_turu)

    @property
    def sonuc_adi(self):
        return self.SONUCLAR.get(self.sonuc, self.sonuc)

    @property
    def muayene_gecikti_mi(self):
        """Sonraki muayene tarihi geçti mi?"""
        from datetime import date
        if not self.sonraki_muayene_tarihi:
            return False
        return date.today() > self.sonraki_muayene_tarihi

    @property
    def muayene_yaklasıyor_mu(self):
        """Sonraki muayene tarihi yaklaşıyor mu? (hatırlatma gün aralığında)"""
        from datetime import date, timedelta
        if not self.sonraki_muayene_tarihi:
            return False
        hatirlatma = self.hatirlatma_gun or 30
        return date.today() >= (self.sonraki_muayene_tarihi - timedelta(days=hatirlatma))

    def __repr__(self):
        return f'<SaglikMuayenesi {self.muayene_turu} — {self.sonuc}>'


class IsgDokumani(db.Model):
    """
    İSG tutanak, form ve saha raporları arşivi.

    Kategoriler:
        - tutanak: Olay/toplantı/tespit tutanağı
        - form: İSG formları (risk değerlendirme, acil durum, vb.)
        - saha_raporu: Saha denetim ve gözlem raporları
        - talimat: İş güvenliği talimatları
        - prosedur: İSG prosedür dokümanları
        - egitim_materyali: Eğitim sunumları ve materyalleri
    """
    __tablename__ = 'isg_dokumani'
    __table_args__ = (
        db.Index('ix_isg_dok_kategori_tarih', 'kategori', 'olusturma_tarihi'),
    )

    # ── Kategori Sabitleri ──
    KAT_TUTANAK = 'tutanak'
    KAT_FORM = 'form'
    KAT_SAHA_RAPORU = 'saha_raporu'
    KAT_TALIMAT = 'talimat'
    KAT_PROSEDUR = 'prosedur'
    KAT_EGITIM_MATERYALI = 'egitim_materyali'

    KATEGORILER = {
        KAT_TUTANAK: 'Tutanak',
        KAT_FORM: 'Form',
        KAT_SAHA_RAPORU: 'Saha Raporu',
        KAT_TALIMAT: 'Talimat',
        KAT_PROSEDUR: 'Prosedür',
        KAT_EGITIM_MATERYALI: 'Eğitim Materyali',
    }

    # ── Onay Durumu Sabitleri ──
    ONAY_TASLAK = 'taslak'
    ONAY_BEKLIYOR = 'onay_bekliyor'
    ONAY_ONAYLANDI = 'onaylandi'
    ONAY_REDDEDILDI = 'reddedildi'

    ONAY_DURUMLARI = {
        ONAY_TASLAK: 'Taslak',
        ONAY_BEKLIYOR: 'Onay Bekliyor',
        ONAY_ONAYLANDI: 'Onaylandı',
        ONAY_REDDEDILDI: 'Reddedildi',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    baslik = db.Column(db.String(200), nullable=False)
    kategori = db.Column(db.String(30), nullable=False, default=KAT_TUTANAK)
    aciklama = db.Column(db.Text, nullable=True)
    dosya_eki_id = db.Column(db.Integer, db.ForeignKey('dosya_eki.id', ondelete='SET NULL'), nullable=True)
    versiyon = db.Column(db.Integer, default=1)
    gecerlilik_tarihi = db.Column(db.Date, nullable=True)
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onay_durumu = db.Column(db.String(20), default=ONAY_TASLAK)
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onay_tarihi = db.Column(db.DateTime, nullable=True)
    red_nedeni = db.Column(db.Text, nullable=True)
    ilgili_bolum = db.Column(db.String(100), nullable=True)  # İlgili bölüm/departman
    etiketler = db.Column(db.JSON, default=list)  # ["yangın", "acil_durum", "kimyasal"]
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    dosya_eki = db.relationship('DosyaEki', backref='isg_dokumanlari', lazy='joined')
    sorumlu = db.relationship('Kullanici', foreign_keys=[sorumlu_id],
                              backref='isg_sorumlu_dokumanlar', lazy='joined')
    onaylayan = db.relationship('Kullanici', foreign_keys=[onaylayan_id],
                                backref='isg_onaylanan_dokumanlar', lazy='joined')

    @property
    def kategori_adi(self):
        return self.KATEGORILER.get(self.kategori, self.kategori)

    @property
    def onay_durumu_adi(self):
        return self.ONAY_DURUMLARI.get(self.onay_durumu, self.onay_durumu)

    @property
    def gecerliligi_doldu_mu(self):
        """Doküman geçerlilik tarihi geçti mi?"""
        from datetime import date
        if not self.gecerlilik_tarihi:
            return False
        return date.today() > self.gecerlilik_tarihi

    def __repr__(self):
        return f'<IsgDokumani {self.baslik} — v{self.versiyon}>'
