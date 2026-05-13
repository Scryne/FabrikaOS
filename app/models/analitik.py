"""
FDYS — Gelişmiş Analitik Modeli
Kategori 4 — Karar Destek Sistemi

Modeller:
    - KpiHedef: Modül bazlı KPI hedef tanımlama ve periyodik takip
"""

from datetime import datetime, timezone
from app.extensions import db


class KpiHedef(db.Model):
    """
    KPI Hedef Tanımlama Tablosu.

    Her modül için KPI hedefleri tanımlanır ve gerçekleşen değerler
    ile otomatik olarak karşılaştırılır. Yöneticiler admin panelinden
    yeni KPI'lar ekleyebilir, düzenleyebilir veya silebilir.
    """
    __tablename__ = 'kpi_hedef'
    __table_args__ = (
        db.Index('ix_kpi_modul_kod_yil_ay', 'modul', 'kpi_kodu', 'yil', 'ay'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modul = db.Column(db.String(50), nullable=False)  # makine|kalite|enerji|isg|stok|personel
    kpi_adi = db.Column(db.String(100), nullable=False)  # "Ortalama OEE", "Hata Oranı" vb.
    kpi_kodu = db.Column(db.String(50), nullable=False)  # unique slug: "ort_oee", "hata_orani"
    birim = db.Column(db.String(20), nullable=False, default='%')  # %, TL, adet, gün
    hedef_deger = db.Column(db.Numeric(12, 2), nullable=False)  # Hedef değer
    alt_limit = db.Column(db.Numeric(12, 2), nullable=True)  # Kabul edilebilir alt sınır
    ust_limit = db.Column(db.Numeric(12, 2), nullable=True)  # Kabul edilebilir üst sınır
    yonu = db.Column(db.String(10), default='yukari')  # yukari: yüksek iyi, asagi: düşük iyi
    periyot = db.Column(db.String(20), default='aylik')  # aylik|haftalik|ceyreklik|yillik
    yil = db.Column(db.Integer, nullable=False)
    ceyrek = db.Column(db.Integer, nullable=True)  # 1-4 (çeyreklik periyot için)
    ay = db.Column(db.Integer, nullable=True)  # 1-12 (aylık periyot için)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturan_id = db.Column(db.Integer, db.ForeignKey('kullanici.id', ondelete='SET NULL'), nullable=True)
    olusturma_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guncelleme_tarihi = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    # İlişkiler
    olusturan = db.relationship('Kullanici', backref='kpi_hedefleri', lazy='joined')

    # ── Sabitler ──
    MODULLER = {
        'makine': 'Makine & Üretim',
        'kalite': 'Kalite Kontrol',
        'enerji': 'Enerji Yönetimi',
        'isg': 'İş Sağlığı & Güvenliği',
        'stok': 'Stok Yönetimi',
        'personel': 'Personel Yönetimi'
    }

    VARSAYILAN_KPILER = [
        {'modul': 'makine', 'kpi_kodu': 'ort_oee', 'kpi_adi': 'Ortalama OEE', 'birim': '%', 'yonu': 'yukari'},
        {'modul': 'makine', 'kpi_kodu': 'ariza_sayisi', 'kpi_adi': 'Arıza Sayısı', 'birim': 'adet', 'yonu': 'asagi'},
        {'modul': 'makine', 'kpi_kodu': 'bakim_maliyeti', 'kpi_adi': 'Bakım Maliyeti', 'birim': 'TL', 'yonu': 'asagi'},
        {'modul': 'kalite', 'kpi_kodu': 'hata_orani', 'kpi_adi': 'Hata Oranı', 'birim': '%', 'yonu': 'asagi'},
        {'modul': 'kalite', 'kpi_kodu': 'fire_orani', 'kpi_adi': 'Fire Oranı', 'birim': '%', 'yonu': 'asagi'},
        {'modul': 'enerji', 'kpi_kodu': 'toplam_maliyet', 'kpi_adi': 'Enerji Maliyeti', 'birim': 'TL', 'yonu': 'asagi'},
        {'modul': 'enerji', 'kpi_kodu': 'birim_tuketim', 'kpi_adi': 'Birim Enerji Tüketimi', 'birim': 'kWh/adet', 'yonu': 'asagi'},
        {'modul': 'isg', 'kpi_kodu': 'kaza_sayisi', 'kpi_adi': 'İş Kazası Sayısı', 'birim': 'adet', 'yonu': 'asagi'},
        {'modul': 'isg', 'kpi_kodu': 'kayip_gun', 'kpi_adi': 'Kayıp İş Günü', 'birim': 'gün', 'yonu': 'asagi'},
        {'modul': 'stok', 'kpi_kodu': 'kritik_malzeme', 'kpi_adi': 'Kritik Stok Malzeme', 'birim': 'adet', 'yonu': 'asagi'},
        {'modul': 'personel', 'kpi_kodu': 'devamsizlik', 'kpi_adi': 'Devamsızlık Oranı', 'birim': '%', 'yonu': 'asagi'},
    ]

    @property
    def modul_adi(self):
        """Modül adını Türkçe döner."""
        return self.MODULLER.get(self.modul, self.modul)

    @property
    def periyot_adi(self):
        """Periyot adını Türkçe döner."""
        adlar = {'aylik': 'Aylık', 'haftalik': 'Haftalık', 'ceyreklik': 'Çeyreklik', 'yillik': 'Yıllık'}
        return adlar.get(self.periyot, self.periyot)

    def hedef_durumu(self, gerceklesen):
        """
        Gerçekleşen değeri hedefe göre değerlendirir.
        Returns: 'basarili' | 'uyari' | 'kritik'
        """
        if gerceklesen is None:
            return 'belirsiz'

        hedef = float(self.hedef_deger)
        gercek = float(gerceklesen)

        if self.yonu == 'yukari':
            # Yüksek iyi (OEE gibi)
            if gercek >= hedef:
                return 'basarili'
            elif self.alt_limit and gercek >= float(self.alt_limit):
                return 'uyari'
            else:
                return 'kritik'
        else:
            # Düşük iyi (hata oranı, maliyet gibi)
            if gercek <= hedef:
                return 'basarili'
            elif self.ust_limit and gercek <= float(self.ust_limit):
                return 'uyari'
            else:
                return 'kritik'

    def tutma_yuzde(self, gerceklesen):
        """Hedef tutma yüzdesini hesaplar."""
        if gerceklesen is None or float(self.hedef_deger) == 0:
            return 0

        hedef = float(self.hedef_deger)
        gercek = float(gerceklesen)

        if self.yonu == 'yukari':
            return round(min((gercek / hedef) * 100, 150), 1)
        else:
            if gercek == 0:
                return 100.0
            return round(min((hedef / gercek) * 100, 150), 1)

    def __repr__(self):
        return f'<KpiHedef {self.modul}.{self.kpi_kodu} — Hedef: {self.hedef_deger}{self.birim}>'
