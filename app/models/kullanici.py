"""
FDYS — Kullanıcı ve Yetki Modeli

Sistem erişimi için kullanıcı tablosu.
8 rol desteklenir: yönetici, operatör, teknisyen, ik_uzmani,
isg_uzmani, muhasebe, crm_yetkilisi, satin_alma.

Modül erişim yapısı granüler:
    {'modul_adi': {'okuma': True, 'yazma': True, 'silme': False}}
    Geriye dönük uyumlu: {'modul_adi': True} formatı da desteklenir.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db, bcrypt


class Kullanici(UserMixin, db.Model):
    """
    Sistem kullanıcısı modeli.

    Roller:
        - yonetici: Tam yetki, tüm modüllere erişim
        - operator: Üretim verisi girişi, kısıtlı raporlar
        - teknisyen: Arıza çözme, bakım işlemleri
        - ik_uzmani: İnsan kaynakları yönetimi
        - isg_uzmani: İş sağlığı ve güvenliği
        - muhasebe: Mali işlemler, sözleşme, borç/alacak
        - crm_yetkilisi: CRM / ortak-firma yönetimi
        - satin_alma: Satın alma süreçleri
    """
    __tablename__ = 'kullanici'

    # ── Rol Sabitleri ──
    ROL_YONETICI = 'yonetici'
    ROL_OPERATOR = 'operator'
    ROL_TEKNISYEN = 'teknisyen'
    ROL_IK_UZMANI = 'ik_uzmani'
    ROL_ISG_UZMANI = 'isg_uzmani'
    ROL_MUHASEBE = 'muhasebe'
    ROL_CRM_YETKILISI = 'crm_yetkilisi'
    ROL_SATIN_ALMA = 'satin_alma'

    ROLLER = {
        ROL_YONETICI: 'Yönetici',
        ROL_OPERATOR: 'Operatör',
        ROL_TEKNISYEN: 'Teknisyen',
        ROL_IK_UZMANI: 'İK Uzmanı',
        ROL_ISG_UZMANI: 'İSG Uzmanı',
        ROL_MUHASEBE: 'Muhasebe',
        ROL_CRM_YETKILISI: 'CRM Yetkilisi',
        ROL_SATIN_ALMA: 'Satın Alma',
    }

    # ── Modül Tanımları (tüm sistemdeki modüller) ──
    MODULLER = {
        'personel': 'Personel Yönetimi',
        'makine': 'Makine & Üretim',
        'stok': 'Stok Yönetimi',
        'kalite': 'Kalite Kontrol',
        'enerji': 'Enerji Yönetimi',
        'isg': 'İş Sağlığı & Güvenliği',
        'ik': 'İnsan Kaynakları',
        'crm': 'CRM (Ortak & Firma)',
        'sozlesme': 'Sözleşme & Kontrat',
        'talep': 'Talep & İş Takip',
        'satin_alma': 'Satın Alma',
        'dys': 'Doküman Yönetimi',
        'duyuru': 'Duyuru & İletişim',
    }

    # ── İzin Türleri ──
    IZIN_OKUMA = 'okuma'
    IZIN_YAZMA = 'yazma'
    IZIN_SILME = 'silme'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    kullanici_adi = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sifre_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='operator')
    departman = db.Column(db.String(50), nullable=True)  # Kullanıcının ait olduğu departman
    modul_erisim = db.Column(db.JSON, default=dict)  # Granüler: {'modul': {'okuma': T, 'yazma': T, 'silme': F}}
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    son_giris = db.Column(db.DateTime, nullable=True)
    oturum_sayisi = db.Column(db.Integer, default=0)
    basarisiz_giris = db.Column(db.Integer, default=0)  # Brute force koruması
    hesap_kilitli = db.Column(db.Boolean, default=False)
    kilit_zamani = db.Column(db.DateTime, nullable=True)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    dashboard_layout = db.Column(db.JSON, default=dict)

    # İlişkiler
    calisan = db.relationship('Calisan', backref='kullanici', uselist=False, lazy='joined')

    def sifre_belirle(self, sifre):
        """Şifreyi bcrypt ile hash'leyerek kaydeder (work factor: 12)."""
        self.sifre_hash = bcrypt.generate_password_hash(sifre).decode('utf-8')

    def sifre_dogrula(self, sifre):
        """Girilen şifreyi kaydedilmiş hash ile doğrular."""
        return bcrypt.check_password_hash(self.sifre_hash, sifre)

    def giris_basarili(self):
        """Başarılı giriş sonrası sayaçları günceller."""
        self.son_giris = datetime.now(timezone.utc)
        self.oturum_sayisi += 1
        self.basarisiz_giris = 0
        self.hesap_kilitli = False
        self.kilit_zamani = None

    def giris_basarisiz(self):
        """Başarısız giriş sayacını artırır, 5'te kilitle."""
        self.basarisiz_giris += 1
        if self.basarisiz_giris >= 5:
            self.hesap_kilitli = True
            self.kilit_zamani = datetime.now(timezone.utc)

    def yonetici_mi(self):
        """Kullanıcının yönetici olup olmadığını kontrol eder."""
        return self.rol == self.ROL_YONETICI

    @property
    def rol_adi(self):
        """Rolün Türkçe karşılığını döner."""
        return self.ROLLER.get(self.rol, self.rol)

    def modul_erisim_var_mi(self, modul_adi, izin_turu=None):
        """
        Kullanıcının belirtilen modüle (ve opsiyonel olarak izin türüne) erişimi
        olup olmadığını kontrol eder.

        Granüler format:  {'personel': {'okuma': True, 'yazma': True, 'silme': False}}
        Eski format:      {'personel': True}
        Her iki format da desteklenir (geriye dönük uyumluluk).

        Args:
            modul_adi: Kontrol edilecek modül adı ('personel', 'crm', vb.)
            izin_turu: Opsiyonel izin türü ('okuma', 'yazma', 'silme').
                       None ise herhangi bir erişim olup olmadığı kontrol edilir.
        """
        if self.yonetici_mi():
            return True

        if not self.modul_erisim:
            return False

        erisim = self.modul_erisim.get(modul_adi)

        if erisim is None:
            return False

        # Eski format uyumluluğu: {'personel': True}
        if isinstance(erisim, bool):
            return erisim

        # Granüler format: {'personel': {'okuma': True, 'yazma': False, 'silme': False}}
        if isinstance(erisim, dict):
            if izin_turu is None:
                # Herhangi bir izin varsa True
                return any(erisim.values())
            return erisim.get(izin_turu, False)

        return False

    def modul_izinleri_getir(self, modul_adi):
        """
        Belirtilen modül için tüm izinleri sözlük olarak döner.
        Yöneticilere tam yetki verir.

        Returns:
            {'okuma': True, 'yazma': True, 'silme': True}
        """
        tam_yetki = {self.IZIN_OKUMA: True, self.IZIN_YAZMA: True, self.IZIN_SILME: True}
        yetki_yok = {self.IZIN_OKUMA: False, self.IZIN_YAZMA: False, self.IZIN_SILME: False}

        if self.yonetici_mi():
            return tam_yetki

        if not self.modul_erisim:
            return yetki_yok

        erisim = self.modul_erisim.get(modul_adi)
        if erisim is None:
            return yetki_yok

        # Eski format uyumluluğu
        if isinstance(erisim, bool):
            return tam_yetki if erisim else yetki_yok

        if isinstance(erisim, dict):
            return {
                self.IZIN_OKUMA: erisim.get(self.IZIN_OKUMA, False),
                self.IZIN_YAZMA: erisim.get(self.IZIN_YAZMA, False),
                self.IZIN_SILME: erisim.get(self.IZIN_SILME, False),
            }

        return yetki_yok

    @classmethod
    def erisim_sablonu_olustur(cls, tam_yetki_moduller=None, okuma_moduller=None):
        """
        Hızlı modül erişim şablonu oluşturur.

        Args:
            tam_yetki_moduller: Tam yetki verilecek modül listesi
            okuma_moduller: Sadece okuma yetkisi verilecek modül listesi

        Returns:
            Granüler erişim sözlüğü
        """
        sablon = {}
        for m in (tam_yetki_moduller or []):
            sablon[m] = {cls.IZIN_OKUMA: True, cls.IZIN_YAZMA: True, cls.IZIN_SILME: True}
        for m in (okuma_moduller or []):
            sablon[m] = {cls.IZIN_OKUMA: True, cls.IZIN_YAZMA: False, cls.IZIN_SILME: False}
        return sablon

    def __repr__(self):
        return f'<Kullanici {self.kullanici_adi} [{self.rol}]>'


class DenetimIzi(db.Model):
    """
    Denetim izi (audit trail) tablosu.
    Tüm veri değişiklikleri @log_action dekoratörüyle buraya loglanır.
    """
    __tablename__ = 'denetim_izi'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    islem = db.Column(db.String(50), nullable=False)  # Oluştur, Güncelle, Sil
    tablo = db.Column(db.String(50), nullable=False)
    kayit_id = db.Column(db.Integer, nullable=True)
    detay = db.Column(db.Text, nullable=True)  # JSON formatında değişiklik detayı
    ip_adresi = db.Column(db.String(45), nullable=True)
    tarih = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # İlişki
    kullanici = db.relationship('Kullanici', backref='denetim_izleri', lazy='joined')

    def __repr__(self):
        return f'<DenetimIzi {self.islem} {self.tablo}#{self.kayit_id}>'
