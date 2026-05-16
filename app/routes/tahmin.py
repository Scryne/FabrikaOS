"""FDYS — AI Tahminleme Rotaları (Kategori 1 — Yapay Zeka Motoru)"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.utils.decorators import modul_erisim_gerekli
from app.extensions import db

tahmin_bp = Blueprint('tahmin', __name__, url_prefix='/tahmin')


import json
from app.models.tahmin import TahminKaydi

def _get_db_tahminler(tahmin_turu):
    kayitlar = TahminKaydi.query.filter_by(tahmin_turu=tahmin_turu, aktif=True).order_by(TahminKaydi.risk_skoru.desc()).all()
    sonuclar = []
    for k in kayitlar:
        meta = json.loads(k.meta_veri) if k.meta_veri else {}
        if tahmin_turu == 'bakim':
            sonuclar.append({
                'makine_id': k.kaynak_id,
                'makine_ad': k.kaynak_adi,
                'risk_skoru': k.risk_skoru,
                'tahmini_gun': k.tahmini_gun,
                'oneri': k.oneri,
                'detaylar': meta
            })
        elif tahmin_turu == 'oee':
            son_14 = meta.get('son_14gun_oee', [0])
            sonuclar.append({
                'makine_id': k.kaynak_id,
                'makine_ad': k.kaynak_adi,
                'makine_kod': meta.get('makine_kod', ''),
                'risk_skoru': k.risk_skoru,
                'oneri': k.oneri,
                'uyari': k.oneri if k.risk_skoru > 30 else '',
                'mevcut_oee': meta.get('mevcut_oee', son_14[-1] if son_14 else 0),
                'trend': meta.get('trend', 0),
                'tahmin_ort': meta.get('tahmin_ort', 0),
                'hedef_oee': meta.get('hedef_oee', 0),
                'guvenilirlik': meta.get('guvenilirlik', 0),
                'gecmis': meta.get('gecmis', {'labels': [], 'values': []}),
                'tahmin': meta.get('tahmin', {'labels': [], 'values': []})
            })
        elif tahmin_turu == 'stok':
            sonuclar.append({
                'malzeme_id': k.kaynak_id,
                'malzeme_ad': k.kaynak_adi,
                'risk_skoru': k.risk_skoru,
                'tukenme_gun': k.tahmini_gun,
                'oneri': k.oneri,
                'kritik_mi': k.risk_skoru >= 75,
                'mevcut_miktar': meta.get('mevcut_stok', 0),
                'gunluk_tuketim': meta.get('gunluk_tuketim', 0),
                'birim': meta.get('birim', 'adet')
            })
        elif tahmin_turu == 'anomali':
            tip = meta.get('tip') or meta.get('anomali_tipi', 'sistem')
            if 'enerji' in tip:
                tip = 'enerji'
            elif 'kalite' in tip:
                tip = 'kalite'
                
            deger = meta.get('deger', meta.get('guncel_tuketim_kwh', meta.get('hata_orani_trend', [0])[-1] if 'hata_orani_trend' in meta else 0))
            ortalama = meta.get('ortalama', meta.get('normal_tuketim_kwh', meta.get('normal_hata_orani', 0)))
            sapma_yuzde = meta.get('sapma_yuzde', 0)
            
            tarih_str = ''
            if k.tahmin_tarihi:
                tarih_str = k.tahmin_tarihi.strftime('%d.%m.%Y')
            elif k.olusturma_tarihi:
                tarih_str = k.olusturma_tarihi.strftime('%d.%m.%Y')
                
            sonuclar.append({
                'tip': tip,
                'kaynak_turu': k.kaynak_turu,
                'kaynak_id': k.kaynak_id,
                'kaynak_adi': k.kaynak_adi,
                'baslik': k.baslik,
                'aciklama': k.aciklama,
                'risk_skoru': k.risk_skoru,
                'tarih': tarih_str,
                'deger': deger,
                'ortalama': ortalama,
                'sapma_yuzde': sapma_yuzde,
                'birim': '%' if tip == 'kalite' else 'kW'
            })
    return sonuclar


@tahmin_bp.route('/')
@login_required
def index():
    """AI Tahminleme ana sayfası — tüm modüllerin özeti."""
    from app.services.tahmin_motoru import tahmin_motoru

    # DB'den mevcut tahminleri al
    ozet = tahmin_motoru.dashboard_ozeti()

    bakim_sonuclari = _get_db_tahminler('bakim')
    oee_sonuclari = _get_db_tahminler('oee')
    stok_sonuclari = _get_db_tahminler('stok')
    anomali_sonuclari = _get_db_tahminler('anomali')

    return render_template('tahmin/index.html',
                           ozet=ozet,
                           bakim_sonuclari=bakim_sonuclari[:10],
                           oee_sonuclari=oee_sonuclari[:10],
                           stok_sonuclari=stok_sonuclari[:10],
                           anomali_sonuclari=anomali_sonuclari[:10])


@tahmin_bp.route('/kestirimci-bakim')
@login_required
def kestirimci_bakim():
    """Kestirimci bakım detay sayfası."""
    sonuclar = _get_db_tahminler('bakim')
    return render_template('tahmin/kestirimci_bakim.html', sonuclar=sonuclar)


@tahmin_bp.route('/oee-tahmin')
@login_required
def oee_tahmin():
    """OEE trend tahmini detay sayfası."""
    sonuclar = _get_db_tahminler('oee')
    return render_template('tahmin/oee_tahmin.html', sonuclar=sonuclar)


@tahmin_bp.route('/stok-tahmin')
@login_required
def stok_tahmin():
    """Stok tükenme tahminleri sayfası."""
    sonuclar = _get_db_tahminler('stok')
    return render_template('tahmin/stok_tahmin.html', sonuclar=sonuclar)


@tahmin_bp.route('/anomaliler')
@login_required
def anomaliler():
    """Anomali tespiti sayfası."""
    sonuclar = _get_db_tahminler('anomali')
    return render_template('tahmin/anomaliler.html', sonuclar=sonuclar)


# ── JSON API Endpoint'leri ──

@tahmin_bp.route('/api/tahminler')
@login_required
def api_tahminler():
    """Tüm aktif tahminleri JSON olarak döner."""
    from app.models.tahmin import TahminKaydi
    tahminler = TahminKaydi.query.filter_by(aktif=True).order_by(
        TahminKaydi.risk_skoru.desc()
    ).all()

    return jsonify({
        'toplam': len(tahminler),
        'tahminler': [{
            'id': t.id,
            'turu': t.tahmin_turu,
            'kaynak': t.kaynak_adi,
            'baslik': t.baslik,
            'risk_skoru': float(t.risk_skoru),
            'risk_seviyesi': t.risk_seviyesi,
            'tahmini_gun': t.tahmini_gun,
            'oneri': t.oneri,
            'tarih': t.olusturma_tarihi.strftime('%d.%m.%Y %H:%M') if t.olusturma_tarihi else None
        } for t in tahminler]
    })


@tahmin_bp.route('/api/hesapla', methods=['POST'])
@login_required
def api_hesapla():
    """Tüm tahminleri yeniden hesaplar (AJAX)."""
    from app.services.tahmin_motoru import tahmin_motoru
    try:
        sonuclar = tahmin_motoru.tum_tahminleri_calistir()
        return jsonify({
            'status': 'success',
            'mesaj': 'Tüm tahminler başarıyla güncellendi.',
            'ozet': sonuclar['ozet']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'mesaj': str(e)}), 500


@tahmin_bp.route('/api/makine/<int:makine_id>/bakim-tahmini')
@login_required
def api_makine_bakim_tahmini(makine_id):
    """Tekil makine bakım tahmini JSON."""
    from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
    sonuc = kestirimci_bakim_servisi.makine_tahmini(makine_id)
    if sonuc:
        return jsonify(sonuc)
    return jsonify({'error': 'Makine bulunamadı'}), 404


@tahmin_bp.route('/api/oee-tahmin/<int:makine_id>')
@login_required
def api_oee_tahmini(makine_id):
    """Tekil makine OEE tahmini JSON."""
    from app.services.ai.oee_tahmin import oee_tahmin_servisi
    sonuc = oee_tahmin_servisi.makine_tahmini(makine_id)
    if sonuc:
        return jsonify(sonuc)
    return jsonify({'error': 'Yeterli veri yok veya makine bulunamadı'}), 404
