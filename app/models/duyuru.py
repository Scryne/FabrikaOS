"""
FDYS — Duyuru & İletişim Modeli
Faz 6 — Duyuru Yönetimi

Kurumsal duyurular, acil bildirimler, etkinlik ilanları.
Hedef kitle filtreleme, okunma takibi, sabitleme ve
otomatik süre sona erme desteği.
"""

from datetime import datetime, timezone
from app.extensions import db


class Duyuru(db.Model):
    """
    Kurumsal duyuru sistemi.

    Türler: bilgi, acil, etkinlik, bakim, toplanti
    Öncelikler: normal, onemli, acil
    Hedef kitleler: tumu, departman, rol, kisi
    """
    __tablename__ = 'duyuru'
    __table_args__ = (
        db.Index('ix_duyuru_yayin_aktif', 'yayin_tarihi', 'aktif'),
        db.Index('ix_duyuru_sabitle', 'sabitle', 'aktif'),
    )

    # ── Tür Sabitleri ──
    TURLER = {
        'bilgi': {'ad': 'Bilgilendirme', 'ikon': 'bi-info-circle', 'renk': '#3b82f6'},
        'acil': {'ad': 'Acil Duyuru', 'ikon': 'bi-exclamation-triangle', 'renk': '#ef4444'},
        'etkinlik': {'ad': 'Etkinlik', 'ikon': 'bi-calendar-event', 'renk': '#8b5cf6'},
        'bakim': {'ad': 'Bakım Bildirimi', 'ikon': 'bi-wrench-adjustable', 'renk': '#f59e0b'},
        'toplanti': {'ad': 'Toplantı', 'ikon': 'bi-people', 'renk': '#06b6d4'},
    }

    # ── Öncelik Sabitleri ──
    ONCELIKLER = {
        'normal': {'ad': 'Normal', 'renk': '#64748b', 'badge': 'bg-secondary'},
        'onemli': {'ad': 'Önemli', 'renk': '#f59e0b', 'badge': 'bg-warning'},
        'acil': {'ad': 'Acil', 'renk': '#ef4444', 'badge': 'bg-danger'},
    }

    # ── Hedef Kitle Sabitleri ──
    HEDEF_KITLELER = {
        'tumu': 'Tüm Kullanıcılar',
        'departman': 'Belirli Departman',
        'rol': 'Belirli Rol',
        'kisi': 'Belirli Kişiler',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    baslik = db.Column(db.String(300), nullable=False, index=True)
    icerik = db.Column(db.Text, nullable=False)  # Rich text HTML içerik

    # Sınıflandırma
    tur = db.Column(db.String(30), nullable=False, default='bilgi')
    oncelik = db.Column(db.String(20), nullable=False, default='normal')

    # Hedef kitle
    hedef_kitle = db.Column(db.String(30), nullable=False, default='tumu')
    hedef_deger = db.Column(db.String(500), nullable=True)  # Departman adı, rol adı veya kullanici_id'ler (virgülle ayrılmış)

    # Yayınlayan
    yayinlayan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)

    # Tarihler
    yayin_tarihi = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    bitis_tarihi = db.Column(db.DateTime, nullable=True)  # NULL ise süresiz

    # Davranış
    sabitle = db.Column(db.Boolean, default=False, nullable=False)  # Üst çubuğa sabitle
    okunma_sayisi = db.Column(db.Integer, default=0, nullable=False)

    # Aktiflik ve tarihler
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # İlişkiler
    yayinlayan = db.relationship('Kullanici', foreign_keys=[yayinlayan_id],
                                 backref=db.backref('yayinlanan_duyurular', lazy='dynamic'))
    okunma_kayitlari = db.relationship('DuyuruOkunma', backref='duyuru',
                                       lazy='dynamic', cascade='all, delete-orphan')

    @property
    def tur_bilgi(self):
        """Tür bilgilerini (ad, ikon, renk) sözlük olarak döner."""
        return self.TURLER.get(self.tur, {'ad': self.tur, 'ikon': 'bi-bell', 'renk': '#6b7280'})

    @property
    def tur_adi(self):
        """Türün Türkçe adını döner."""
        return self.tur_bilgi['ad']

    @property
    def tur_ikonu(self):
        """Türün Bootstrap icon sınıfını döner."""
        return self.tur_bilgi['ikon']

    @property
    def tur_rengi(self):
        """Türün renk kodunu döner."""
        return self.tur_bilgi['renk']

    @property
    def oncelik_bilgi(self):
        """Öncelik bilgilerini (ad, renk, badge) sözlük olarak döner."""
        return self.ONCELIKLER.get(self.oncelik, {'ad': self.oncelik, 'renk': '#6b7280', 'badge': 'bg-secondary'})

    @property
    def oncelik_adi(self):
        """Önceliğin Türkçe adını döner."""
        return self.oncelik_bilgi['ad']

    @property
    def hedef_kitle_adi(self):
        """Hedef kitle açıklamasını döner."""
        return self.HEDEF_KITLELER.get(self.hedef_kitle, self.hedef_kitle)

    @property
    def suresi_doldu_mu(self):
        """Duyurunun süresi dolmuş mu?"""
        if self.bitis_tarihi is None:
            return False
        bitis = self.bitis_tarihi.replace(tzinfo=timezone.utc) if self.bitis_tarihi.tzinfo is None else self.bitis_tarihi
        return datetime.now(timezone.utc) > bitis

    @property
    def aktif_duyuru_mu(self):
        """Duyurunun aktif ve süresi dolmamış olduğunu kontrol eder."""
        return self.aktif and not self.suresi_doldu_mu

    def kullanici_gorebilir_mi(self, kullanici):
        """
        Belirtilen kullanıcının bu duyuruyu görüp göremeyeceğini kontrol eder.

        Args:
            kullanici: Kontrol edilecek kullanıcı nesnesi

        Returns:
            bool: Kullanıcı duyuruyu görebilir mi
        """
        if not self.aktif_duyuru_mu:
            return False

        if kullanici.yonetici_mi():
            return True

        if self.hedef_kitle == 'tumu':
            return True

        if self.hedef_kitle == 'departman':
            return kullanici.departman == self.hedef_deger

        if self.hedef_kitle == 'rol':
            return kullanici.rol == self.hedef_deger

        if self.hedef_kitle == 'kisi':
            if self.hedef_deger:
                kisi_idleri = [int(x.strip()) for x in self.hedef_deger.split(',') if x.strip().isdigit()]
                return kullanici.id in kisi_idleri

        return False

    def kullanici_okudu_mu(self, kullanici_id):
        """Belirtilen kullanıcı bu duyuruyu okudu mu?"""
        return DuyuruOkunma.query.filter_by(
            duyuru_id=self.id,
            kullanici_id=kullanici_id
        ).first() is not None

    def okunma_kaydet(self, kullanici_id):
        """Kullanıcının duyuruyu okuduğunu kaydeder."""
        if not self.kullanici_okudu_mu(kullanici_id):
            okunma = DuyuruOkunma(
                duyuru_id=self.id,
                kullanici_id=kullanici_id
            )
            db.session.add(okunma)
            self.okunma_sayisi = (self.okunma_sayisi or 0) + 1
            return True
        return False

    @property
    def icerik_onizleme(self):
        """İçeriğin kısa önizlemesini döner (HTML etiketleri temizlenmiş)."""
        import re
        temiz = re.sub(r'<[^>]+>', '', self.icerik or '')
        return temiz[:200] + '...' if len(temiz) > 200 else temiz

    def __repr__(self):
        return f'<Duyuru [{self.tur}] "{self.baslik}">'


class DuyuruOkunma(db.Model):
    """
    Duyuru okunma kaydı — hangi kullanıcı hangi duyuruyu ne zaman okudu.
    """
    __tablename__ = 'duyuru_okunma'
    __table_args__ = (
        db.UniqueConstraint('duyuru_id', 'kullanici_id', name='uq_duyuru_okunma_unique'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    duyuru_id = db.Column(db.Integer, db.ForeignKey('duyuru.id', ondelete='CASCADE'), nullable=False, index=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='CASCADE'), nullable=False, index=True)
    tarih = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # İlişkiler
    kullanici = db.relationship('Kullanici', backref=db.backref('okunan_duyurular', lazy='dynamic'))

    def __repr__(self):
        return f'<DuyuruOkunma duyuru={self.duyuru_id} kullanici={self.kullanici_id}>'
