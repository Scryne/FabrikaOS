"""
FDYS — Çapraz Modül Korelasyon Servisi v2.0
Kategori 4.1 — Gelişmiş Analitik

v2.0 Yenilikler:
    - Operatör trend göstergesi (iyileşme/kötüleşme)
    - Pearson korelasyon katsayısı (enerji×üretim)
    - Chi-square istatistiksel anlamlılık testi (hata×zaman)
    - Aksiyon önerili insight kartları
"""
import math
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, case
from app.extensions import db
from app.models.makine import Makine, UretimVerisi, ArizaKaydi
from app.models.personel import Calisan
from app.models.kalite import HataKaydi
from app.models.enerji import EnerjiTuketimi

logger = logging.getLogger(__name__)


class KorelasyonServisi:
    """Operatör×Makine, Enerji×Üretim, Hata×Zaman korelasyon analizleri."""

    def operator_makine_matrisi(self, gun=30):
        """Operatör × Makine OEE performans matrisi + trend göstergesi."""
        bas = datetime.now(timezone.utc).date() - timedelta(days=gun)
        onceki_bas = bas - timedelta(days=gun)

        # Mevcut dönem
        veriler = db.session.query(
            UretimVerisi.calisan_id,
            UretimVerisi.makine_id,
            func.avg(UretimVerisi.oee_yuzde).label('ort_oee'),
            func.sum(UretimVerisi.gercek_uretim).label('toplam_uretim'),
            func.sum(UretimVerisi.hatali_uretim).label('toplam_hata'),
            func.count(UretimVerisi.id).label('vardiya_sayisi')
        ).filter(UretimVerisi.tarih >= bas)\
         .group_by(UretimVerisi.calisan_id, UretimVerisi.makine_id).all()

        if not veriler:
            return {'operatorler': [], 'makineler': [], 'matris': [], 'insightlar': []}

        # Önceki dönem (trend hesabı için)
        onceki_veriler = db.session.query(
            UretimVerisi.calisan_id,
            UretimVerisi.makine_id,
            func.avg(UretimVerisi.oee_yuzde).label('ort_oee'),
        ).filter(
            UretimVerisi.tarih >= onceki_bas,
            UretimVerisi.tarih < bas
        ).group_by(UretimVerisi.calisan_id, UretimVerisi.makine_id).all()

        onceki_map = {}
        for v in onceki_veriler:
            onceki_map[(v.calisan_id, v.makine_id)] = float(v.ort_oee or 0)

        op_ids = sorted(set(v.calisan_id for v in veriler))
        mk_ids = sorted(set(v.makine_id for v in veriler))
        operatorler = {c.id: c.ad_soyad for c in Calisan.query.filter(Calisan.id.in_(op_ids)).all()}
        makineler_db = {m.id: m.kod for m in Makine.query.filter(Makine.id.in_(mk_ids)).all()}

        veri_map = {}
        for v in veriler:
            toplam = int(v.toplam_uretim or 0)
            hata = int(v.toplam_hata or 0)
            hata_oran = round((hata / toplam) * 100, 2) if toplam > 0 else 0
            mevcut_oee = round(float(v.ort_oee or 0), 1)
            onceki_oee = onceki_map.get((v.calisan_id, v.makine_id))

            # Trend hesabı
            trend = None
            trend_yon = 'stabil'
            if onceki_oee and onceki_oee > 0:
                trend = round(mevcut_oee - onceki_oee, 1)
                if trend > 2:
                    trend_yon = 'yukseliyor'
                elif trend < -2:
                    trend_yon = 'dusuyor'

            veri_map[(v.calisan_id, v.makine_id)] = {
                'oee': mevcut_oee,
                'uretim': toplam,
                'hata_orani': hata_oran,
                'vardiya': int(v.vardiya_sayisi),
                'trend': trend,
                'trend_yon': trend_yon,
            }

        matris = []
        for oid in op_ids:
            satir = []
            for mid in mk_ids:
                satir.append(veri_map.get(
                    (oid, mid),
                    {'oee': None, 'uretim': 0, 'hata_orani': 0, 'vardiya': 0, 'trend': None, 'trend_yon': 'stabil'}
                ))
            matris.append(satir)

        # Insight: her operatörün en iyi makinesi + aksiyon önerisi
        insightlar = []
        for i, oid in enumerate(op_ids):
            gecerli_hucre = [(j, matris[i][j]) for j in range(len(mk_ids)) if matris[i][j]['oee']]
            if not gecerli_hucre:
                continue

            en_iyi_j, en_iyi = max(gecerli_hucre, key=lambda x: x[1]['oee'])
            insightlar.append({
                'icon': 'bi-person-check', 'seviye': 'info',
                'baslik': f"{operatorler.get(oid, '?')}, {makineler_db.get(mk_ids[en_iyi_j], '?')}'de en yüksek OEE",
                'aciklama': f"Ortalama OEE: %{en_iyi['oee']} ({en_iyi['vardiya']} vardiya)",
                'deger': en_iyi['oee'],
                'aksiyon': f"{operatorler.get(oid, '?')} bu makineye öncelikli olarak atanmalı."
            })

            # Düşüş trendi uyarısı
            dusen = [(j, h) for j, h in gecerli_hucre if h.get('trend_yon') == 'dusuyor']
            if dusen:
                j, h = dusen[0]
                insightlar.append({
                    'icon': 'bi-graph-down-arrow', 'seviye': 'warning',
                    'baslik': f"{operatorler.get(oid, '?')}, {makineler_db.get(mk_ids[j], '?')}'de düşüş trendi",
                    'aciklama': f"OEE {abs(h['trend'])} puan düştü. Eğitim veya rotasyon önerilir.",
                    'deger': h['oee'],
                    'aksiyon': 'Operatör eğitim planı oluşturulmalı veya makine rotasyonu yapılmalı.'
                })

        insightlar.sort(key=lambda x: x.get('deger', 0), reverse=True)

        return {
            'operatorler': [{'id': oid, 'ad': operatorler.get(oid, '?')} for oid in op_ids],
            'makineler': [{'id': mid, 'kod': makineler_db.get(mid, '?')} for mid in mk_ids],
            'matris': matris, 'insightlar': insightlar[:5]
        }

    def enerji_uretim_korelasyonu(self, gun=30):
        """Makine bazlı enerji verimliliği + Pearson korelasyon katsayısı."""
        bas = datetime.now(timezone.utc).date() - timedelta(days=gun)
        makineler = Makine.query.filter_by(aktif=True).all()
        sonuclar = []

        tum_uretimler = []
        tum_enerjiler = []

        for m in makineler:
            uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
                .filter(UretimVerisi.makine_id == m.id, UretimVerisi.tarih >= bas).scalar() or 0
            enerji = db.session.query(func.sum(EnerjiTuketimi.miktar))\
                .filter(EnerjiTuketimi.makine_id == m.id, EnerjiTuketimi.enerji_turu == 'elektrik',
                        EnerjiTuketimi.donem_baslangic >= bas).scalar() or 0

            uretim_int = int(uretim)
            enerji_float = float(enerji)

            if uretim_int > 0 and enerji_float > 0:
                birim = round(enerji_float / uretim_int, 3)
                sonuclar.append({
                    'makine_id': m.id, 'makine_kod': m.kod, 'makine_ad': m.ad,
                    'toplam_uretim': uretim_int, 'toplam_enerji': round(enerji_float, 1),
                    'birim_enerji': birim
                })
                tum_uretimler.append(uretim_int)
                tum_enerjiler.append(enerji_float)

        sonuclar.sort(key=lambda x: x['birim_enerji'])

        for i, s in enumerate(sonuclar):
            s['sira'] = i + 1
            s['verimlilik'] = 'yuksek' if i < len(sonuclar) / 3 else ('orta' if i < 2 * len(sonuclar) / 3 else 'dusuk')

        # Pearson korelasyon katsayısı hesapla
        pearson_r = self._pearson_korelasyon(tum_uretimler, tum_enerjiler)

        return {
            'makineler': sonuclar,
            'pearson_r': pearson_r,
            'pearson_yorum': self._pearson_yorum(pearson_r),
        }

    def _pearson_korelasyon(self, x_list, y_list):
        """Pearson korelasyon katsayısı hesaplar (-1 ile +1 arası)."""
        n = len(x_list)
        if n < 3:
            return None

        x_mean = sum(x_list) / n
        y_mean = sum(y_list) / n

        pay = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_list, y_list))
        payda_x = math.sqrt(sum((x - x_mean) ** 2 for x in x_list))
        payda_y = math.sqrt(sum((y - y_mean) ** 2 for y in y_list))

        if payda_x == 0 or payda_y == 0:
            return None

        return round(pay / (payda_x * payda_y), 3)

    def _pearson_yorum(self, r):
        """Pearson katsayısını yorumlar."""
        if r is None:
            return 'Yeterli veri yok.'
        r_abs = abs(r)
        if r_abs >= 0.8:
            yon = 'pozitif' if r > 0 else 'negatif'
            return f'Çok güçlü {yon} korelasyon (r={r}). Üretim ve enerji tüketimi güçlü şekilde bağlı.'
        elif r_abs >= 0.5:
            return f'Orta düzey korelasyon (r={r}). Beklenen bir ilişki mevcut.'
        elif r_abs >= 0.3:
            return f'Zayıf korelasyon (r={r}). İlişki belirsiz.'
        else:
            return f'Korelasyon yok (r={r}). Üretim ve enerji bağımsız değişkenler gibi davranıyor.'

    def hata_zaman_paterni(self, gun=60):
        """Hata kayıtlarının gün×vardiya heatmap dağılımı + chi-square testi."""
        bas = datetime.now(timezone.utc) - timedelta(days=gun)
        hatalar = HataKaydi.query.filter(HataKaydi.tarih >= bas).all()
        gun_adlari = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        vardiyalar = ['sabah', 'ogleden_sonra', 'gece']
        matris = [[0] * 3 for _ in range(7)]
        toplam = 0
        for h in hatalar:
            tarih = h.tarih if isinstance(h.tarih, datetime) else datetime.combine(h.tarih, datetime.min.time())
            gun_idx = tarih.weekday()
            v_idx = vardiyalar.index(h.vardiya) if h.vardiya in vardiyalar else (
                0 if tarih.hour < 14 else (1 if tarih.hour < 22 else 2))
            matris[gun_idx][v_idx] += h.adet or 1
            toplam += h.adet or 1

        # En yoğun zaman dilimi
        max_val, max_gun, max_var = 0, 0, 0
        for i in range(7):
            for j in range(3):
                if matris[i][j] > max_val:
                    max_val, max_gun, max_var = matris[i][j], i, j

        # Chi-square anlamlılık testi
        chi_square = self._chi_square_test(matris, toplam)

        insight = None
        if toplam > 0 and max_val > 0:
            yuzde = round((max_val / toplam) * 100, 1)
            vardiya_ad = {'sabah': 'Sabah', 'ogleden_sonra': 'Öğleden Sonra', 'gece': 'Gece'}
            anlamli_mi = chi_square.get('anlamli', False) if chi_square else False

            aksiyon = 'Dağılım rastgele görünüyor, genel iyileştirme önerilir.'
            if anlamli_mi:
                aksiyon = f"{gun_adlari[max_gun]} {vardiya_ad.get(vardiyalar[max_var], '')} vardiyası için özel eğitim planı oluşturulmalı."

            insight = {
                'icon': 'bi-clock-history', 'seviye': 'warning',
                'baslik': f"Hataların %{yuzde} kadarı {gun_adlari[max_gun]} {vardiya_ad.get(vardiyalar[max_var], '')} vardiyasında",
                'aciklama': f"Son {gun} günde toplam {toplam} hata kaydı analiz edildi."
                            + (f" (İstatistiksel olarak anlamlı, p<0.05)" if anlamli_mi else " (Rastgele dağılım)"),
                'deger': yuzde,
                'aksiyon': aksiyon,
            }
        return {
            'gunler': gun_adlari, 'vardiyalar': ['Sabah', 'Öğleden Sonra', 'Gece'],
            'matris': matris, 'toplam': toplam, 'insight': insight,
            'chi_square': chi_square,
        }

    def _chi_square_test(self, matris, toplam):
        """Basitleştirilmiş chi-square bağımsızlık testi."""
        if toplam < 10:
            return None

        satir_toplamlari = [sum(row) for row in matris]
        sutun_toplamlari = [sum(matris[i][j] for i in range(7)) for j in range(3)]

        chi2 = 0
        for i in range(7):
            for j in range(3):
                beklenen = (satir_toplamlari[i] * sutun_toplamlari[j]) / toplam if toplam > 0 else 0
                if beklenen > 0:
                    chi2 += ((matris[i][j] - beklenen) ** 2) / beklenen

        # Serbestlik derecesi = (satır-1) * (sütun-1) = 6*2 = 12
        # p < 0.05 için chi2 > 21.026 (df=12)
        df = 12
        kritik_deger = 21.026
        anlamli = chi2 > kritik_deger

        return {
            'chi2': round(chi2, 2),
            'df': df,
            'kritik_deger': kritik_deger,
            'anlamli': anlamli,
            'yorum': 'Hata dağılımı istatistiksel olarak anlamlı farklılık gösteriyor.' if anlamli
                      else 'Hata dağılımı rastgele, anlamlı fark yok.'
        }

    def akilli_insightlar(self):
        """Tüm korelasyon analizlerinden birleşik insight kartları üretir."""
        insightlar = []
        try:
            om = self.operator_makine_matrisi()
            insightlar.extend(om.get('insightlar', [])[:2])
        except Exception as e:
            logger.warning(f"Operatör-makine insight hatası: {e}")
        try:
            eu = self.enerji_uretim_korelasyonu()
            eu_makineler = eu.get('makineler', []) if isinstance(eu, dict) else eu
            if eu_makineler:
                en_verimli = eu_makineler[0]
                insightlar.append({
                    'icon': 'bi-lightning-charge', 'seviye': 'success',
                    'baslik': f"En verimli makine: {en_verimli['makine_kod']}",
                    'aciklama': f"Birim enerji: {en_verimli['birim_enerji']} kWh/adet",
                    'deger': en_verimli['birim_enerji'],
                    'aksiyon': 'Bu makinenin operasyonel parametreleri diğer makinelere referans olarak kullanılabilir.'
                })
                if len(eu_makineler) > 1:
                    en_verimsiz = eu_makineler[-1]
                    fark = round(en_verimsiz['birim_enerji'] / en_verimli['birim_enerji'], 1) if en_verimli['birim_enerji'] > 0 else 0
                    insightlar.append({
                        'icon': 'bi-exclamation-triangle', 'seviye': 'danger',
                        'baslik': f"En verimsiz makine: {en_verimsiz['makine_kod']}",
                        'aciklama': f"Birim enerji: {en_verimsiz['birim_enerji']} kWh/adet — {fark}x fark",
                        'deger': en_verimsiz['birim_enerji'],
                        'aksiyon': 'Enerji verimliliği denetimi yapılmalı, motor ve kompresör bakımı kontrol edilmeli.'
                    })
        except Exception as e:
            logger.warning(f"Enerji-üretim insight hatası: {e}")
        try:
            hz = self.hata_zaman_paterni()
            if hz.get('insight'):
                insightlar.append(hz['insight'])
        except Exception as e:
            logger.warning(f"Hata-zaman insight hatası: {e}")

        return insightlar[:5]


korelasyon_servisi = KorelasyonServisi()
