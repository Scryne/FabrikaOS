"""FDYS — Enerji Takip Modülü Rotaları (Faz 4 — Kurumsal)"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.enerji import EnerjiTuketimi
from app.models.makine import Makine
from app.forms.kalite_isg_enerji import EnerjiTuketimForm
from app.utils.decorators import modul_erisim_gerekli, log_action
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

enerji_bp = Blueprint('enerji', __name__, url_prefix='/enerji')


@enerji_bp.route('/')
@login_required
@modul_erisim_gerekli('enerji')
def index():
    """Enerji tüketim paneli — maliyet özetleri, tür dağılımı, trend grafikleri."""
    sayfa = request.args.get('sayfa', 1, type=int)
    tuketimler = EnerjiTuketimi.query.order_by(EnerjiTuketimi.donem_baslangic.desc())\
        .paginate(page=sayfa, per_page=20, error_out=False)

    # Toplam Maliyet ve Karbon Salınımı
    toplam_maliyet = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet)).scalar() or 0
    toplam_karbon = db.session.query(func.sum(EnerjiTuketimi.karbon_salinimi)).scalar() or 0

    # Tür bazlı tüketim toplamları
    tur_toplamlari = db.session.query(
        EnerjiTuketimi.enerji_turu,
        func.sum(EnerjiTuketimi.miktar),
        func.sum(EnerjiTuketimi.toplam_maliyet),
        func.sum(EnerjiTuketimi.karbon_salinimi)
    ).group_by(EnerjiTuketimi.enerji_turu).all()

    tur_ozet = {}
    for tur, miktar, maliyet, karbon in tur_toplamlari:
        tur_ozet[tur] = {
            'miktar': float(miktar) if miktar else 0,
            'maliyet': float(maliyet) if maliyet else 0,
            'karbon': float(karbon) if karbon else 0
        }

    # Aylık tüketim trendi (son 6 ay)
    alti_ay_once = datetime.now(timezone.utc).date() - timedelta(days=180)
    aylik_trend = db.session.query(
        func.strftime('%Y-%m', EnerjiTuketimi.donem_baslangic),
        EnerjiTuketimi.enerji_turu,
        func.sum(EnerjiTuketimi.miktar)
    ).filter(EnerjiTuketimi.donem_baslangic >= alti_ay_once)\
     .group_by(func.strftime('%Y-%m', EnerjiTuketimi.donem_baslangic), EnerjiTuketimi.enerji_turu)\
     .order_by(func.strftime('%Y-%m', EnerjiTuketimi.donem_baslangic)).all()

    # Trend verisini yapılandır
    trend_aylari = sorted(set(d[0] for d in aylik_trend))
    trend_data = {
        'elektrik': [], 'dogalgaz': [], 'su': [], 'buhar': [], 'basincli_hava': []
    }

    for ay in trend_aylari:
        for tur in trend_data.keys():
            val = next((float(d[2]) for d in aylik_trend if d[0] == ay and d[1] == tur), 0)
            trend_data[tur].append(val)

    maliyet_labels = list(tur_ozet.keys())
    maliyet_values = [tur_ozet[k]['maliyet'] for k in maliyet_labels]
    
    toplam_kayit = EnerjiTuketimi.query.count()

    return render_template('enerji/index.html',
                           tuketimler=tuketimler,
                           toplam_maliyet=round(float(toplam_maliyet), 2),
                           toplam_karbon=round(float(toplam_karbon), 2),
                           tur_ozet=tur_ozet,
                           trend_chart={
                               'labels': trend_aylari,
                               'elektrik': trend_data['elektrik'],
                               'dogalgaz': trend_data['dogalgaz'],
                               'su': trend_data['su']
                           },
                           maliyet_chart={'labels': maliyet_labels, 'values': maliyet_values},
                           toplam_kayit=toplam_kayit)


@enerji_bp.route('/kaydet', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('enerji')
@log_action('Enerji Tüketim Kaydı')
def kaydet():
    form = EnerjiTuketimForm()
    form.makine_id.choices = [(0, '--- Genel / Fabrika ---')] + \
                             [(m.id, m.ad) for m in Makine.query.filter_by(aktif=True).all()]

    if form.validate_on_submit():
        birimler = {'elektrik': 'kWh', 'dogalgaz': 'm³', 'su': 'm³', 'buhar': 'Ton', 'basincli_hava': 'm³'}
        enerji_turu = form.enerji_turu.data

        tuketim = EnerjiTuketimi(
            makine_id=form.makine_id.data if form.makine_id.data != 0 else None,
            departman=form.departman.data,
            enerji_turu=enerji_turu,
            miktar=form.miktar.data,
            birim=birimler.get(enerji_turu, 'Birim'),
            birim_fiyat=form.birim_fiyat.data or 0,
            donem_baslangic=form.donem_baslangic.data,
            donem_bitis=form.donem_bitis.data,
            hedef_miktar=form.hedef_miktar.data,
            fatura_no=form.fatura_no.data,
            notlar=form.notlar.data,
            kaydeden_id=current_user.id
        )
        
        # Maliyet ve karbon otomatik hesapla
        tuketim.hesapla_maliyet_ve_karbon()

        db.session.add(tuketim)
        db.session.commit()

        # Hedef aşımı kontrolü
        if tuketim.hedef_sapma_yuzde and tuketim.hedef_sapma_yuzde > 10:
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici
            yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik="Enerji Hedef Aşımı!",
                    mesaj=f"{enerji_turu.capitalize()} tüketimi hedefi %{tuketim.hedef_sapma_yuzde} aştı.",
                    seviye="uyari",
                    modul="enerji",
                    url=url_for('enerji.index')
                )

        flash('Enerji tüketim verisi başarıyla kaydedildi.', 'success')
        return redirect(url_for('enerji.index'))

    return render_template('enerji/form.html', form=form)
