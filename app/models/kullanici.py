"""
FDYS — Kullanıcı ve Yetki Modeli

Sistem erişimi için kullanıcı tablosu.
3 rol desteklenir: yönetici, operatör, teknisyen.
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
    """
    __tablename__ = 'kullanici'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    kullanici_adi = db.Column(db.String(50), unique=True, nullable=False, index=True)
    sifre_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='operator')  # yonetici|operator|teknisyen
    modul_erisim = db.Column(db.JSON, default=dict)  # Hangi modüllere erişebilir
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
        return self.rol == 'yonetici'

    def modul_erisim_var_mi(self, modul_adi):
        """Kullanıcının belirtilen modüle erişimi olup olmadığını kontrol eder."""
        if self.yonetici_mi():
            return True
        return self.modul_erisim.get(modul_adi, False) if self.modul_erisim else False

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
