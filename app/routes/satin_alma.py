"""
FDYS — Satın Alma Modülü Rotaları
Faz 7

Satın alma talepleri, siparişler, teklifler ve raporlama endpoint'leri.
"""

import logging
from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, jsonify, current_app
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, yazma_izni_gerekli, log_action
from app.models.satin_alma import SatinAlmaTalebi, SatinAlmaSiparis, TeklifKarsilastirma
from app.models.stok import Tedarikci
from app.forms.satin_alma import (
    SatinAlmaTalebiForm, SatinAlmaSiparisForm, TeklifKarsilastirmaForm,
    TalepRedForm, TeslimAlmaForm
)
from app.services.satin_alma_servisi import (
    talep_olustur, talep_onayla, talep_reddet, talep_iptal,
    siparis_olustur, siparis_teslim_al, siparis_kargoda,
    teklif_ekle, teklif_sec, teklif_sil,
    satin_alma_istatistikler, aylik_harcama_ozeti, tedarikci_performans_ozeti
)

logger = logging.getLogger(__name__)

satin_alma_bp = Blueprint('satin_alma', __name__, url_prefix='/satin-alma')


# ══════════════════════════════════════════════════════════════════
# DASHBOARD VE LİSTELER
# ══════════════════════════════════════════════════════════════════

@satin_alma_bp.route('/')
@login_required
@modul_erisim_gerekli('satin_alma')
def index():
    """Satın alma dashboard ve özet görünümü."""
    istatistikler = satin_alma_istatistikler()
    aylik_harcama = aylik_harcama_ozeti()
    
    # Son talepler
    son_talepler = SatinAlmaTalebi.query.filter_by(aktif=True).order_by(
        SatinAlmaTalebi.id.desc()
    ).limit(5).all()

    # Son siparişler
    son_siparisler = SatinAlmaSiparis.query.filter_by(aktif=True).order_by(
        SatinAlmaSiparis.id.desc()
    ).limit(5).all()

    # Eğer sadece okuma izni varsa (onaycı/izleyici ise)
    # kendi departmanı veya tümü gibi filtreler eklenebilir,
    # şimdilik herkes hepsini görüyor.
    return render_template('satin_alma/index.html',
                           istatistikler=istatistikler,
                           aylik_harcama=aylik_harcama,
                           son_talepler=son_talepler,
                           son_siparisler=son_siparisler)


@satin_alma_bp.route('/talepler')
@login_required
@modul_erisim_gerekli('satin_alma')
def talepler():
    """Tüm taleplerin listelendiği sayfa."""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum', '')
    arama = request.args.get('q', '')

    query = SatinAlmaTalebi.query.filter_by(aktif=True)

    if durum:
        query = query.filter_by(durum=durum)

    if arama:
        query = query.filter(or_(
            SatinAlmaTalebi.talep_no.ilike(f'%{arama}%'),
            SatinAlmaTalebi.kalem_adi.ilike(f'%{arama}%')
        ))

    talepler_paginated = query.order_by(SatinAlmaTalebi.id.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('satin_alma/talepler.html',
                           talepler=talepler_paginated,
                           durum=durum, arama=arama)


@satin_alma_bp.route('/siparisler')
@login_required
@modul_erisim_gerekli('satin_alma')
def siparisler():
    """Sipariş listesi."""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum', '')
    arama = request.args.get('q', '')

    query = SatinAlmaSiparis.query.filter_by(aktif=True)

    if durum:
        query = query.filter_by(durum=durum)

    if arama:
        query = query.filter(or_(
            SatinAlmaSiparis.siparis_no.ilike(f'%{arama}%'),
            SatinAlmaSiparis.fatura_no.ilike(f'%{arama}%')
        ))

    siparisler_paginated = query.order_by(SatinAlmaSiparis.id.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('satin_alma/siparisler.html',
                           siparisler=siparisler_paginated,
                           durum=durum, arama=arama)


# ══════════════════════════════════════════════════════════════════
# TALEP İŞLEMLERİ (CRUD)
# ══════════════════════════════════════════════════════════════════

@satin_alma_bp.route('/talep/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Satın Alma Talebi Oluşturma')
def talep_ekle():
    """Yeni satın alma talebi oluşturma."""
    form = SatinAlmaTalebiForm()
    
    # Tedarikçi listesini doldur
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    form.tedarikci_id.choices = [(0, '--- Seçiniz ---')] + [(t.id, t.ad) for t in tedarikciler]

    if form.validate_on_submit():
        kwargs = form.data.copy()
        if kwargs.get('tedarikci_id') == 0:
            kwargs['tedarikci_id'] = None
            
        talep = talep_olustur(current_user, **kwargs)
        flash(f'Talep oluşturuldu: {talep.talep_no}', 'success')
        return redirect(url_for('satin_alma.talep_detay', id=talep.id))

    return render_template('satin_alma/talep_form.html', form=form, title='Yeni Satın Alma Talebi')


@satin_alma_bp.route('/talep/<int:id>')
@login_required
@modul_erisim_gerekli('satin_alma')
def talep_detay(id):
    """Talep detay sayfası — teklifler ve siparişler buradan görülür."""
    talep = SatinAlmaTalebi.query.get_or_404(id)
    
    # Formları hazırla (modallar için)
    teklif_form = TeklifKarsilastirmaForm()
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    teklif_form.tedarikci_id.choices = [(t.id, t.ad) for t in tedarikciler]
    
    red_form = TalepRedForm()
    
    siparis_form = SatinAlmaSiparisForm()
    siparis_form.tedarikci_id.choices = [(t.id, t.ad) for t in tedarikciler]
    siparis_form.talep_id.data = talep.id
    siparis_form.miktar.data = talep.miktar
    # Seçili teklif varsa sipariş formunu doldur
    if talep.secilen_teklif:
        siparis_form.tedarikci_id.data = talep.secilen_teklif.tedarikci_id
        siparis_form.birim_fiyat.data = talep.secilen_teklif.birim_fiyat

    return render_template('satin_alma/talep_detay.html',
                           talep=talep,
                           teklif_form=teklif_form,
                           red_form=red_form,
                           siparis_form=siparis_form)


@satin_alma_bp.route('/talep/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Satın Alma Talebi Düzenleme')
def talep_duzenle(id):
    """Sadece bekleyen talepler düzenlenebilir."""
    talep = SatinAlmaTalebi.query.get_or_404(id)
    
    if not talep.onay_bekliyor_mu:
        flash('Sadece onay bekleyen talepler düzenlenebilir.', 'danger')
        return redirect(url_for('satin_alma.talep_detay', id=talep.id))
        
    form = SatinAlmaTalebiForm(obj=talep)
    
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    form.tedarikci_id.choices = [(0, '--- Seçiniz ---')] + [(t.id, t.ad) for t in tedarikciler]
    
    if request.method == 'GET' and not talep.tedarikci_id:
        form.tedarikci_id.data = 0

    if form.validate_on_submit():
        talep.malzeme_hizmet = form.malzeme_hizmet.data
        talep.kalem_adi = form.kalem_adi.data
        talep.miktar = form.miktar.data
        talep.birim = form.birim.data
        talep.tahmini_birim_fiyat = form.tahmini_birim_fiyat.data
        talep.departman = form.departman.data
        talep.aciliyet = form.aciliyet.data
        talep.aciklama = form.aciklama.data
        talep.gerekce = form.gerekce.data
        talep.istenen_teslim_tarihi = form.istenen_teslim_tarihi.data
        
        if form.tedarikci_id.data == 0:
            talep.tedarikci_id = None
        else:
            talep.tedarikci_id = form.tedarikci_id.data
            
        db.session.commit()
        flash('Talep güncellendi.', 'success')
        return redirect(url_for('satin_alma.talep_detay', id=talep.id))

    return render_template('satin_alma/talep_form.html', form=form, talep=talep, title='Talep Düzenle')


# ══════════════════════════════════════════════════════════════════
# ONAY VE İPTAL AKIŞI
# ══════════════════════════════════════════════════════════════════

@satin_alma_bp.route('/talep/<int:id>/onayla', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')  # İdealde 'onaylama' yetkisi olmalı
@log_action('Satın Alma Talebi Onaylama')
def onayla(id):
    """Yöneticiler talebi onaylayabilir."""
    _, err = talep_onayla(id, current_user)
    if err:
        flash(err, 'danger')
    else:
        flash('Talep başarıyla onaylandı.', 'success')
    return redirect(url_for('satin_alma.talep_detay', id=id))


@satin_alma_bp.route('/talep/<int:id>/reddet', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Satın Alma Talebi Reddetme')
def reddet(id):
    form = TalepRedForm()
    if form.validate_on_submit():
        _, err = talep_reddet(id, current_user, form.red_nedeni.data)
        if err:
            flash(err, 'danger')
        else:
            flash('Talep reddedildi.', 'warning')
    return redirect(url_for('satin_alma.talep_detay', id=id))


@satin_alma_bp.route('/talep/<int:id>/iptal', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Satın Alma Talebi İptal')
def iptal(id):
    _, err = talep_iptal(id)
    if err:
        flash(err, 'danger')
    else:
        flash('Talep iptal edildi.', 'info')
    return redirect(url_for('satin_alma.talep_detay', id=id))


# ══════════════════════════════════════════════════════════════════
# TEKLİF İŞLEMLERİ
# ══════════════════════════════════════════════════════════════════

@satin_alma_bp.route('/talep/<int:id>/teklif-ekle', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Teklif Ekleme')
def teklif_ekle_route(id):
    form = TeklifKarsilastirmaForm()
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    form.tedarikci_id.choices = [(t.id, t.ad) for t in tedarikciler]
    
    if form.validate_on_submit():
        _, err = teklif_ekle(id, **form.data)
        if err:
            flash(err, 'danger')
        else:
            flash('Teklif başarıyla eklendi.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
                
    return redirect(url_for('satin_alma.talep_detay', id=id))


@satin_alma_bp.route('/teklif/<int:teklif_id>/sec', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Teklif Seçme')
def teklif_sec_route(teklif_id):
    teklif, err = teklif_sec(teklif_id)
    if err:
        flash(err, 'danger')
        return redirect(url_for('satin_alma.talepler'))
    flash('Teklif seçildi ve tedarikçi belirlendi.', 'success')
    return redirect(url_for('satin_alma.talep_detay', id=teklif.talep_id))


@satin_alma_bp.route('/teklif/<int:teklif_id>/sil', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Teklif Silme')
def teklif_sil_route(teklif_id):
    teklif = TeklifKarsilastirma.query.get_or_404(teklif_id)
    talep_id = teklif.talep_id
    _, err = teklif_sil(teklif_id)
    if err:
        flash(err, 'danger')
    else:
        flash('Teklif silindi.', 'success')
    return redirect(url_for('satin_alma.talep_detay', id=talep_id))


# ══════════════════════════════════════════════════════════════════
# SİPARİŞ İŞLEMLERİ
# ══════════════════════════════════════════════════════════════════

@satin_alma_bp.route('/siparis/olustur', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Sipariş Oluşturma')
def siparis_olustur_route():
    form = SatinAlmaSiparisForm()
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    form.tedarikci_id.choices = [(t.id, t.ad) for t in tedarikciler]
    
    if form.validate_on_submit():
        siparis, err = siparis_olustur(form.talep_id.data, current_user, **form.data)
        if err:
            flash(err, 'danger')
            return redirect(url_for('satin_alma.talep_detay', id=form.talep_id.data))
            
        flash(f'Sipariş başarıyla oluşturuldu: {siparis.siparis_no}', 'success')
        return redirect(url_for('satin_alma.siparis_detay', id=siparis.id))
        
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'danger')
            
    return redirect(request.referrer or url_for('satin_alma.talepler'))


@satin_alma_bp.route('/siparis/<int:id>')
@login_required
@modul_erisim_gerekli('satin_alma')
def siparis_detay(id):
    siparis = SatinAlmaSiparis.query.get_or_404(id)
    teslim_form = TeslimAlmaForm()
    
    return render_template('satin_alma/siparis_detay.html',
                           siparis=siparis,
                           teslim_form=teslim_form)


@satin_alma_bp.route('/siparis/<int:id>/kargo', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Sipariş Kargoya Verildi')
def kargoda_route(id):
    _, err = siparis_kargoda(id)
    if err:
        flash(err, 'danger')
    else:
        flash('Sipariş durumu kargoda olarak güncellendi.', 'info')
    return redirect(url_for('satin_alma.siparis_detay', id=id))


@satin_alma_bp.route('/siparis/<int:id>/teslim-al', methods=['POST'])
@login_required
@yazma_izni_gerekli('satin_alma')
@log_action('Sipariş Teslim Alma')
def teslim_al_route(id):
    form = TeslimAlmaForm()
    if form.validate_on_submit():
        _, err = siparis_teslim_al(id, current_user,
                                   gercek_teslim=form.gercek_teslim.data,
                                   fatura_no=form.fatura_no.data,
                                   notlar=form.notlar.data)
        if err:
            flash(err, 'danger')
        else:
            flash('Sipariş başarıyla teslim alındı.', 'success')
    return redirect(url_for('satin_alma.siparis_detay', id=id))


# ══════════════════════════════════════════════════════════════════
# RAPORLAR
# ══════════════════════════════════════════════════════════════════

@satin_alma_bp.route('/tedarikci-performans')
@login_required
@modul_erisim_gerekli('satin_alma')
def tedarikci_performans():
    ozet = tedarikci_performans_ozeti()
    return render_template('satin_alma/rapor_tedarikci.html', ozet=ozet)
