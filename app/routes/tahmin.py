"""FDYS — AI Tahminleme Rotaları (Kategori 1 — Yapay Zeka Motoru)"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.utils.decorators import modul_erisim_gerekli
from app.extensions import db

tahmin_bp = Blueprint('tahmin', __name__, url_prefix='/tahmin')


@tahmin_bp.route('/')
@login_required
def index():
    """AI Tahminleme ana sayfası — tüm modüllerin özeti."""
    from app.services.tahmin_motoru import tahmin_motoru

    # DB'den mevcut tahminleri al
    ozet = tahmin_motoru.dashboard_ozeti()

    # Alt modüllerin verilerini topla
    from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
    from app.services.ai.oee_tahmin import oee_tahmin_servisi
    from app.services.ai.stok_tahmin import stok_tahmin_servisi
    from app.services.ai.anomali_tespit import anomali_tespit_servisi

    bakim_sonuclari = kestirimci_bakim_servisi.tum_makineleri_analiz_et()
    oee_sonuclari = oee_tahmin_servisi.tum_makineleri_analiz_et()
    stok_sonuclari = stok_tahmin_servisi.tum_malzemeleri_analiz_et()
    anomali_sonuclari = anomali_tespit_servisi.tum_anomalileri_tespit_et()

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
    from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
    sonuclar = kestirimci_bakim_servisi.tum_makineleri_analiz_et()
    return render_template('tahmin/kestirimci_bakim.html', sonuclar=sonuclar)


@tahmin_bp.route('/oee-tahmin')
@login_required
def oee_tahmin():
    """OEE trend tahmini detay sayfası."""
    from app.services.ai.oee_tahmin import oee_tahmin_servisi
    sonuclar = oee_tahmin_servisi.tum_makineleri_analiz_et()
    return render_template('tahmin/oee_tahmin.html', sonuclar=sonuclar)


@tahmin_bp.route('/stok-tahmin')
@login_required
def stok_tahmin():
    """Stok tükenme tahminleri sayfası."""
    from app.services.ai.stok_tahmin import stok_tahmin_servisi
    sonuclar = stok_tahmin_servisi.tum_malzemeleri_analiz_et()
    return render_template('tahmin/stok_tahmin.html', sonuclar=sonuclar)


@tahmin_bp.route('/anomaliler')
@login_required
def anomaliler():
    """Anomali tespiti sayfası."""
    from app.services.ai.anomali_tespit import anomali_tespit_servisi
    sonuclar = anomali_tespit_servisi.tum_anomalileri_tespit_et()
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
