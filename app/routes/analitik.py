"""FDYS — Gelişmiş Analitik ve Karar Destek Rotaları (Kategori 4)"""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.utils.decorators import role_required
from app.models.makine import Makine
from app.models.analitik import KpiHedef
from datetime import datetime, timezone

analitik_bp = Blueprint('analitik', __name__, url_prefix='/analitik')


@analitik_bp.route('/')
@login_required
@role_required('yonetici')
def index():
    """Ana analitik sayfası — 4 sekme."""
    makineler = Makine.query.filter_by(aktif=True).order_by(Makine.kod).all()
    bugun = datetime.now(timezone.utc)
    return render_template('analitik/index.html', makineler=makineler, yil=bugun.year, ay=bugun.month)


# ══════════════════════════════════════
#  Çapraz Korelasyon API'leri
# ══════════════════════════════════════

@analitik_bp.route('/api/korelasyon/operator-makine')
@login_required
@role_required('yonetici')
def api_operator_makine():
    from app.services.analitik.korelasyon import korelasyon_servisi
    gun = request.args.get('gun', 30, type=int)
    return jsonify(korelasyon_servisi.operator_makine_matrisi(gun))


@analitik_bp.route('/api/korelasyon/enerji-uretim')
@login_required
@role_required('yonetici')
def api_enerji_uretim():
    from app.services.analitik.korelasyon import korelasyon_servisi
    gun = request.args.get('gun', 30, type=int)
    return jsonify(korelasyon_servisi.enerji_uretim_korelasyonu(gun))


@analitik_bp.route('/api/korelasyon/hata-zaman')
@login_required
@role_required('yonetici')
def api_hata_zaman():
    from app.services.analitik.korelasyon import korelasyon_servisi
    gun = request.args.get('gun', 60, type=int)
    return jsonify(korelasyon_servisi.hata_zaman_paterni(gun))


@analitik_bp.route('/api/korelasyon/insightlar')
@login_required
@role_required('yonetici')
def api_insightlar():
    from app.services.analitik.korelasyon import korelasyon_servisi
    return jsonify(korelasyon_servisi.akilli_insightlar())


# ══════════════════════════════════════
#  Karşılaştırmalı Analiz API'leri
# ══════════════════════════════════════

@analitik_bp.route('/api/karsilastir/makine')
@login_required
@role_required('yonetici')
def api_makine_karsilastir():
    from app.services.analitik.karsilastirma import karsilastirma_servisi
    m1 = request.args.get('m1', type=int)
    m2 = request.args.get('m2', type=int)
    if not m1 or not m2:
        return jsonify({'error': 'İki makine seçilmelidir'}), 400
    bas = request.args.get('bas')
    bit = request.args.get('bit')
    try:
        bas_d = datetime.strptime(bas, '%Y-%m-%d').date() if bas else None
        bit_d = datetime.strptime(bit, '%Y-%m-%d').date() if bit else None
    except ValueError:
        bas_d = bit_d = None
    sonuc = karsilastirma_servisi.makine_karsilastir(m1, m2, bas_d, bit_d)
    if not sonuc:
        return jsonify({'error': 'Makine bulunamadı'}), 404
    return jsonify(sonuc)


@analitik_bp.route('/api/karsilastir/donem')
@login_required
@role_required('yonetici')
def api_donem_karsilastir():
    from app.services.analitik.karsilastirma import karsilastirma_servisi
    try:
        d1_bas = datetime.strptime(request.args['d1_bas'], '%Y-%m-%d').date()
        d1_bit = datetime.strptime(request.args['d1_bit'], '%Y-%m-%d').date()
        d2_bas = datetime.strptime(request.args['d2_bas'], '%Y-%m-%d').date()
        d2_bit = datetime.strptime(request.args['d2_bit'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        return jsonify({'error': 'Geçersiz tarih parametreleri'}), 400
    return jsonify(karsilastirma_servisi.donem_karsilastir(d1_bas, d1_bit, d2_bas, d2_bit))


@analitik_bp.route('/api/karsilastir/vardiya')
@login_required
@role_required('yonetici')
def api_vardiya_karsilastir():
    from app.services.analitik.karsilastirma import karsilastirma_servisi
    gun = request.args.get('gun', 30, type=int)
    return jsonify(karsilastirma_servisi.vardiya_karsilastir(gun))


# ══════════════════════════════════════
#  KPI Hedef Yönetimi
# ══════════════════════════════════════

@analitik_bp.route('/api/kpi/ozet')
@login_required
@role_required('yonetici')
def api_kpi_ozet():
    from app.services.analitik.kpi_servisi import kpi_servisi
    yil = request.args.get('yil', datetime.now(timezone.utc).year, type=int)
    ay = request.args.get('ay', datetime.now(timezone.utc).month, type=int)
    return jsonify(kpi_servisi.kpi_dashboard_ozeti(yil, ay))


@analitik_bp.route('/kpi/ekle', methods=['POST'])
@login_required
@role_required('yonetici')
def kpi_ekle():
    try:
        hedef = KpiHedef(
            modul=request.form['modul'],
            kpi_adi=request.form['kpi_adi'],
            kpi_kodu=request.form['kpi_kodu'],
            birim=request.form.get('birim', '%'),
            hedef_deger=float(request.form['hedef_deger']),
            alt_limit=float(request.form['alt_limit']) if request.form.get('alt_limit') else None,
            ust_limit=float(request.form['ust_limit']) if request.form.get('ust_limit') else None,
            yonu=request.form.get('yonu', 'yukari'),
            periyot=request.form.get('periyot', 'aylik'),
            yil=int(request.form.get('yil', datetime.now(timezone.utc).year)),
            ay=int(request.form['ay']) if request.form.get('ay') else None,
            olusturan_id=current_user.id
        )
        db.session.add(hedef)
        db.session.commit()
        flash('KPI hedefi başarıyla eklendi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'KPI eklenirken hata oluştu: {str(e)}', 'danger')
    return redirect(url_for('analitik.index') + '#kpi')


@analitik_bp.route('/kpi/<int:id>/duzenle', methods=['POST'])
@login_required
@role_required('yonetici')
def kpi_duzenle(id):
    hedef = KpiHedef.query.get_or_404(id)
    try:
        hedef.kpi_adi = request.form.get('kpi_adi', hedef.kpi_adi)
        hedef.hedef_deger = float(request.form.get('hedef_deger', hedef.hedef_deger))
        hedef.alt_limit = float(request.form['alt_limit']) if request.form.get('alt_limit') else None
        hedef.ust_limit = float(request.form['ust_limit']) if request.form.get('ust_limit') else None
        hedef.yonu = request.form.get('yonu', hedef.yonu)
        db.session.commit()
        flash('KPI hedefi güncellendi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Güncelleme hatası: {str(e)}', 'danger')
    return redirect(url_for('analitik.index') + '#kpi')


@analitik_bp.route('/kpi/<int:id>/sil', methods=['POST'])
@login_required
@role_required('yonetici')
def kpi_sil(id):
    hedef = KpiHedef.query.get_or_404(id)
    db.session.delete(hedef)
    db.session.commit()
    flash('KPI hedefi silindi.', 'info')
    return redirect(url_for('analitik.index') + '#kpi')


@analitik_bp.route('/kpi/varsayilan-yukle', methods=['POST'])
@login_required
@role_required('yonetici')
def kpi_varsayilan_yukle():
    """Varsayılan KPI hedeflerini veritabanına yükler."""
    yil = datetime.now(timezone.utc).year
    varsayilan_hedefler = {
        'makine': {'ort_oee': 85, 'ariza_sayisi': 5, 'bakim_maliyeti': 50000},
        'kalite': {'hata_orani': 2.0, 'fire_orani': 1.5},
        'enerji': {'toplam_maliyet': 100000, 'birim_tuketim': 1.0},
        'isg': {'kaza_sayisi': 0, 'kayip_gun': 0},
        'stok': {'kritik_malzeme': 3},
        'personel': {'devamsizlik': 5}
    }
    eklenen = 0
    for kpi_def in KpiHedef.VARSAYILAN_KPILER:
        mevcut = KpiHedef.query.filter_by(modul=kpi_def['modul'], kpi_kodu=kpi_def['kpi_kodu'], yil=yil).first()
        if not mevcut:
            hedef_deger = varsayilan_hedefler.get(kpi_def['modul'], {}).get(kpi_def['kpi_kodu'], 0)
            hedef = KpiHedef(
                modul=kpi_def['modul'], kpi_adi=kpi_def['kpi_adi'], kpi_kodu=kpi_def['kpi_kodu'],
                birim=kpi_def['birim'], hedef_deger=hedef_deger, yonu=kpi_def['yonu'],
                periyot='aylik', yil=yil, olusturan_id=current_user.id
            )
            db.session.add(hedef)
            eklenen += 1
    db.session.commit()
    flash(f'{eklenen} varsayılan KPI hedefi yüklendi.', 'success')
    return redirect(url_for('analitik.index') + '#kpi')


# ══════════════════════════════════════
#  Maliyet Merkezi API'leri
# ══════════════════════════════════════

@analitik_bp.route('/api/maliyet/tco/<int:makine_id>')
@login_required
@role_required('yonetici')
def api_tco(makine_id):
    from app.services.analitik.maliyet_servisi import maliyet_servisi
    sonuc = maliyet_servisi.makine_tco(makine_id)
    if not sonuc:
        return jsonify({'error': 'Makine bulunamadı'}), 404
    return jsonify(sonuc)


@analitik_bp.route('/api/maliyet/birim-maliyet')
@login_required
@role_required('yonetici')
def api_birim_maliyet():
    from app.services.analitik.maliyet_servisi import maliyet_servisi
    gun = request.args.get('gun', 30, type=int)
    return jsonify(maliyet_servisi.tum_makineler_birim_maliyet(gun))


@analitik_bp.route('/api/maliyet/roi/<int:makine_id>')
@login_required
@role_required('yonetici')
def api_roi(makine_id):
    from app.services.analitik.maliyet_servisi import maliyet_servisi
    yontem = request.args.get('amortisman', 'dogrusal')
    sonuc = maliyet_servisi.makine_roi(makine_id, amortisman_yontemi=yontem)
    if not sonuc:
        return jsonify({'error': 'Makine veya satın alma verisi bulunamadı'}), 404
    return jsonify(sonuc)


@analitik_bp.route('/api/maliyet/tco-karsilastirma')
@login_required
@role_required('yonetici')
def api_tco_karsilastirma():
    """Tüm makinelerin TCO karşılaştırmalı tablosu."""
    from app.services.analitik.maliyet_servisi import maliyet_servisi
    return jsonify(maliyet_servisi.tum_makineler_tco_karsilastirma())


# ══════════════════════════════════════
#  Fabrika Sağlık Skoru & Yıllık KPI
# ══════════════════════════════════════

@analitik_bp.route('/api/kpi/saglik-skoru')
@login_required
@role_required('yonetici')
def api_saglik_skoru():
    """Fabrika geneli tek sağlık skoru (0-100)."""
    from app.services.analitik.kpi_servisi import kpi_servisi
    yil = request.args.get('yil', datetime.now(timezone.utc).year, type=int)
    ay = request.args.get('ay', datetime.now(timezone.utc).month, type=int)
    return jsonify(kpi_servisi.fabrika_saglik_skoru(yil, ay))


@analitik_bp.route('/api/kpi/yillik-seri')
@login_required
@role_required('yonetici')
def api_yillik_kpi_serisi():
    """12 aylık hedef vs gerçekleşen serisi."""
    from app.services.analitik.kpi_servisi import kpi_servisi
    modul = request.args.get('modul', 'makine')
    kpi_kodu = request.args.get('kpi_kodu', 'ort_oee')
    yil = request.args.get('yil', datetime.now(timezone.utc).year, type=int)
    return jsonify(kpi_servisi.yillik_kpi_serisi(modul, kpi_kodu, yil))


# ══════════════════════════════════════
#  İş Emri Analitik API'leri
# ══════════════════════════════════════

@analitik_bp.route('/api/is-emri/teknisyen-performans')
@login_required
@role_required('yonetici')
def api_teknisyen_performans():
    """Teknisyen bazlı performans raporu."""
    from app.services.is_emri_servisi import is_emri_servisi
    gun = request.args.get('gun', 30, type=int)
    return jsonify(is_emri_servisi.teknisyen_performans_raporu(gun))


@analitik_bp.route('/api/is-emri/kategori-istatistik')
@login_required
@role_required('yonetici')
def api_kategori_istatistik():
    """Kategori bazlı iş emri dağılımı."""
    from app.services.is_emri_servisi import is_emri_servisi
    return jsonify(is_emri_servisi.kategori_istatistik())


@analitik_bp.route('/api/is-emri/haftalik-trend')
@login_required
@role_required('yonetici')
def api_haftalik_trend():
    """Haftalık oluşturulan vs kapanan trend."""
    from app.services.is_emri_servisi import is_emri_servisi
    hafta = request.args.get('hafta', 8, type=int)
    return jsonify(is_emri_servisi.haftalik_trend(hafta))


# ══════════════════════════════════════
#  Otomasyon Kural Yönetimi API'leri
# ══════════════════════════════════════

@analitik_bp.route('/api/otomasyon/kurallar')
@login_required
@role_required('yonetici')
def api_otomasyon_kurallar():
    """Otomasyon kurallarının durumlarını ve istatistiklerini döner."""
    from app.services.otomasyon_motoru import otomasyon_motoru
    return jsonify(otomasyon_motoru.kural_istatistikleri_al())


@analitik_bp.route('/api/otomasyon/kural-toggle', methods=['POST'])
@login_required
@role_required('yonetici')
def api_otomasyon_kural_toggle():
    """Otomasyon kuralını aktif/pasif yapar."""
    from app.services.otomasyon_motoru import otomasyon_motoru
    data = request.get_json()
    if not data or 'kural' not in data or 'aktif' not in data:
        return jsonify({'error': 'Geçersiz veri'}), 400
    basarili = otomasyon_motoru.kural_toggle(data['kural'], data['aktif'])
    if basarili:
        return jsonify({'success': True})
    return jsonify({'error': 'Geçersiz kural adı'}), 400

