"""
FDYS — Sözleşme Route Modülü
Faz 3 — Sözleşme, Kira Kontrat & Sigorta Poliçe
"""

import os
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_file
from flask_login import login_required, current_user
import json

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, log_action
from app.models.sozlesme import Sozlesme, KiraKontrat, SigortaPolice, StandartMetin
from app.forms.sozlesme import SozlesmeForm, KiraKontratForm, SigortaPoliceForm, StandartMetinForm
from app.services import sozlesme_servisi

sozlesme_bp = Blueprint('sozlesme', __name__, url_prefix='/sozlesme')


@sozlesme_bp.route('/')
@login_required
@modul_erisim_gerekli('sozlesme')
def index():
    """Sözleşme Ana Dashboard."""
    stats = sozlesme_servisi.sozlesme_dashboard_istatistik()
    return render_template('sozlesme/index.html', stats=stats)


# ==========================================
# ANA SÖZLEŞME İŞLEMLERİ
# ==========================================

@sozlesme_bp.route('/liste')
@login_required
@modul_erisim_gerekli('sozlesme')
def sozlesme_listesi():
    """Genel Sözleşmeler Listesi."""
    page = request.args.get('page', 1, type=int)
    arama = request.args.get('q', '').strip()
    tur = request.args.get('tur', '')
    durum = request.args.get('durum', '')
    
    sorgu = Sozlesme.query.filter_by(aktif=True)
    
    if arama:
        terim = f"%{arama}%"
        sorgu = sorgu.filter(
            db.or_(
                Sozlesme.sozlesme_no.ilike(terim),
                Sozlesme.baslik.ilike(terim)
            )
        )
        
    if tur:
        sorgu = sorgu.filter(Sozlesme.tur == tur)
        
    if durum:
        sorgu = sorgu.filter(Sozlesme.durum == durum)
        
    sozlesmeler = sorgu.order_by(Sozlesme.olusturma_tarihi.desc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('sozlesme/kira_listesi.html', 
                           sozlesmeler=sozlesmeler,
                           arama=arama, tur=tur, durum=durum,
                           sayfa_baslik='Genel Sözleşmeler',
                           is_kira=False)


@sozlesme_bp.route('/kira-listesi')
@login_required
@modul_erisim_gerekli('sozlesme')
def kira_listesi():
    """Sadece Kira Sözleşmeleri Listesi."""
    page = request.args.get('page', 1, type=int)
    arama = request.args.get('q', '').strip()
    durum = request.args.get('durum', '')
    
    sorgu = Sozlesme.query.filter_by(aktif=True, tur='kira')
    
    if arama:
        terim = f"%{arama}%"
        sorgu = sorgu.filter(
            db.or_(
                Sozlesme.sozlesme_no.ilike(terim),
                Sozlesme.baslik.ilike(terim)
            )
        )
        
    if durum:
        sorgu = sorgu.filter(Sozlesme.durum == durum)
        
    sozlesmeler = sorgu.order_by(Sozlesme.olusturma_tarihi.desc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('sozlesme/kira_listesi.html', 
                           sozlesmeler=sozlesmeler,
                           arama=arama, tur='kira', durum=durum,
                           sayfa_baslik='Kira Sözleşmeleri',
                           is_kira=True)


@sozlesme_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Sözleşme Ekleme')
def sozlesme_ekle():
    """Yeni sözleşme (ve opsiyonel kira kontratı) ekler."""
    tur = request.args.get('tur', 'kira')
    form = SozlesmeForm()
    kira_form = KiraKontratForm()
    
    # Form seçimleri (Choices)
    form.standart_metin_id.choices = sozlesme_servisi.standart_metin_secenekleri()
    form.taraf_id.choices = sozlesme_servisi.taraf_secenekleri(form.taraf_tip.data or 'ortak')
    
    if request.method == 'GET':
        form.sozlesme_no.data = sozlesme_servisi.sonraki_sozlesme_no()
        form.tur.data = tur
    
    if form.validate_on_submit():
        if form.bitis_tarihi.data and form.baslangic_tarihi.data and form.bitis_tarihi.data < form.baslangic_tarihi.data:
            flash("Bitiş tarihi, başlangıç tarihinden önce olamaz.", "danger")
            return render_template('sozlesme/sozlesme_form.html', form=form, kira_form=kira_form, is_edit=False)

        if Sozlesme.query.filter_by(sozlesme_no=form.sozlesme_no.data).first():
            flash(f"'{form.sozlesme_no.data}' numaralı sözleşme zaten var.", 'danger')
            return render_template('sozlesme/sozlesme_form.html', form=form, kira_form=kira_form, is_edit=False)
            
        sozlesme = Sozlesme()
        form.populate_obj(sozlesme)
        
        if form.standart_metin_id.data == 0:
            sozlesme.standart_metin_id = None
            
        db.session.add(sozlesme)
        db.session.flush() # id almak için
        
        # Eğer tür kira ise kira kontratını da ekle
        if form.tur.data == 'kira':
            # Kira formu validasyonu
            kira_kontrat = KiraKontrat(sozlesme_id=sozlesme.id)
            kira_form.populate_obj(kira_kontrat)
            db.session.add(kira_kontrat)
            
        db.session.commit()
        flash('Sözleşme başarıyla eklendi.', 'success')
        return redirect(url_for('sozlesme.sozlesme_detay', id=sozlesme.id))
        
    # Ajax değişikliklerinde taraf_id seçeneklerini yenilemek için eğer validate false ise
    if request.method == 'POST':
        taraf_tip_raw = request.form.get('taraf_tip')
        if taraf_tip_raw:
            form.taraf_id.choices = sozlesme_servisi.taraf_secenekleri(taraf_tip_raw)
            
    return render_template('sozlesme/sozlesme_form.html', form=form, kira_form=kira_form, is_edit=False)


@sozlesme_bp.route('/<int:id>')
@login_required
@modul_erisim_gerekli('sozlesme')
def sozlesme_detay(id):
    """Sözleşme detay kartı."""
    rapor = sozlesme_servisi.sozlesme_detay_rapor(id)
    if not rapor:
        flash('Sözleşme bulunamadı.', 'danger')
        return redirect(url_for('sozlesme.sozlesme_listesi'))
        
    return render_template('sozlesme/sozlesme_detay.html', 
                           sozlesme=rapor['sozlesme'],
                           taraf=rapor['taraf'],
                           kira=rapor['kira'],
                           police=rapor['police'])


@sozlesme_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Sözleşme Düzenleme')
def sozlesme_duzenle(id):
    """Sözleşme (ve varsa kira kontratı) düzenleme."""
    sozlesme = db.session.get(Sozlesme, id)
    if not sozlesme:
        flash('Sözleşme bulunamadı.', 'danger')
        return redirect(url_for('sozlesme.sozlesme_listesi'))
        
    form = SozlesmeForm(obj=sozlesme)
    kira_form = KiraKontratForm(obj=sozlesme.kira_kontrat) if sozlesme.kira_kontrat else KiraKontratForm()
    
    # Options
    form.standart_metin_id.choices = sozlesme_servisi.standart_metin_secenekleri()
    form.taraf_id.choices = sozlesme_servisi.taraf_secenekleri(form.taraf_tip.data or sozlesme.taraf_tip)
    
    # Standart metin ID 0 ayarı
    if request.method == 'GET' and not sozlesme.standart_metin_id:
        form.standart_metin_id.data = 0
        
    if request.method == 'POST':
        taraf_tip_raw = request.form.get('taraf_tip')
        if taraf_tip_raw:
            form.taraf_id.choices = sozlesme_servisi.taraf_secenekleri(taraf_tip_raw)

    if form.validate_on_submit():
        if form.bitis_tarihi.data and form.baslangic_tarihi.data and form.bitis_tarihi.data < form.baslangic_tarihi.data:
            flash("Bitiş tarihi, başlangıç tarihinden önce olamaz.", "danger")
            return render_template('sozlesme/sozlesme_form.html', form=form, kira_form=kira_form, is_edit=True, sozlesme=sozlesme)

        mevcut = Sozlesme.query.filter(Sozlesme.sozlesme_no == form.sozlesme_no.data, Sozlesme.id != id).first()
        if mevcut:
            flash(f"'{form.sozlesme_no.data}' numaralı sözleşme zaten var.", 'danger')
            return render_template('sozlesme/sozlesme_form.html', form=form, kira_form=kira_form, is_edit=True, sozlesme=sozlesme)
            
        eski_durum = sozlesme.durum
        form.populate_obj(sozlesme)
        
        if form.standart_metin_id.data == 0:
            sozlesme.standart_metin_id = None
            
        if sozlesme.tur == 'kira':
            if not sozlesme.kira_kontrat:
                kira_kontrat = KiraKontrat(sozlesme_id=sozlesme.id)
                db.session.add(kira_kontrat)
                sozlesme.kira_kontrat = kira_kontrat
            kira_form.populate_obj(sozlesme.kira_kontrat)
        else:
            if sozlesme.kira_kontrat:
                db.session.delete(sozlesme.kira_kontrat)
                sozlesme.kira_kontrat = None

        if eski_durum != sozlesme.durum and sozlesme.durum in ['iptal', 'sona_erdi']:
            if sozlesme.sigorta_police and sozlesme.sigorta_police.durum == 'aktif':
                sozlesme.sigorta_police.durum = 'iptal' if sozlesme.durum == 'iptal' else 'suresi_doldu'
                sozlesme.sigorta_police.notlar = (sozlesme.sigorta_police.notlar or "") + f"\nAna sözleşme {sozlesme.durum} olduğu için poliçe durumu otomatik güncellendi."
            
        db.session.commit()
        flash('Sözleşme başarıyla güncellendi.', 'success')
        return redirect(url_for('sozlesme.sozlesme_detay', id=sozlesme.id))
        
    return render_template('sozlesme/sozlesme_form.html', form=form, kira_form=kira_form, is_edit=True, sozlesme=sozlesme)


@sozlesme_bp.route('/<int:id>/sil', methods=['POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Sözleşme Silme')
def sozlesme_sil(id):
    sozlesme = db.session.get(Sozlesme, id)
    if sozlesme:
        sozlesme.aktif = False
        db.session.commit()
        flash('Sözleşme silindi.', 'success')
    return redirect(url_for('sozlesme.sozlesme_listesi'))


# ==========================================
# SİGORTA POLİÇESİ İŞLEMLERİ
# ==========================================

@sozlesme_bp.route('/policeler')
@login_required
@modul_erisim_gerekli('sozlesme')
def police_listesi():
    """Sigorta Poliçeleri Listesi."""
    page = request.args.get('page', 1, type=int)
    arama = request.args.get('q', '').strip()
    tur = request.args.get('tur', '')
    durum = request.args.get('durum', '')
    
    sorgu = SigortaPolice.query.filter_by(aktif=True)
    
    if arama:
        terim = f"%{arama}%"
        sorgu = sorgu.filter(
            db.or_(
                SigortaPolice.police_no.ilike(terim),
                SigortaPolice.sigorta_sirketi.ilike(terim)
            )
        )
        
    if tur:
        sorgu = sorgu.filter(SigortaPolice.sigorta_turu == tur)
        
    if durum:
        sorgu = sorgu.filter(SigortaPolice.durum == durum)
        
    policeler = sorgu.order_by(SigortaPolice.police_bitis.asc()).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('sozlesme/police_listesi.html', 
                           policeler=policeler,
                           arama=arama, tur=tur, durum=durum)


@sozlesme_bp.route('/police/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Poliçe Ekleme')
def police_ekle():
    """Yeni poliçe ekler."""
    form = SigortaPoliceForm()
    
    # Bağlı sözleşme seçenekleri
    sozlesmeler = Sozlesme.query.filter_by(aktif=True).order_by(Sozlesme.sozlesme_no).all()
    form.sozlesme_id.choices = [(0, '— Bağlı Sözleşme Yok —')] + [(s.id, f"{s.sozlesme_no} — {s.baslik[:30]}") for s in sozlesmeler]
    
    if request.method == 'GET':
        form.police_no.data = sozlesme_servisi.sonraki_police_no()
        
    if form.validate_on_submit():
        if SigortaPolice.query.filter_by(police_no=form.police_no.data).first():
            flash(f"'{form.police_no.data}' numaralı poliçe zaten var.", 'danger')
            return render_template('sozlesme/police_form.html', form=form, is_edit=False)
            
        police = SigortaPolice()
        form.populate_obj(police)
        
        if form.sozlesme_id.data == 0:
            police.sozlesme_id = None
            
        db.session.add(police)
        db.session.commit()
        flash('Poliçe başarıyla eklendi.', 'success')
        return redirect(url_for('sozlesme.police_listesi'))
        
    return render_template('sozlesme/police_form.html', form=form, is_edit=False)


@sozlesme_bp.route('/police/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Poliçe Düzenleme')
def police_duzenle(id):
    """Poliçe düzenler."""
    police = db.session.get(SigortaPolice, id)
    if not police:
        flash('Poliçe bulunamadı.', 'danger')
        return redirect(url_for('sozlesme.police_listesi'))
        
    form = SigortaPoliceForm(obj=police)
    
    sozlesmeler = Sozlesme.query.filter_by(aktif=True).order_by(Sozlesme.sozlesme_no).all()
    form.sozlesme_id.choices = [(0, '— Bağlı Sözleşme Yok —')] + [(s.id, f"{s.sozlesme_no} — {s.baslik[:30]}") for s in sozlesmeler]
    
    if request.method == 'GET' and not police.sozlesme_id:
        form.sozlesme_id.data = 0
        
    if form.validate_on_submit():
        mevcut = SigortaPolice.query.filter(SigortaPolice.police_no == form.police_no.data, SigortaPolice.id != id).first()
        if mevcut:
            flash(f"'{form.police_no.data}' numaralı poliçe zaten var.", 'danger')
            return render_template('sozlesme/police_form.html', form=form, is_edit=True, police=police)
            
        form.populate_obj(police)
        
        if form.sozlesme_id.data == 0:
            police.sozlesme_id = None
            
        db.session.commit()
        flash('Poliçe güncellendi.', 'success')
        return redirect(url_for('sozlesme.police_listesi'))
        
    return render_template('sozlesme/police_form.html', form=form, is_edit=True, police=police)


@sozlesme_bp.route('/police/<int:id>/sil', methods=['POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Poliçe Silme')
def police_sil(id):
    police = db.session.get(SigortaPolice, id)
    if police:
        police.aktif = False
        db.session.commit()
        flash('Poliçe silindi.', 'success')
    return redirect(url_for('sozlesme.police_listesi'))


# ==========================================
# HATIRLATMALAR & TAKVİM
# ==========================================

@sozlesme_bp.route('/hatirlatmalar')
@login_required
@modul_erisim_gerekli('sozlesme')
def hatirlatmalar():
    """Süresi yaklaşan sözleşme ve poliçeleri gösterir."""
    veri = sozlesme_servisi.hatirlatma_kontrol()
    return render_template('sozlesme/hatirlatmalar.html', 
                           sozlesmeler=veri['sozlesmeler'],
                           policeler=veri['policeler'])


@sozlesme_bp.route('/api/takvim-olaylari')
@login_required
@modul_erisim_gerekli('sozlesme')
def api_takvim_olaylari():
    """Takvim için JSON formatında olayları döndürür."""
    olaylar = sozlesme_servisi.yaklasan_olaylar_takvim()
    return jsonify(olaylar)


# ==========================================
# STANDART METİNLER (ŞABLONLAR)
# ==========================================

@sozlesme_bp.route('/sablonlar')
@login_required
@modul_erisim_gerekli('sozlesme')
def sablonlar():
    """Standart metin şablonlarını listeler."""
    metinler = StandartMetin.query.filter_by(aktif=True).all()
    return render_template('sozlesme/standart_metinler.html', metinler=metinler)


@sozlesme_bp.route('/sablon/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Sözleşme Şablonu Ekleme')
def sablon_ekle():
    form = StandartMetinForm()
    if form.validate_on_submit():
        metin = StandartMetin()
        form.populate_obj(metin)
        db.session.add(metin)
        db.session.commit()
        flash('Şablon eklendi.', 'success')
        return redirect(url_for('sozlesme.sablonlar'))
    return render_template('sozlesme/sablon_form.html', form=form, is_edit=False)


@sozlesme_bp.route('/sablon/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Sözleşme Şablonu Düzenleme')
def sablon_duzenle(id):
    metin = db.session.get(StandartMetin, id)
    if not metin:
        flash('Şablon bulunamadı.', 'danger')
        return redirect(url_for('sozlesme.sablonlar'))
        
    form = StandartMetinForm(obj=metin)
    if form.validate_on_submit():
        form.populate_obj(metin)
        db.session.commit()
        flash('Şablon güncellendi.', 'success')
        return redirect(url_for('sozlesme.sablonlar'))
    return render_template('sozlesme/sablon_form.html', form=form, is_edit=True, metin=metin)


@sozlesme_bp.route('/sablon/<int:id>/sil', methods=['POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
@log_action('Sözleşme Şablonu Silme')
def sablon_sil(id):
    metin = db.session.get(StandartMetin, id)
    if metin:
        metin.aktif = False
        db.session.commit()
        flash('Şablon silindi.', 'success')
    return redirect(url_for('sozlesme.sablonlar'))


# ==========================================
# AJAX & API ENDPOINTLERİ
# ==========================================

@sozlesme_bp.route('/api/taraf-getir/<tip>')
@login_required
def api_taraf_getir(tip):
    """Taraf tipine göre seçenekleri döndürür."""
    secenekler = sozlesme_servisi.taraf_secenekleri(tip)
    return jsonify([{'id': s[0], 'text': s[1]} for s in secenekler])


@sozlesme_bp.route('/api/kira-artis-hesapla/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('sozlesme', 'yazma')
def api_kira_artis_hesapla(id):
    """Kira artışı hesaplar veya uygular."""
    try:
        data = request.get_json()
        orani = data.get('oran')
        uygula = data.get('uygula', False)
        
        if uygula:
            sonuc = sozlesme_servisi.kira_artisi_uygula(id, orani)
            if sonuc:
                return jsonify({'success': True, 'data': sonuc})
        else:
            sonuc = sozlesme_servisi.kira_artisi_hesapla(id, orani)
            if sonuc:
                return jsonify({'success': True, 'data': sonuc})
                
        return jsonify({'success': False, 'message': 'Hesaplama yapılamadı.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@sozlesme_bp.route('/api/sablon-onizleme/<int:id>')
@login_required
@modul_erisim_gerekli('sozlesme')
def api_sablon_onizleme(id):
    """Sözleşmeye ait standart metni doldurulmuş şekilde döndürür."""
    icerik = sozlesme_servisi.sozlesme_sablon_onizleme(id)
    if icerik is None:
        return jsonify({'success': False, 'message': 'Şablon veya sözleşme bulunamadı.'})
    return jsonify({'success': True, 'icerik': icerik})


@sozlesme_bp.route('/raporlar')
@login_required
@modul_erisim_gerekli('sozlesme')
def raporlar():
    """Sözleşme genel raporlama."""
    tur = request.args.get('tur', '')
    durum = request.args.get('durum', '')
    taraf_tip = request.args.get('taraf_tip', '')
    
    filtre = {}
    if tur: filtre['tur'] = tur
    if durum: filtre['durum'] = durum
    if taraf_tip: filtre['taraf_tip'] = taraf_tip
    
    rapor_verisi = sozlesme_servisi.sozlesme_rapor(filtre)
    
    return render_template('sozlesme/raporlar.html', 
                           rapor=rapor_verisi,
                           secili_tur=tur,
                           secili_durum=durum,
                           secili_taraf=taraf_tip)


@sozlesme_bp.route('/export')
@login_required
@modul_erisim_gerekli('sozlesme')
@log_action('Sözleşmeler Excel Export')
def export_excel():
    """Sözleşmeleri Excel'e aktarır."""
    tur = request.args.get('tur', '')
    filtre = {'tur': tur} if tur else None
    
    excel_data = sozlesme_servisi.sozlesme_excel_export(filtre)
    if not excel_data:
        flash('Excel oluşturulamadı.', 'danger')
        return redirect(url_for('sozlesme.sozlesme_listesi'))
        
    from io import BytesIO
    tarih = datetime.now().strftime("%Y%m%d")
    isim = f"sozlesmeler_{tur if tur else 'tumu'}_{tarih}.xlsx"
    
    return send_file(
        BytesIO(excel_data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=isim
    )
