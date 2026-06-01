"""
FDYS — Doküman Yönetim Sistemi (DYS) Modeli
Faz 6 — Merkezi Doküman Yönetimi

Versiyon kontrolü, erişim seviyeleri, onay akışı,
OCR tam metin arama ve indirme istatistikleri destekler.
"""

from datetime import datetime, timezone
from app.extensions import db


class Dokuman(db.Model):
    """
    Merkezi doküman yönetimi — versiyon kontrolü ve tam metin arama.

    Kategoriler: prosedur, talimat, form, rapor, sozlesme, diger
    Erişim seviyeleri: herkese_acik, departman, ozel, yonetim
    Onay durumları: taslak, onay_bekliyor, onaylandi, reddedildi
    """
    __tablename__ = 'dokuman'
    __table_args__ = (
        db.Index('ix_dokuman_kategori_departman', 'kategori', 'departman'),
        db.Index('ix_dokuman_onay_durumu', 'onay_durumu'),
    )

    # ── Kategori Sabitleri ──
    KATEGORILER = {
        'prosedur': 'Prosedür',
        'talimat': 'Talimat',
        'form': 'Form',
        'rapor': 'Rapor',
        'sozlesme': 'Sözleşme',
        'diger': 'Diğer',
    }

    # ── Erişim Seviyeleri ──
    ERISIM_SEVIYELERI = {
        'herkese_acik': 'Herkese Açık',
        'departman': 'Departman İçi',
        'ozel': 'Özel (Sadece Sahip)',
        'yonetim': 'Yönetim Kadrosu',
    }

    # ── Onay Durumları ──
    ONAY_DURUMLARI = {
        'taslak': 'Taslak',
        'onay_bekliyor': 'Onay Bekliyor',
        'onaylandi': 'Onaylandı',
        'reddedildi': 'Reddedildi',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    baslik = db.Column(db.String(300), nullable=False, index=True)
    kategori = db.Column(db.String(50), nullable=False, default='diger')
    alt_kategori = db.Column(db.String(100), nullable=True)
    etiketler = db.Column(db.JSON, default=list)  # ["ISO9001", "acil", "gizli"]

    # Dosya bilgileri
    dosya_adi = db.Column(db.String(255), nullable=False)       # Sunucuda saklanan ad (UUID prefix)
    orijinal_adi = db.Column(db.String(255), nullable=False)    # Kullanıcının yüklediği orijinal ad
    mime_type = db.Column(db.String(100), nullable=True)
    dosya_boyutu = db.Column(db.Integer, nullable=True)         # Byte cinsinden

    # Versiyon kontrolü
    versiyon = db.Column(db.Integer, nullable=False, default=1)
    onceki_versiyon_id = db.Column(db.Integer, db.ForeignKey('dokuman.id', ondelete='SET NULL'), nullable=True)

    # Sahiplik ve erişim
    sahip_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    departman = db.Column(db.String(50), nullable=True)
    erisim_seviyesi = db.Column(db.String(30), nullable=False, default='herkese_acik')

    # OCR ve arama
    ocr_metin = db.Column(db.Text, nullable=True)  # OCR çıktısı — tam metin arama için

    # İstatistikler
    indirme_sayisi = db.Column(db.Integer, nullable=False, default=0)

    # Onay akışı
    onay_durumu = db.Column(db.String(30), nullable=False, default='taslak')
    onaylayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    onay_tarihi = db.Column(db.DateTime, nullable=True)
    red_nedeni = db.Column(db.Text, nullable=True)

    # Açıklama
    aciklama = db.Column(db.Text, nullable=True)

    # Aktiflik ve tarihler
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    sahip = db.relationship('Kullanici', foreign_keys=[sahip_id],
                            backref=db.backref('dokumanlar', lazy='dynamic'))
    onaylayan = db.relationship('Kullanici', foreign_keys=[onaylayan_id],
                                backref=db.backref('onayladigi_dokumanlar', lazy='dynamic'))
    onceki_versiyon = db.relationship('Dokuman', remote_side=[id],
                                     backref=db.backref('sonraki_versiyonlar', lazy='dynamic'))

    # ── Dosya Türü Tespit ──
    DOSYA_TIPI_ESLESME = {
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image',
        'pdf': 'pdf',
        'doc': 'document', 'docx': 'document',
        'xls': 'spreadsheet', 'xlsx': 'spreadsheet', 'csv': 'spreadsheet',
        'txt': 'text', 'md': 'text',
        'ppt': 'presentation', 'pptx': 'presentation',
        'zip': 'archive', 'rar': 'archive', '7z': 'archive',
    }

    DOSYA_TIPI_IKON = {
        'image': 'bi-file-earmark-image',
        'pdf': 'bi-file-earmark-pdf',
        'document': 'bi-file-earmark-word',
        'spreadsheet': 'bi-file-earmark-spreadsheet',
        'text': 'bi-file-earmark-text',
        'presentation': 'bi-file-earmark-slides',
        'archive': 'bi-file-earmark-zip',
    }

    DOSYA_TIPI_RENK = {
        'image': '#10b981',
        'pdf': '#ef4444',
        'document': '#3b82f6',
        'spreadsheet': '#22c55e',
        'text': '#8b5cf6',
        'presentation': '#f59e0b',
        'archive': '#6b7280',
    }

    @property
    def dosya_tipi(self):
        """Dosya uzantısından tip belirler."""
        uzanti = self.orijinal_adi.rsplit('.', 1)[-1].lower() if '.' in self.orijinal_adi else ''
        return self.DOSYA_TIPI_ESLESME.get(uzanti, 'document')

    @property
    def ikon_sinifi(self):
        """Bootstrap icon CSS sınıfı."""
        return self.DOSYA_TIPI_IKON.get(self.dosya_tipi, 'bi-file-earmark')

    @property
    def tip_rengi(self):
        """Dosya tipi renk kodu."""
        return self.DOSYA_TIPI_RENK.get(self.dosya_tipi, '#6b7280')

    @property
    def resim_mi(self):
        """Dosya bir resim mi?"""
        return self.dosya_tipi == 'image'

    @property
    def kategori_adi(self):
        """Kategorinin Türkçe karşılığını döner."""
        return self.KATEGORILER.get(self.kategori, self.kategori)

    @property
    def erisim_seviyesi_adi(self):
        """Erişim seviyesinin Türkçe karşılığını döner."""
        return self.ERISIM_SEVIYELERI.get(self.erisim_seviyesi, self.erisim_seviyesi)

    @property
    def onay_durumu_adi(self):
        """Onay durumunun Türkçe karşılığını döner."""
        return self.ONAY_DURUMLARI.get(self.onay_durumu, self.onay_durumu)

    @property
    def boyut_formatli(self):
        """Dosya boyutunu okunabilir formatta döner (KB, MB)."""
        if not self.dosya_boyutu:
            return '—'
        if self.dosya_boyutu < 1024:
            return f'{self.dosya_boyutu} B'
        elif self.dosya_boyutu < 1024 * 1024:
            return f'{self.dosya_boyutu / 1024:.1f} KB'
        else:
            return f'{self.dosya_boyutu / (1024 * 1024):.1f} MB'

    @property
    def etiket_listesi(self):
        """Etiketleri liste olarak döner."""
        if isinstance(self.etiketler, list):
            return self.etiketler
        return []

    def versiyon_gecmisi(self):
        """
        Dokümanın tüm versiyon geçmişini döner.
        Mevcut versiyondan geriye doğru takip eder.
        """
        gecmis = [self]
        mevcut = self
        while mevcut.onceki_versiyon_id:
            onceki = db.session.get(Dokuman, mevcut.onceki_versiyon_id)
            if onceki and onceki not in gecmis:
                gecmis.append(onceki)
                mevcut = onceki
            else:
                break
        return gecmis

    def indirme_artir(self):
        """İndirme sayısını 1 artırır."""
        self.indirme_sayisi = (self.indirme_sayisi or 0) + 1

    def erisim_kontrol(self, kullanici):
        """
        Kullanıcının bu dokümana erişip erişemeyeceğini kontrol eder.

        Args:
            kullanici: Kontrol edilecek kullanıcı nesnesi

        Returns:
            bool: Erişim izni var mı
        """
        if kullanici.yonetici_mi():
            return True

        if self.erisim_seviyesi == 'herkese_acik':
            return True

        if self.erisim_seviyesi == 'ozel':
            return kullanici.id == self.sahip_id

        if self.erisim_seviyesi == 'departman':
            return kullanici.departman == self.departman

        if self.erisim_seviyesi == 'yonetim':
            return kullanici.rol in ('yonetici', 'muhasebe')

        return False

    def __repr__(self):
        return f'<Dokuman v{self.versiyon} "{self.baslik}">'
