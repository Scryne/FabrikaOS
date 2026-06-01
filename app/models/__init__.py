"""
FDYS — Veritabanı Modelleri

Tüm modeller buradan import edilir.
18+ tablo, modüllere göre gruplanmıştır.
"""

from app.models.kullanici import Kullanici, DenetimIzi
from app.models.personel import Calisan, VardiyaPlani, IzinTalebi
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
from app.models.stok import Malzeme, StokHareketi, Tedarikci
from app.models.kalite import HataKaydi, DuzelticiFaaliyet
from app.models.enerji import EnerjiTuketimi
from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi, SaglikMuayenesi, IsgDokumani
from app.models.bildirim import Bildirim
from app.models.tahmin import TahminKaydi
from app.models.is_emri import IsEmri, IsEmriYorum
from app.models.analitik import KpiHedef
from app.models.dosya import DosyaEki
from app.models.eposta import EpostaAyarlari
from app.models.kurumsal import KurumsalAyarlar
from app.models.ik import (
    SavunmaTutanak, FazlaMesai, SertifikaTakip,
    MaasSkalasi, ZimmetKaydi, GirisCikisEvrak
)
from app.models.crm import (
    Ortak, Firma, FirmaYetkilisi, CrmIletisimGecmisi
)
from app.models.sozlesme import (
    Sozlesme, KiraKontrat, SigortaPolice, StandartMetin
)
from app.models.talep import Talep, TalepGecmisi
from app.models.dis_kullanici import DisKullanici, Borc, Tahsilat
from app.models.dys import Dokuman
from app.models.duyuru import Duyuru, DuyuruOkunma
from app.models.satin_alma import (
    SatinAlmaTalebi, SatinAlmaSiparis, TeklifKarsilastirma
)

__all__ = [
    'Kullanici', 'DenetimIzi',
    'Calisan', 'VardiyaPlani', 'IzinTalebi',
    'Makine', 'UretimVerisi', 'ArizaKaydi', 'BakimKaydi', 'DurusKaydi',
    'Malzeme', 'StokHareketi', 'Tedarikci',
    'HataKaydi', 'DuzelticiFaaliyet',
    'EnerjiTuketimi',
    'IsKazasi', 'RiskDegerlendirme', 'IsgEgitimi', 'SaglikMuayenesi', 'IsgDokumani',
    'Bildirim',
    'TahminKaydi',
    'IsEmri', 'IsEmriYorum',
    'KpiHedef',
    'DosyaEki',
    'EpostaAyarlari',
    'KurumsalAyarlar',
    'SavunmaTutanak', 'FazlaMesai', 'SertifikaTakip',
    'MaasSkalasi', 'ZimmetKaydi', 'GirisCikisEvrak',
    'Ortak', 'Firma', 'FirmaYetkilisi', 'CrmIletisimGecmisi',
    'Sozlesme', 'KiraKontrat', 'SigortaPolice', 'StandartMetin',
    'Talep', 'TalepGecmisi',
    'DisKullanici', 'Borc', 'Tahsilat',
    'Dokuman',
    'Duyuru', 'DuyuruOkunma',
    'SatinAlmaTalebi', 'SatinAlmaSiparis', 'TeklifKarsilastirma',
]

