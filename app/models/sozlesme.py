"""
FDYS — Sözleşme, Kira Kontrat & Sigorta Poliçe Modelleri
Faz 3 — Sözleşme Yönetimi

Ana sözleşme tablosu, kira kontratı detayları, sigorta poliçesi
ve standart metin şablonlarını içerir.
CRM modülüne (Ortak & Firma) bağımlıdır.
"""

from datetime import datetime, timezone, date
from app.extensions import db


class Sozlesme(db.Model):
    """
    Ana sözleşme tablosu.
    Polimorfik yapı: taraf_tip ('ortak' | 'firma') + taraf_id ile CRM'e bağlanır.

    Sözleşme Türleri:
        - kira: Kira sözleşmesi (KiraKontrat ile detaylandırılır)
        - hizmet: Hizmet sözleşmesi
        - bakim: Bakım sözleşmesi
        - sigorta: Sigorta poliçesi (SigortaPolice ile detaylandırılır)
        - diger: Diğer sözleşme tipleri
    """
    __tablename__ = 'sozlesme'
    __table_args__ = (
        db.Index('ix_sozlesme_tur', 'tur'),
        db.Index('ix_sozlesme_durum', 'durum'),
        db.Index('ix_sozlesme_taraf', 'taraf_tip', 'taraf_id'),
        db.Index('ix_sozlesme_bitis', 'bitis_tarihi'),
    )

    # ── Sözleşme Türü Sabitleri ──
    TUR_KIRA = 'kira'
    TUR_HIZMET = 'hizmet'
    TUR_BAKIM = 'bakim'
    TUR_SIGORTA = 'sigorta'
    TUR_DIGER = 'diger'

    TURLER = {
        TUR_KIRA: 'Kira Sözleşmesi',
        TUR_HIZMET: 'Hizmet Sözleşmesi',
        TUR_BAKIM: 'Bakım Sözleşmesi',
        TUR_SIGORTA: 'Sigorta Poliçesi',
        TUR_DIGER: 'Diğer',
    }

    # ── Taraf Tipi Sabitleri ──
    TARAF_ORTAK = 'ortak'
    TARAF_FIRMA = 'firma'

    TARAF_TIPLERI = {
        TARAF_ORTAK: 'Ortak',
        TARAF_FIRMA: 'Firma',
    }

    # ── Ödeme Periyodu Sabitleri ──
    PERIYOD_AYLIK = 'aylik'
    PERIYOD_3_AYLIK = '3_aylik'
    PERIYOD_6_AYLIK = '6_aylik'
    PERIYOD_YILLIK = 'yillik'
    PERIYOD_TEK_SEFER = 'tek_sefer'

    ODEME_PERIYOTLARI = {
        PERIYOD_AYLIK: 'Aylık',
        PERIYOD_3_AYLIK: '3 Aylık',
        PERIYOD_6_AYLIK: '6 Aylık',
        PERIYOD_YILLIK: 'Yıllık',
        PERIYOD_TEK_SEFER: 'Tek Seferlik',
    }

    # ── Para Birimi Sabitleri ──
    PARA_TL = 'TL'
    PARA_USD = 'USD'
    PARA_EUR = 'EUR'

    PARA_BIRIMLERI = {
        PARA_TL: '₺ TL',
        PARA_USD: '$ USD',
        PARA_EUR: '€ EUR',
    }

    # ── Durum Sabitleri ──
    DURUM_AKTIF = 'aktif'
    DURUM_SONA_ERDI = 'sona_erdi'
    DURUM_IPTAL = 'iptal'
    DURUM_ASKIDA = 'askida'

    DURUMLAR = {
        DURUM_AKTIF: 'Aktif',
        DURUM_SONA_ERDI: 'Sona Erdi',
        DURUM_IPTAL: 'İptal Edildi',
        DURUM_ASKIDA: 'Askıda',
    }

    DURUM_RENKLERI = {
        DURUM_AKTIF: 'success',
        DURUM_SONA_ERDI: 'secondary',
        DURUM_IPTAL: 'danger',
        DURUM_ASKIDA: 'warning',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sozlesme_no = db.Column(db.String(30), unique=True, nullable=False, index=True)

    # Sözleşme türü
    tur = db.Column(db.String(20), nullable=False, default=TUR_KIRA)

    # Polimorfik taraf bilgisi (CRM bağlantısı)
    taraf_tip = db.Column(db.String(10), nullable=False, default=TARAF_ORTAK)
    taraf_id = db.Column(db.Integer, nullable=False)

    # Temel bilgiler
    baslik = db.Column(db.String(300), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)

    # Tarih bilgileri
    baslangic_tarihi = db.Column(db.Date, nullable=False)
    bitis_tarihi = db.Column(db.Date, nullable=True)

    # Mali bilgiler
    tutar = db.Column(db.Numeric(14, 2), nullable=True)
    para_birimi = db.Column(db.String(5), nullable=False, default=PARA_TL)
    odeme_periyodu = db.Column(db.String(20), nullable=True, default=PERIYOD_AYLIK)

    # Otomatik yenileme
    otomatik_yenileme = db.Column(db.Boolean, default=False, nullable=False)
    yenileme_suresi_ay = db.Column(db.Integer, nullable=True)  # Ay cinsinden yenileme süresi

    # Hatırlatma
    hatirlatma_gun = db.Column(db.Integer, nullable=True, default=30)  # Bitiş öncesi kaç gün

    # Standart metin şablonu bağlantısı
    standart_metin_id = db.Column(db.Integer, db.ForeignKey('standart_metin.id', ondelete='SET NULL'), nullable=True)

    # Durum
    durum = db.Column(db.String(20), nullable=False, default=DURUM_AKTIF)
    notlar = db.Column(db.Text, nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # ── İlişkiler ──
    kira_kontrat = db.relationship('KiraKontrat', backref='sozlesme', uselist=False,
                                    cascade='all, delete-orphan', passive_deletes=True)
    sigorta_police = db.relationship('SigortaPolice', backref='bagli_sozlesme', uselist=False,
                                      cascade='all, delete-orphan', passive_deletes=True)
    standart_metin = db.relationship('StandartMetin', foreign_keys=[standart_metin_id],
                                      backref='bagli_sozlesmeler', lazy='joined')

    # ── Property'ler ──
    @property
    def tur_adi(self):
        return self.TURLER.get(self.tur, self.tur)

    @property
    def taraf_tip_adi(self):
        return self.TARAF_TIPLERI.get(self.taraf_tip, self.taraf_tip)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def durum_renk(self):
        return self.DURUM_RENKLERI.get(self.durum, 'secondary')

    @property
    def odeme_periyodu_adi(self):
        return self.ODEME_PERIYOTLARI.get(self.odeme_periyodu, self.odeme_periyodu or '—')

    @property
    def para_birimi_adi(self):
        return self.PARA_BIRIMLERI.get(self.para_birimi, self.para_birimi)

    @property
    def kalan_gun(self):
        """Sözleşme bitiş tarihine kalan gün sayısı."""
        if not self.bitis_tarihi:
            return None
        bugun = date.today()
        fark = (self.bitis_tarihi - bugun).days
        return fark

    @property
    def suresi_dolmak_uzere(self):
        """Hatırlatma günü içinde mi?"""
        kalan = self.kalan_gun
        if kalan is None:
            return False
        hatirlatma = self.hatirlatma_gun or 30
        return 0 < kalan <= hatirlatma

    @property
    def suresi_doldu(self):
        """Süresi dolmuş mu?"""
        kalan = self.kalan_gun
        if kalan is None:
            return False
        return kalan <= 0

    @property
    def taraf_bilgi(self):
        """Taraf adını döndürür (ortak ad_soyad veya firma ünvan)."""
        try:
            if self.taraf_tip == self.TARAF_ORTAK:
                from app.models.crm import Ortak
                ortak = db.session.get(Ortak, self.taraf_id)
                return ortak.ad_soyad if ortak else '—'
            else:
                from app.models.crm import Firma
                firma = db.session.get(Firma, self.taraf_id)
                return firma.unvan if firma else '—'
        except Exception:
            return '—'

    @property
    def tutar_formatli(self):
        """Tutarı para birimi ile formatlar."""
        if self.tutar is None:
            return '—'
        sembol = {'TL': '₺', 'USD': '$', 'EUR': '€'}.get(self.para_birimi, self.para_birimi)
        return f'{sembol} {self.tutar:,.2f}'

    def __repr__(self):
        return f'<Sozlesme {self.sozlesme_no} — {self.baslik[:50]}>'


class KiraKontrat(db.Model):
    """
    Kira kontratı detayları.
    Sozlesme tablosuna 1:1 ilişki ile bağlıdır (tur='kira').

    Artış Türleri:
        - tufe: TÜFE bazlı artış
        - yfe: ÜFE/YFE bazlı artış
        - sabit_yuzde: Sabit yüzde ile artış
        - anlasmali: Karşılıklı anlaşma ile
    """
    __tablename__ = 'kira_kontrat'
    __table_args__ = (
        db.Index('ix_kira_blok_daire', 'blok', 'daire_no'),
        db.Index('ix_kira_sonraki_artis', 'sonraki_artis_tarihi'),
    )

    # ── Artış Türü Sabitleri ──
    ARTIS_TUFE = 'tufe'
    ARTIS_YFE = 'yfe'
    ARTIS_SABIT = 'sabit_yuzde'
    ARTIS_ANLASMALI = 'anlasmali'

    ARTIS_TURLERI = {
        ARTIS_TUFE: 'TÜFE Bazlı',
        ARTIS_YFE: 'ÜFE/YFE Bazlı',
        ARTIS_SABIT: 'Sabit Yüzde',
        ARTIS_ANLASMALI: 'Anlaşmalı',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sozlesme_id = db.Column(db.Integer, db.ForeignKey('sozlesme.id', ondelete='CASCADE'),
                             unique=True, nullable=False, index=True)

    # Konum bilgileri
    daire_no = db.Column(db.String(20), nullable=True)
    blok = db.Column(db.String(50), nullable=True)
    kat = db.Column(db.String(10), nullable=True)

    # Alan bilgisi
    m2 = db.Column(db.Numeric(8, 2), nullable=True)

    # Mali bilgiler
    kira_tutari = db.Column(db.Numeric(12, 2), nullable=True)
    depozito = db.Column(db.Numeric(12, 2), nullable=True)
    aidat_tutari = db.Column(db.Numeric(10, 2), nullable=True)

    # Artış bilgileri
    artis_turu = db.Column(db.String(20), nullable=True, default=ARTIS_TUFE)
    artis_orani = db.Column(db.Numeric(5, 2), nullable=True)  # Sabit yüzde ise
    son_artis_tarihi = db.Column(db.Date, nullable=True)
    sonraki_artis_tarihi = db.Column(db.Date, nullable=True)

    # Ödeme bilgileri
    odeme_gunu = db.Column(db.Integer, nullable=True)  # 1-31 arası

    # Gecikme faizi
    gecikme_faiz_orani = db.Column(db.Numeric(5, 2), nullable=True)  # Aylık %

    # ── Property'ler ──
    @property
    def artis_turu_adi(self):
        return self.ARTIS_TURLERI.get(self.artis_turu, self.artis_turu or '—')

    @property
    def konum_bilgi(self):
        """Blok, kat ve daire bilgisini birleştirerek döndürür."""
        parts = []
        if self.blok:
            parts.append(f'Blok {self.blok}')
        if self.kat:
            parts.append(f'Kat {self.kat}')
        if self.daire_no:
            parts.append(f'No {self.daire_no}')
        return ' - '.join(parts) if parts else '—'

    @property
    def kira_formatli(self):
        """Kira tutarını formatlar."""
        if self.kira_tutari is None:
            return '—'
        return f'₺ {self.kira_tutari:,.2f}'

    @property
    def artis_kalan_gun(self):
        """Bir sonraki artış tarihine kalan gün."""
        if not self.sonraki_artis_tarihi:
            return None
        return (self.sonraki_artis_tarihi - date.today()).days

    def __repr__(self):
        return f'<KiraKontrat {self.konum_bilgi} — ₺{self.kira_tutari}>'


class SigortaPolice(db.Model):
    """
    Sigorta poliçesi detayları.

    Sigorta Türleri:
        - yangin: Yangın sigortası
        - deprem: Deprem/DASK sigortası
        - kasko: Araç kasko sigortası
        - isveren_sorumluluk: İşveren sorumluluk sigortası
        - genel_sorumluluk: Genel sorumluluk sigortası
        - ferdi_kaza: Ferdi kaza sigortası
    """
    __tablename__ = 'sigorta_police'
    __table_args__ = (
        db.Index('ix_police_durum', 'durum'),
        db.Index('ix_police_bitis', 'police_bitis'),
    )

    # ── Sigorta Türü Sabitleri ──
    TUR_YANGIN = 'yangin'
    TUR_DEPREM = 'deprem'
    TUR_KASKO = 'kasko'
    TUR_ISVEREN = 'isveren_sorumluluk'
    TUR_GENEL = 'genel_sorumluluk'
    TUR_FERDI = 'ferdi_kaza'

    SIGORTA_TURLERI = {
        TUR_YANGIN: 'Yangın Sigortası',
        TUR_DEPREM: 'Deprem / DASK',
        TUR_KASKO: 'Araç Kasko',
        TUR_ISVEREN: 'İşveren Sorumluluk',
        TUR_GENEL: 'Genel Sorumluluk',
        TUR_FERDI: 'Ferdi Kaza',
    }

    # ── Durum Sabitleri ──
    DURUM_AKTIF = 'aktif'
    DURUM_SURESI_DOLDU = 'suresi_doldu'
    DURUM_IPTAL = 'iptal'

    DURUMLAR = {
        DURUM_AKTIF: 'Aktif',
        DURUM_SURESI_DOLDU: 'Süresi Doldu',
        DURUM_IPTAL: 'İptal Edildi',
    }

    DURUM_RENKLERI = {
        DURUM_AKTIF: 'success',
        DURUM_SURESI_DOLDU: 'danger',
        DURUM_IPTAL: 'secondary',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sozlesme_id = db.Column(db.Integer, db.ForeignKey('sozlesme.id', ondelete='CASCADE'),
                             nullable=True, unique=True, index=True)

    # Poliçe bilgileri
    police_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sigorta_sirketi = db.Column(db.String(150), nullable=False)
    sigorta_turu = db.Column(db.String(30), nullable=False, default=TUR_YANGIN)

    # Tarihler
    police_baslangic = db.Column(db.Date, nullable=False)
    police_bitis = db.Column(db.Date, nullable=False)

    # Mali bilgiler
    prim_tutari = db.Column(db.Numeric(12, 2), nullable=True)
    teminat_tutari = db.Column(db.Numeric(14, 2), nullable=True)

    # Hatırlatma
    hatirlatma_gun = db.Column(db.Integer, nullable=True, default=30)

    # Durum
    durum = db.Column(db.String(20), nullable=False, default=DURUM_AKTIF)
    notlar = db.Column(db.Text, nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # ── Property'ler ──
    @property
    def sigorta_turu_adi(self):
        return self.SIGORTA_TURLERI.get(self.sigorta_turu, self.sigorta_turu)

    @property
    def durum_adi(self):
        return self.DURUMLAR.get(self.durum, self.durum)

    @property
    def durum_renk(self):
        return self.DURUM_RENKLERI.get(self.durum, 'secondary')

    @property
    def kalan_gun(self):
        """Poliçe bitiş tarihine kalan gün sayısı."""
        if not self.police_bitis:
            return None
        return (self.police_bitis - date.today()).days

    @property
    def suresi_dolmak_uzere(self):
        """Hatırlatma süresi içinde mi?"""
        kalan = self.kalan_gun
        if kalan is None:
            return False
        hatirlatma = self.hatirlatma_gun or 30
        return 0 < kalan <= hatirlatma

    @property
    def suresi_doldu(self):
        """Poliçe süresi dolmuş mu?"""
        kalan = self.kalan_gun
        if kalan is None:
            return False
        return kalan <= 0

    @property
    def prim_formatli(self):
        """Prim tutarını formatlar."""
        if self.prim_tutari is None:
            return '—'
        return f'₺ {self.prim_tutari:,.2f}'

    @property
    def teminat_formatli(self):
        """Teminat tutarını formatlar."""
        if self.teminat_tutari is None:
            return '—'
        return f'₺ {self.teminat_tutari:,.2f}'

    def __repr__(self):
        return f'<SigortaPolice {self.police_no} — {self.sigorta_sirketi}>'


class StandartMetin(db.Model):
    """
    Sözleşme standart metin şablonları.
    Değişkenler (ör: {ortak_adi}, {daire_no}, {tutar}) ile şablonlar oluşturulabilir.
    """
    __tablename__ = 'standart_metin'
    __table_args__ = (
        db.Index('ix_metin_tur', 'tur'),
    )

    # ── Metin Türü Sabitleri ──
    TUR_KIRA = 'kira'
    TUR_HIZMET = 'hizmet'
    TUR_BAKIM = 'bakim'
    TUR_GENEL = 'genel'

    METIN_TURLERI = {
        TUR_KIRA: 'Kira Sözleşmesi',
        TUR_HIZMET: 'Hizmet Sözleşmesi',
        TUR_BAKIM: 'Bakım Sözleşmesi',
        TUR_GENEL: 'Genel Şablon',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    baslik = db.Column(db.String(200), nullable=False)
    icerik = db.Column(db.Text, nullable=False)  # HTML/Markdown şablon içeriği
    tur = db.Column(db.String(20), nullable=False, default=TUR_GENEL)

    # Dinamik değişkenler: ["{ortak_adi}", "{daire_no}", "{tutar}", "{tarih}"]
    degiskenler = db.Column(db.JSON, nullable=True)

    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ── Property'ler ──
    @property
    def tur_adi(self):
        return self.METIN_TURLERI.get(self.tur, self.tur)

    @property
    def degisken_listesi(self):
        """Değişken listesini döndürür."""
        if not self.degiskenler:
            return []
        return self.degiskenler if isinstance(self.degiskenler, list) else []

    def icerik_doldur(self, degerler):
        """
        Şablon içeriğindeki değişkenleri verilen değerlerle doldurur.

        Args:
            degerler: dict — {'{ortak_adi}': 'Ahmet Yılmaz', '{tutar}': '5.000'}

        Returns:
            str: Doldurulmuş metin
        """
        sonuc = self.icerik
        for degisken, deger in degerler.items():
            sonuc = sonuc.replace(degisken, str(deger))
        return sonuc

    def __repr__(self):
        return f'<StandartMetin {self.baslik[:50]}>'
