"""
FDYS — Excel/CSV Import Servisi
Faz 5 — Toplu Veri İçe Aktarma
"""

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

import openpyxl
from app.extensions import db

logger = logging.getLogger(__name__)


@dataclass
class ImportSonuc:
    basarili_sayisi: int = 0
    hatali_sayisi: int = 0
    atlanan_sayisi: int = 0
    toplam_satir: int = 0
    hatalar: list = field(default_factory=list)

    @property
    def basarili_mi(self):
        return self.basarili_sayisi > 0


class ImportService:

    @staticmethod
    def _parse_excel(file_storage) -> list:
        wb = openpyxl.load_workbook(file_storage, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        basliklar = [str(h).strip().lower() if h else '' for h in rows[0]]
        sonuc = []
        for row in rows[1:]:
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue
            satir = {}
            for i, baslik in enumerate(basliklar):
                satir[baslik] = row[i] if i < len(row) else None
            sonuc.append(satir)
        return sonuc

    @staticmethod
    def _parse_csv(file_storage) -> list:
        stream = io.StringIO(file_storage.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream, delimiter=';')
        return [{k.strip().lower(): (v.strip() if v else '') for k, v in row.items()} for row in reader]

    def _dosya_oku(self, file_storage) -> list:
        dosya_adi = file_storage.filename.lower()
        if dosya_adi.endswith(('.xlsx', '.xls')):
            return self._parse_excel(file_storage)
        elif dosya_adi.endswith('.csv'):
            return self._parse_csv(file_storage)
        raise ValueError("Desteklenmeyen dosya formatı. .xlsx veya .csv kullanın.")

    @staticmethod
    def _zorunlu(satir, alan, no, hatalar):
        val = satir.get(alan)
        if val is None or str(val).strip() == '':
            hatalar.append({'satir': no, 'alan': alan, 'mesaj': f'"{alan}" zorunludur.'})
            return None
        return str(val).strip()

    @staticmethod
    def _sayi(satir, alan, no, hatalar, zorunlu=False):
        val = satir.get(alan)
        if val is None or str(val).strip() == '':
            if zorunlu:
                hatalar.append({'satir': no, 'alan': alan, 'mesaj': f'"{alan}" zorunludur.'})
            return None
        try:
            return Decimal(str(val).replace(',', '.'))
        except (InvalidOperation, ValueError):
            hatalar.append({'satir': no, 'alan': alan, 'mesaj': f'"{alan}" geçerli bir sayı olmalıdır.'})
            return None

    @staticmethod
    def _tarih(satir, alan, no, hatalar, zorunlu=False):
        val = satir.get(alan)
        if val is None or str(val).strip() == '':
            if zorunlu:
                hatalar.append({'satir': no, 'alan': alan, 'mesaj': f'"{alan}" zorunludur.'})
            return None
        if isinstance(val, datetime):
            return val.date()
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(str(val).strip(), fmt).date()
            except ValueError:
                continue
        hatalar.append({'satir': no, 'alan': alan, 'mesaj': f'Geçersiz tarih formatı (GG.AA.YYYY).'})
        return None

    def _commit(self, sonuc, tip):
        if sonuc.basarili_sayisi > 0:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"{tip} import commit hatası: {e}")
                sonuc.hatalar.append({'satir': 0, 'alan': '-', 'mesaj': f'Veritabanı hatası: {str(e)}'})
                sonuc.basarili_sayisi = 0

    def import_malzeme(self, file_storage) -> ImportSonuc:
        from app.models.stok import Malzeme
        sonuc = ImportSonuc()
        try:
            satirlar = self._dosya_oku(file_storage)
        except Exception as e:
            sonuc.hatalar.append({'satir': 0, 'alan': '-', 'mesaj': str(e)})
            return sonuc
        sonuc.toplam_satir = len(satirlar)
        for i, s in enumerate(satirlar, start=2):
            h = []
            kod = self._zorunlu(s, 'kod', i, h)
            ad = self._zorunlu(s, 'ad', i, h)
            birim = self._zorunlu(s, 'birim', i, h)
            birim_fiyat = self._sayi(s, 'birim fiyat', i, h)
            minimum_stok = self._sayi(s, 'minimum stok', i, h)
            mevcut = self._sayi(s, 'mevcut miktar', i, h)
            if h:
                sonuc.hatali_sayisi += 1
                sonuc.hatalar.extend(h)
                continue
            if Malzeme.query.filter_by(kod=kod).first():
                sonuc.atlanan_sayisi += 1
                sonuc.hatalar.append({'satir': i, 'alan': 'kod', 'mesaj': f'"{kod}" zaten mevcut.'})
                continue
            db.session.add(Malzeme(
                kod=kod, ad=ad, birim=birim,
                kategori=(str(s.get('kategori', '')).strip() or None),
                lokasyon=(str(s.get('lokasyon', '')).strip() or None),
                birim_fiyat=birim_fiyat, minimum_stok=minimum_stok or 0, mevcut_miktar=mevcut or 0
            ))
            sonuc.basarili_sayisi += 1
        self._commit(sonuc, 'Malzeme')
        return sonuc

    def import_calisan(self, file_storage) -> ImportSonuc:
        from app.models.personel import Calisan
        sonuc = ImportSonuc()
        try:
            satirlar = self._dosya_oku(file_storage)
        except Exception as e:
            sonuc.hatalar.append({'satir': 0, 'alan': '-', 'mesaj': str(e)})
            return sonuc
        sonuc.toplam_satir = len(satirlar)
        for i, s in enumerate(satirlar, start=2):
            h = []
            sicil = self._zorunlu(s, 'sicil no', i, h)
            ad = self._zorunlu(s, 'ad soyad', i, h)
            dept = self._zorunlu(s, 'departman', i, h)
            poz = self._zorunlu(s, 'pozisyon', i, h)
            tarih = self._tarih(s, 'işe başlama', i, h, zorunlu=True)
            if h:
                sonuc.hatali_sayisi += 1
                sonuc.hatalar.extend(h)
                continue
            if Calisan.query.filter_by(sicil_no=sicil).first():
                sonuc.atlanan_sayisi += 1
                sonuc.hatalar.append({'satir': i, 'alan': 'sicil no', 'mesaj': f'"{sicil}" zaten mevcut.'})
                continue
            db.session.add(Calisan(
                sicil_no=sicil, ad_soyad=ad, departman=dept, pozisyon=poz, ise_baslama=tarih,
                telefon=(str(s.get('telefon', '')).strip() or None),
                eposta=(str(s.get('e-posta', '') or s.get('eposta', '')).strip() or None),
                ucret=self._sayi(s, 'ücret', i, [])
            ))
            sonuc.basarili_sayisi += 1
        self._commit(sonuc, 'Çalışan')
        return sonuc

    def import_makine(self, file_storage) -> ImportSonuc:
        from app.models.makine import Makine
        sonuc = ImportSonuc()
        try:
            satirlar = self._dosya_oku(file_storage)
        except Exception as e:
            sonuc.hatalar.append({'satir': 0, 'alan': '-', 'mesaj': str(e)})
            return sonuc
        sonuc.toplam_satir = len(satirlar)
        for i, s in enumerate(satirlar, start=2):
            h = []
            kod = self._zorunlu(s, 'kod', i, h)
            ad = self._zorunlu(s, 'ad', i, h)
            kapasite = self._sayi(s, 'teorik kapasite', i, h, zorunlu=True)
            tarih = self._tarih(s, 'satın alma tarihi', i, h, zorunlu=True)
            if h:
                sonuc.hatali_sayisi += 1
                sonuc.hatalar.extend(h)
                continue
            if Makine.query.filter_by(kod=kod).first():
                sonuc.atlanan_sayisi += 1
                sonuc.hatalar.append({'satir': i, 'alan': 'kod', 'mesaj': f'"{kod}" zaten mevcut.'})
                continue
            oee = self._sayi(s, 'hedef oee', i, [])
            bakim = self._sayi(s, 'bakım periyodu (gün)', i, [])
            db.session.add(Makine(
                kod=kod, ad=ad, teorik_kapasite=int(kapasite), satin_alma_tarihi=tarih,
                marka=(str(s.get('marka', '')).strip() or None),
                model=(str(s.get('model', '')).strip() or None),
                lokasyon=(str(s.get('lokasyon', '')).strip() or None),
                hedef_oee=oee or 85, periyodik_bakim_gun=int(bakim) if bakim else 90
            ))
            sonuc.basarili_sayisi += 1
        self._commit(sonuc, 'Makine')
        return sonuc


import_service = ImportService()
