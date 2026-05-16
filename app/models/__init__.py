"""
FDYS — Veritabanı Modelleri

Tüm modeller buradan import edilir.
18 tablo, 6 modüle göre gruplanmıştır.
"""

from app.models.kullanici import Kullanici, DenetimIzi
from app.models.personel import Calisan, VardiyaPlani, IzinTalebi
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
from app.models.stok import Malzeme, StokHareketi, Tedarikci
from app.models.kalite import HataKaydi, DuzelticiFaaliyet
from app.models.enerji import EnerjiTuketimi
from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi
from app.models.bildirim import Bildirim
from app.models.tahmin import TahminKaydi
from app.models.is_emri import IsEmri, IsEmriYorum
from app.models.analitik import KpiHedef
from app.models.dosya import DosyaEki
from app.models.eposta import EpostaAyarlari
from app.models.kurumsal import KurumsalAyarlar

__all__ = [
    'Kullanici', 'DenetimIzi',
    'Calisan', 'VardiyaPlani', 'IzinTalebi',
    'Makine', 'UretimVerisi', 'ArizaKaydi', 'BakimKaydi', 'DurusKaydi',
    'Malzeme', 'StokHareketi', 'Tedarikci',
    'HataKaydi', 'DuzelticiFaaliyet',
    'EnerjiTuketimi',
    'IsKazasi', 'RiskDegerlendirme', 'IsgEgitimi',
    'Bildirim',
    'TahminKaydi',
    'IsEmri', 'IsEmriYorum',
    'KpiHedef',
    'DosyaEki',
    'EpostaAyarlari',
    'KurumsalAyarlar',
]
