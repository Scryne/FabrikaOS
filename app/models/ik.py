"""
FDYS — İK (İnsan Kaynakları) Modeli
Faz 1 — Tam Genişletme

Savunma/Tutanak, Fazla Mesai, Sertifika Takip, Maaş Skalası,
Zimmet Kaydı ve Giriş/Çıkış Evrak tablolarını içerir.
Tüm tablolar Calisan modeline CASCADE ile bağlıdır.
"""

from datetime import datetime, timezone
from app.extensions import db


class SavunmaTutanak(db.Model):
    """
    Savunma, tutanak, uyarı, ihtar ve disiplin kurulu kararları.

    Türler:
        - savunma: Çalışandan savunma isteme
        - tutanak: Olay tespit tutanağı
        - uyari: Sözlü/yazılı uyarı
        - ihtar: Resmi ihtar
        - disiplin_kurulu: Disiplin kurulu kararı
    """
    __tablename__ = 'savunma_tutanak'
    __table_args__ = (
        db.Index('ix_savunma_calisan_tarih', 'calisan_id', 'olusturma_tarihi'),
    )

    # ── Tür Sabitleri ──
    TUR_SAVUNMA = 'savunma'
    TUR_TUTANAK = 'tutanak'
    TUR_UYARI = 'uyari'
    TUR_IHTAR = 'ihtar'
    TUR_DISIPLIN_KURULU = 'disiplin_kurulu'

    TURLER = {
        TUR_SAVUNMA: 'Savunma',
        TUR_TUTANAK: 'Tutanak',
        TUR_UYARI: 'Uyarı',
        TUR_IHTAR: 'İhtar',
        TUR_DISIPLIN_KURULU: 'Disiplin Kurulu',
    }

    # ── Durum Sabitleri ──
    DURUM_ACIK = 'acik'
    DURUM_KAPATILDI = 'kapatildi'
    DURUM_ITIRAZ = 'itiraz_edildi'

    DURUMLAR = {
        DURUM_ACIK: 'Açık',
        DURUM_KAPATILDI: 'Kapatıldı',
        DURUM_ITIRAZ: 'İtiraz Edildi',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    tur = db.Column(db.String(30), nullable=False, default=TUR_SAVUNMA)
    konu = db.Column(db.String(200), nullable=False)
    icerik = db.Column(db.Text, nullable=False)
    karar = db.Column(db.Text, nullable=True)
    karar_tarihi = db.Column(db.Date, nullable=True)
    olusturan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    taniklar = db.Column(db.JSON, default=list)  # [{"ad_soyad": "...", "sicil_no": "..."}]
    dosya_ekleri = db.Column(db.JSON, default=list)  # Eklenen dosya ID'leri
    durum = db.Column(db.String(20), default=DURUM_ACIK)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('savunma_tutanaklar', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))
    olusturan = db.relationship('Kullanici', foreign_keys=[olusturan_id],
                                backref='olusturulan_savunmalar', lazy='joined')

    @property
    def tur_adi(self):
        return self.TURLER.get(self.tur, self.tur)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    def __repr__(self):
        return f'<SavunmaTutanak {self.tur} — {self.konu[:30]}>'


class FazlaMesai(db.Model):
    """
    Fazla mesai kayıtları ve onay akışı.

    Mesai türleri:
        - hafta_ici: Hafta içi fazla mesai (1.5x)
        - hafta_sonu: Hafta sonu mesai (2.0x)
        - resmi_tatil: Resmi tatil mesaisi (2.0x)
    """
    __tablename__ = 'fazla_mesai'
    __table_args__ = (
        db.Index('ix_mesai_calisan_tarih', 'calisan_id', 'tarih'),
    )

    # ── Mesai Türü Sabitleri ──
    MESAI_HAFTA_ICI = 'hafta_ici'
    MESAI_HAFTA_SONU = 'hafta_sonu'
    MESAI_RESMI_TATIL = 'resmi_tatil'

    MESAI_TURLERI = {
        MESAI_HAFTA_ICI: 'Hafta İçi',
        MESAI_HAFTA_SONU: 'Hafta Sonu',
        MESAI_RESMI_TATIL: 'Resmi Tatil',
    }

    # ── Varsayılan Ücret Çarpanları ──
    UCRET_CARPANLARI = {
        MESAI_HAFTA_ICI: 1.5,
        MESAI_HAFTA_SONU: 2.0,
        MESAI_RESMI_TATIL: 2.0,
    }

    # ── Onay Durumları ──
    ONAY_BEKLIYOR = 'bekliyor'
    ONAY_ONAYLANDI = 'onaylandi'
    ONAY_REDDEDILDI = 'reddedildi'

    ONAY_DURUMLARI = {
        ONAY_BEKLIYOR: 'Bekliyor',
        ONAY_ONAYLANDI: 'Onaylandı',
        ONAY_REDDEDILDI: 'Reddedildi',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    tarih = db.Column(db.Date, nullable=False, index=True)
    baslangic_saati = db.Column(db.Time, nullable=False)
    bitis_saati = db.Column(db.Time, nullable=False)
    toplam_saat = db.Column(db.Numeric(4, 1), nullable=True)
    mesai_turu = db.Column(db.String(20), nullable=False, default=MESAI_HAFTA_ICI)
    neden = db.Column(db.Text, nullable=True)
    onay_durumu = db.Column(db.String(20), default=ONAY_BEKLIYOR)
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onay_tarihi = db.Column(db.DateTime, nullable=True)
    ucret_carpani = db.Column(db.Numeric(3, 1), nullable=True)  # 1.5x, 2.0x vb.
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('fazla_mesailer', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))
    onaylayan = db.relationship('Kullanici', foreign_keys=[onaylayan_id],
                                backref='onaylanan_mesailer', lazy='joined')

    @property
    def mesai_turu_adi(self):
        return self.MESAI_TURLERI.get(self.mesai_turu, self.mesai_turu)

    @property
    def onay_durumu_adi(self):
        return self.ONAY_DURUMLARI.get(self.onay_durumu, self.onay_durumu)

    def hesapla_toplam_saat(self):
        """Başlangıç ve bitiş saatinden toplam saati hesaplar."""
        from datetime import timedelta
        if self.baslangic_saati and self.bitis_saati:
            baslangic = timedelta(hours=self.baslangic_saati.hour, minutes=self.baslangic_saati.minute)
            bitis = timedelta(hours=self.bitis_saati.hour, minutes=self.bitis_saati.minute)
            fark = bitis - baslangic
            if fark.total_seconds() < 0:
                fark += timedelta(hours=24)  # Gece yarısını geçen mesai
            self.toplam_saat = round(fark.total_seconds() / 3600, 1)
        return self.toplam_saat

    def varsayilan_carpan_belirle(self):
        """Mesai türüne göre varsayılan ücret çarpanını belirler."""
        self.ucret_carpani = self.UCRET_CARPANLARI.get(self.mesai_turu, 1.5)
        return self.ucret_carpani

    def __repr__(self):
        return f'<FazlaMesai {self.tarih} — {self.toplam_saat}h>'


class SertifikaTakip(db.Model):
    """
    Çalışan sertifika ve yetkinlik belgesi takibi.

    Kategoriler:
        - mesleki: Mesleki yeterlilik belgeleri
        - teknik: Teknik eğitim sertifikaları
        - isg: İSG sertifikaları
        - dil: Yabancı dil belgeleri
        - bilgi_teknolojileri: BT sertifikaları
        - diger: Diğer
    """
    __tablename__ = 'sertifika_takip'
    __table_args__ = (
        db.Index('ix_sertifika_calisan_bitis', 'calisan_id', 'gecerlilik_bitis'),
    )

    # ── Kategori Sabitleri ──
    KAT_MESLEKI = 'mesleki'
    KAT_TEKNIK = 'teknik'
    KAT_ISG = 'isg'
    KAT_DIL = 'dil'
    KAT_BT = 'bilgi_teknolojileri'
    KAT_DIGER = 'diger'

    KATEGORILER = {
        KAT_MESLEKI: 'Mesleki Yeterlilik',
        KAT_TEKNIK: 'Teknik Eğitim',
        KAT_ISG: 'İSG',
        KAT_DIL: 'Yabancı Dil',
        KAT_BT: 'Bilgi Teknolojileri',
        KAT_DIGER: 'Diğer',
    }

    # ── Durum Sabitleri ──
    DURUM_GECERLI = 'gecerli'
    DURUM_SURESI_DOLDU = 'suresi_doldu'
    DURUM_IPTAL = 'iptal'

    DURUMLAR = {
        DURUM_GECERLI: 'Geçerli',
        DURUM_SURESI_DOLDU: 'Süresi Doldu',
        DURUM_IPTAL: 'İptal',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    sertifika_adi = db.Column(db.String(200), nullable=False)
    veren_kurum = db.Column(db.String(150), nullable=False)
    sertifika_no = db.Column(db.String(100), nullable=True)
    kategori = db.Column(db.String(30), nullable=False, default=KAT_MESLEKI)
    verilis_tarihi = db.Column(db.Date, nullable=False)
    gecerlilik_bitis = db.Column(db.Date, nullable=True)  # NULL = süresiz
    hatirlatma_gun = db.Column(db.Integer, default=30)  # Süre dolmadan kaç gün önce uyarı
    dosya_eki_id = db.Column(db.Integer, db.ForeignKey('dosya_eki.id', ondelete='SET NULL'), nullable=True)
    durum = db.Column(db.String(20), default=DURUM_GECERLI)
    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('sertifikalar', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))
    dosya_eki = db.relationship('DosyaEki', backref='sertifika_kayitlari', lazy='joined')

    @property
    def kategori_adi(self):
        return self.KATEGORILER.get(self.kategori, self.kategori)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def suresi_doluyor_mu(self):
        """Sertifika geçerlilik süresi dolmak üzere mi?"""
        from datetime import date, timedelta
        if not self.gecerlilik_bitis:
            return False
        return date.today() >= (self.gecerlilik_bitis - timedelta(days=self.hatirlatma_gun or 30))

    @property
    def suresi_doldu_mu(self):
        """Sertifika geçerlilik süresi doldu mu?"""
        from datetime import date
        if not self.gecerlilik_bitis:
            return False
        return date.today() > self.gecerlilik_bitis

    def __repr__(self):
        return f'<SertifikaTakip {self.sertifika_adi} — {self.durum}>'


class MaasSkalasi(db.Model):
    """
    Yıl/dönem bazında maaş skalası takibi.
    Her çalışanın maaş değişiklik geçmişi tutulur.
    """
    __tablename__ = 'maas_skalasi'
    __table_args__ = (
        db.Index('ix_maas_calisan_donem', 'calisan_id', 'donem_baslangic'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    donem_baslangic = db.Column(db.Date, nullable=False)
    donem_bitis = db.Column(db.Date, nullable=True)  # NULL = devam eden dönem
    brut_maas = db.Column(db.Numeric(12, 2), nullable=False)
    net_maas = db.Column(db.Numeric(12, 2), nullable=True)
    ek_odeme = db.Column(db.Numeric(10, 2), default=0)  # Prim, ikramiye vb.
    ek_odeme_aciklama = db.Column(db.String(200), nullable=True)
    artis_orani = db.Column(db.Numeric(5, 2), nullable=True)  # Önceki döneme göre % artış
    derece = db.Column(db.Integer, nullable=True)
    kademe = db.Column(db.Integer, nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('maas_gecmisi', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))

    @property
    def guncel_mi(self):
        """Bu maaş kaydı güncel (devam eden dönem) mi?"""
        return self.donem_bitis is None

    def __repr__(self):
        return f'<MaasSkalasi {self.donem_baslangic} — {self.brut_maas}₺>'


class ZimmetKaydi(db.Model):
    """
    Personele teslim edilen demirbaş/cihaz takibi.

    Kategoriler:
        - bilisim: Bilişim ekipmanları (laptop, telefon vb.)
        - otopark: Otopark kartı, kumanda
        - anahtar: Anahtar, giriş kartı
        - kiyafet: İş kıyafeti, KKD
        - alet: Alet, ekipman
        - diger: Diğer
    """
    __tablename__ = 'zimmet_kaydi'
    __table_args__ = (
        db.Index('ix_zimmet_calisan_durum', 'calisan_id', 'durum'),
    )

    # ── Kategori Sabitleri ──
    KAT_BILISIM = 'bilisim'
    KAT_OTOPARK = 'otopark'
    KAT_ANAHTAR = 'anahtar'
    KAT_KIYAFET = 'kiyafet'
    KAT_ALET = 'alet'
    KAT_DIGER = 'diger'

    KATEGORILER = {
        KAT_BILISIM: 'Bilişim',
        KAT_OTOPARK: 'Otopark',
        KAT_ANAHTAR: 'Anahtar / Kart',
        KAT_KIYAFET: 'Kıyafet / KKD',
        KAT_ALET: 'Alet / Ekipman',
        KAT_DIGER: 'Diğer',
    }

    # ── Durum Sabitleri ──
    DURUM_TESLIM_EDILDI = 'teslim_edildi'
    DURUM_IADE_EDILDI = 'iade_edildi'
    DURUM_KAYIP = 'kayip'
    DURUM_HASAR = 'hasar'

    DURUMLAR = {
        DURUM_TESLIM_EDILDI: 'Teslim Edildi',
        DURUM_IADE_EDILDI: 'İade Edildi',
        DURUM_KAYIP: 'Kayıp',
        DURUM_HASAR: 'Hasarlı',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    demirbas_adi = db.Column(db.String(200), nullable=False)
    demirbas_kodu = db.Column(db.String(50), nullable=True)  # Barkod/envanter kodu
    seri_no = db.Column(db.String(100), nullable=True)
    kategori = db.Column(db.String(20), nullable=False, default=KAT_BILISIM)
    teslim_tarihi = db.Column(db.Date, nullable=False)
    iade_tarihi = db.Column(db.Date, nullable=True)  # NULL = iade edilmemiş
    durum = db.Column(db.String(20), default=DURUM_TESLIM_EDILDI)
    deger = db.Column(db.Numeric(10, 2), nullable=True)  # Tahmini değer
    notlar = db.Column(db.Text, nullable=True)
    teslim_alan_imza = db.Column(db.Boolean, default=False)  # İmza alındı mı
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('zimmet_kayitlari', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))

    @property
    def kategori_adi(self):
        return self.KATEGORILER.get(self.kategori, self.kategori)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def iade_edilmedi_mi(self):
        """Zimmet iade edilmemiş mi?"""
        return self.durum == self.DURUM_TESLIM_EDILDI and self.iade_tarihi is None

    def __repr__(self):
        return f'<ZimmetKaydi {self.demirbas_adi} — {self.durum}>'


class GirisCikisEvrak(db.Model):
    """
    İşe giriş/çıkış evrakları ve süreç takibi.
    Her çalışan için standart evrak listesi oluşturulur.
    """
    __tablename__ = 'giris_cikis_evrak'
    __table_args__ = (
        db.Index('ix_evrak_calisan_tur', 'calisan_id', 'evrak_turu'),
    )

    # ── Evrak Türü Sabitleri ──
    EVRAK_ISE_GIRIS = 'ise_giris'
    EVRAK_ISTEN_CIKIS = 'isten_cikis'

    EVRAK_TURLERI = {
        EVRAK_ISE_GIRIS: 'İşe Giriş',
        EVRAK_ISTEN_CIKIS: 'İşten Çıkış',
    }

    # ── Durum Sabitleri ──
    DURUM_BEKLIYOR = 'bekliyor'
    DURUM_TAMAMLANDI = 'tamamlandi'
    DURUM_EKSIK = 'eksik'

    DURUMLAR = {
        DURUM_BEKLIYOR: 'Bekliyor',
        DURUM_TAMAMLANDI: 'Tamamlandı',
        DURUM_EKSIK: 'Eksik',
    }

    # ── Standart Evrak Şablonları ──
    ISE_GIRIS_EVRAKLARI = [
        'Nüfus Cüzdanı Fotokopisi',
        'Diploma Fotokopisi',
        'İkametgâh Belgesi',
        'Adli Sicil Kaydı',
        'SGK İşe Giriş Bildirgesi',
        'Sağlık Raporu',
        'Kan Grubu Belgesi',
        'Vesikalık Fotoğraf (2 adet)',
        'Askerlik Terhis/Tecil Belgesi',
        'İş Sözleşmesi',
        'KVKK Aydınlatma Metni',
        'Zimmet Teslim Tutanağı',
    ]

    ISTEN_CIKIS_EVRAKLARI = [
        'İstifa Dilekçesi / Fesih Bildirimi',
        'İbraname',
        'SGK İşten Ayrılış Bildirgesi',
        'Zimmet İade Tutanağı',
        'İş Deneyim Belgesi',
        'Kıdem/İhbar Tazminatı Hesabı',
    ]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisan.id', ondelete='CASCADE'), nullable=False, index=True)
    evrak_turu = db.Column(db.String(20), nullable=False, default=EVRAK_ISE_GIRIS)
    evrak_adi = db.Column(db.String(200), nullable=False)
    durum = db.Column(db.String(20), default=DURUM_BEKLIYOR)
    tamamlama_tarihi = db.Column(db.Date, nullable=True)
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    dosya_eki_id = db.Column(db.Integer, db.ForeignKey('dosya_eki.id', ondelete='SET NULL'), nullable=True)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    calisan = db.relationship('Calisan', backref=db.backref('giris_cikis_evraklar', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True))
    sorumlu = db.relationship('Kullanici', foreign_keys=[sorumlu_id],
                              backref='sorumlu_evraklar', lazy='joined')
    dosya_eki = db.relationship('DosyaEki', backref='evrak_kayitlari', lazy='joined')

    @property
    def evrak_turu_adi(self):
        return self.EVRAK_TURLERI.get(self.evrak_turu, self.evrak_turu)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @classmethod
    def standart_evrak_olustur(cls, calisan_id, evrak_turu):
        """Standart evrak listesini toplu oluşturur."""
        evrak_listesi = cls.ISE_GIRIS_EVRAKLARI if evrak_turu == cls.EVRAK_ISE_GIRIS else cls.ISTEN_CIKIS_EVRAKLARI
        evraklar = []
        for evrak_adi in evrak_listesi:
            evrak = cls(
                calisan_id=calisan_id,
                evrak_turu=evrak_turu,
                evrak_adi=evrak_adi,
                durum=cls.DURUM_BEKLIYOR,
            )
            evraklar.append(evrak)
        return evraklar

    def __repr__(self):
        return f'<GirisCikisEvrak {self.evrak_turu} — {self.evrak_adi}>'
