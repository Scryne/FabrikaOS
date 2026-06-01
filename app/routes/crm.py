"""
FDYS — CRM Route Modülü
Faz 2 — Ortak & Firma Yönetimi
"""

import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, log_action
from app.models.crm import Ortak, Firma, FirmaYetkilisi, CrmIletisimGecmisi
from app.forms.crm import OrtakForm, FirmaForm, FirmaYetkilisiForm, IletisimForm
from app.services import crm_servisi

crm_bp = Blueprint('crm', __name__, url_prefix='/crm')


# --- GÜVENLİ DOSYA YÜKLEME YARDIMCISI ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_obj, subfolder='crm'):
    if not file_obj or not file_obj.filename:
        return None
    
    if allowed_file(file_obj.filename):
        filename = secure_filename(file_obj.filename)
        # Benzersiz isim oluştur
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Yükleme klasörünü hazırla
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), subfolder)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        file_obj.save(file_path)
        
        # Sadece veritabanında tutulacak göreceli yolu dön
        return f"{subfolder}/{unique_filename}"
    return None


@crm_bp.route('/')
@login_required
@modul_erisim_gerekli('crm')
def index():
    """CRM Dashboard."""
    stats = crm_servisi.crm_dashboard_istatistik()
    
    # İletişim ekleme formu (modal için)
    iletisim_form = IletisimForm()
    
    return render_template('crm/index.html', stats=stats, form=iletisim_form)


# ==========================================
# ORTAK (SANAYİ SİTESİ ORTAĞI) İŞLEMLERİ
# ==========================================

@crm_bp.route('/ortaklar')
@login_required
@modul_erisim_gerekli('crm')
def ortaklar():
    """Ortaklar listesi ve arama."""
    page = request.args.get('page', 1, type=int)
    arama = request.args.get('q', '').strip()
    durum = request.args.get('durum', '')
    tip = request.args.get('tip', '')
    
    sorgu = Ortak.query.filter_by(aktif=True)
    
    if arama:
        terim = f"%{arama}%"
        sorgu = sorgu.filter(
            db.or_(
                Ortak.ad_soyad.ilike(terim),
                Ortak.ortak_no.ilike(terim),
                Ortak.tc_kimlik.ilike(terim),
                Ortak.telefon.ilike(terim),
                Ortak.blok.ilike(terim),
                Ortak.daire_no.ilike(terim)
            )
        )
        
    if durum:
        sorgu = sorgu.filter(Ortak.durum == durum)
        
    if tip:
        sorgu = sorgu.filter(Ortak.ortak_tipi == tip)
        
    ortaklar = sorgu.order_by(Ortak.ortak_no).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('crm/ortaklar.html', 
                           ortaklar=ortaklar, 
                           arama=arama, 
                           durum=durum, 
                           tip=tip)


@crm_bp.route('/ortaklar/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Ortak Ekleme')
def ortak_ekle():
    """Yeni ortak ekleme formu."""
    form = OrtakForm()
    
    # Varsayılan değerler
    if request.method == 'GET':
        form.ortak_no.data = crm_servisi.sonraki_ortak_no()
    
    if form.validate_on_submit():
        # TC Kimlik veya Ortak No kontrolü
        if Ortak.query.filter_by(ortak_no=form.ortak_no.data).first():
            flash(f"'{form.ortak_no.data}' numaralı ortak zaten mevcut.", 'danger')
            return render_template('crm/ortak_form.html', form=form, is_edit=False)
            
        if form.tc_kimlik.data and Ortak.query.filter_by(tc_kimlik=form.tc_kimlik.data).first():
            flash(f"'{form.tc_kimlik.data}' TC numaralı ortak zaten mevcut.", 'danger')
            return render_template('crm/ortak_form.html', form=form, is_edit=False)
            
        ortak = Ortak()
        form.populate_obj(ortak)
        
        # Profil fotoğrafı yükleme
        if 'fotograf' in request.files:
            file = request.files['fotograf']
            file_path = save_uploaded_file(file, 'crm/avatars')
            if file_path:
                ortak.fotograf = file_path
                
        db.session.add(ortak)
        db.session.commit()
        
        flash('Ortak başarıyla eklendi.', 'success')
        return redirect(url_for('crm.ortak_detay', id=ortak.id))
        
    return render_template('crm/ortak_form.html', form=form, is_edit=False)


@crm_bp.route('/ortaklar/<int:id>')
@login_required
@modul_erisim_gerekli('crm')
def ortak_detay(id):
    """Ortak detay kartı."""
    detay = crm_servisi.ortak_detay_rapor(id)
    if not detay:
        flash('Ortak bulunamadı.', 'danger')
        return redirect(url_for('crm.ortaklar'))
        
    iletisim_form = IletisimForm()
    iletisim_form.ilgili_tip.data = 'ortak'
    iletisim_form.ilgili_id.data = id
        
    return render_template('crm/ortak_detay.html', 
                           ortak=detay['ortak'], 
                           iletisimler=detay['iletisimler'],
                           iletisim_sayisi=detay['iletisim_sayisi'],
                           iletisim_form=iletisim_form)


@crm_bp.route('/ortaklar/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Ortak Düzenleme')
def ortak_duzenle(id):
    """Ortak düzenleme formu."""
    ortak = db.session.get(Ortak, id)
    if not ortak:
        flash('Ortak bulunamadı.', 'danger')
        return redirect(url_for('crm.ortaklar'))
        
    form = OrtakForm(obj=ortak)
    
    if form.validate_on_submit():
        # TC veya Ortak No çakışma kontrolü
        mevcut_no = Ortak.query.filter(Ortak.ortak_no == form.ortak_no.data, Ortak.id != id).first()
        if mevcut_no:
            flash(f"'{form.ortak_no.data}' numaralı ortak zaten mevcut.", 'danger')
            return render_template('crm/ortak_form.html', form=form, is_edit=True, ortak=ortak)
            
        if form.tc_kimlik.data:
            mevcut_tc = Ortak.query.filter(Ortak.tc_kimlik == form.tc_kimlik.data, Ortak.id != id).first()
            if mevcut_tc:
                flash(f"'{form.tc_kimlik.data}' TC numaralı ortak zaten mevcut.", 'danger')
                return render_template('crm/ortak_form.html', form=form, is_edit=True, ortak=ortak)
                
        form.populate_obj(ortak)
        
        # Profil fotoğrafı güncelleme
        if 'fotograf' in request.files:
            file = request.files['fotograf']
            if file and file.filename:
                file_path = save_uploaded_file(file, 'crm/avatars')
                if file_path:
                    ortak.fotograf = file_path
                    
        db.session.commit()
        flash('Ortak başarıyla güncellendi.', 'success')
        return redirect(url_for('crm.ortak_detay', id=ortak.id))
        
    return render_template('crm/ortak_form.html', form=form, is_edit=True, ortak=ortak)


@crm_bp.route('/ortaklar/<int:id>/sil', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Ortak Silme')
def ortak_sil(id):
    """Ortak silme (soft delete)."""
    ortak = db.session.get(Ortak, id)
    if ortak:
        ortak.aktif = False
        db.session.commit()
        flash('Ortak kaydı silindi.', 'success')
    return redirect(url_for('crm.ortaklar'))


# ==========================================
# FİRMA (İŞLETME) İŞLEMLERİ
# ==========================================

@crm_bp.route('/firmalar')
@login_required
@modul_erisim_gerekli('crm')
def firmalar():
    """Firmalar listesi ve arama."""
    page = request.args.get('page', 1, type=int)
    arama = request.args.get('q', '').strip()
    durum = request.args.get('durum', '')
    sektor = request.args.get('sektor', '')
    
    sorgu = Firma.query.filter_by(aktif=True)
    
    if arama:
        terim = f"%{arama}%"
        sorgu = sorgu.filter(
            db.or_(
                Firma.unvan.ilike(terim),
                Firma.firma_no.ilike(terim),
                Firma.vergi_no.ilike(terim),
                Firma.yetkili_kisi.ilike(terim),
                Firma.blok.ilike(terim),
                Firma.daire_no.ilike(terim)
            )
        )
        
    if durum:
        sorgu = sorgu.filter(Firma.durum == durum)
        
    if sektor:
        sorgu = sorgu.filter(Firma.sektor == sektor)
        
    firma_listesi = sorgu.order_by(Firma.firma_no).paginate(page=page, per_page=15, error_out=False)
    
    # Sektör seçeneklerini al (filtre menüsü için)
    sektorler = Firma.SEKTORLER
    
    return render_template('crm/firmalar.html', 
                           firmalar=firma_listesi, 
                           arama=arama, 
                           durum=durum, 
                           sektor=sektor,
                           sektorler=sektorler)


@crm_bp.route('/firmalar/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Firma Ekleme')
def firma_ekle():
    """Yeni firma ekleme formu."""
    form = FirmaForm()
    
    if request.method == 'GET':
        form.firma_no.data = crm_servisi.sonraki_firma_no()
    
    if form.validate_on_submit():
        if Firma.query.filter_by(firma_no=form.firma_no.data).first():
            flash(f"'{form.firma_no.data}' numaralı firma zaten mevcut.", 'danger')
            return render_template('crm/firma_form.html', form=form, is_edit=False)
            
        if form.vergi_no.data and Firma.query.filter_by(vergi_no=form.vergi_no.data).first():
            flash(f"'{form.vergi_no.data}' vergi numaralı firma zaten mevcut.", 'danger')
            return render_template('crm/firma_form.html', form=form, is_edit=False)
            
        firma = Firma()
        form.populate_obj(firma)
        
        # Logo yükleme
        if 'logo' in request.files:
            file = request.files['logo']
            file_path = save_uploaded_file(file, 'crm/logos')
            if file_path:
                firma.logo = file_path
                
        db.session.add(firma)
        db.session.commit()
        
        flash('Firma başarıyla eklendi.', 'success')
        return redirect(url_for('crm.firma_detay', id=firma.id))
        
    return render_template('crm/firma_form.html', form=form, is_edit=False)


@crm_bp.route('/firmalar/<int:id>')
@login_required
@modul_erisim_gerekli('crm')
def firma_detay(id):
    """Firma detay kartı."""
    detay = crm_servisi.firma_detay_rapor(id)
    if not detay:
        flash('Firma bulunamadı.', 'danger')
        return redirect(url_for('crm.firmalar'))
        
    yetkili_form = FirmaYetkilisiForm()
    yetkili_form.firma_id.data = id
    
    iletisim_form = IletisimForm()
    iletisim_form.ilgili_tip.data = 'firma'
    iletisim_form.ilgili_id.data = id
        
    return render_template('crm/firma_detay.html', 
                           firma=detay['firma'], 
                           yetkililer=detay['yetkililer'],
                           iletisimler=detay['iletisimler'],
                           iletisim_sayisi=detay['iletisim_sayisi'],
                           yetkili_form=yetkili_form,
                           iletisim_form=iletisim_form)


@crm_bp.route('/firmalar/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Firma Düzenleme')
def firma_duzenle(id):
    """Firma düzenleme formu."""
    firma = db.session.get(Firma, id)
    if not firma:
        flash('Firma bulunamadı.', 'danger')
        return redirect(url_for('crm.firmalar'))
        
    form = FirmaForm(obj=firma)
    
    if form.validate_on_submit():
        mevcut_no = Firma.query.filter(Firma.firma_no == form.firma_no.data, Firma.id != id).first()
        if mevcut_no:
            flash(f"'{form.firma_no.data}' numaralı firma zaten mevcut.", 'danger')
            return render_template('crm/firma_form.html', form=form, is_edit=True, firma=firma)
            
        if form.vergi_no.data:
            mevcut_vn = Firma.query.filter(Firma.vergi_no == form.vergi_no.data, Firma.id != id).first()
            if mevcut_vn:
                flash(f"'{form.vergi_no.data}' vergi numaralı firma zaten mevcut.", 'danger')
                return render_template('crm/firma_form.html', form=form, is_edit=True, firma=firma)
                
        form.populate_obj(firma)
        
        # Logo güncelleme
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                file_path = save_uploaded_file(file, 'crm/logos')
                if file_path:
                    firma.logo = file_path
                    
        db.session.commit()
        flash('Firma başarıyla güncellendi.', 'success')
        return redirect(url_for('crm.firma_detay', id=firma.id))
        
    return render_template('crm/firma_form.html', form=form, is_edit=True, firma=firma)


@crm_bp.route('/firmalar/<int:id>/sil', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Firma Silme')
def firma_sil(id):
    """Firma silme (soft delete)."""
    firma = db.session.get(Firma, id)
    if firma:
        firma.aktif = False
        db.session.commit()
        flash('Firma kaydı silindi.', 'success')
    return redirect(url_for('crm.firmalar'))


# ==========================================
# YETKİLİ & İLETİŞİM İŞLEMLERİ
# ==========================================

@crm_bp.route('/yetkili-ekle', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Firma Yetkilisi Ekleme')
def yetkili_ekle():
    """Firmaya yeni yetkili ekler."""
    form = FirmaYetkilisiForm()
    
    if form.validate_on_submit():
        firma = db.session.get(Firma, form.firma_id.data)
        if not firma:
            flash('Firma bulunamadı.', 'danger')
            return redirect(url_for('crm.firmalar'))
            
        yetkili = FirmaYetkilisi(
            firma_id=firma.id,
            ad_soyad=form.ad_soyad.data,
            gorev=form.gorev.data,
            telefon=form.telefon.data,
            eposta=form.eposta.data,
            tc_kimlik=form.tc_kimlik.data
        )
        
        db.session.add(yetkili)
        db.session.commit()
        flash('Yetkili başarıyla eklendi.', 'success')
        return redirect(url_for('crm.firma_detay', id=firma.id))
        
    flash('Form verilerinde hata var. Lütfen kontrol edin.', 'danger')
    # Hata durumunda geldiği sayfaya geri dön (genelde firma_detay)
    return redirect(request.referrer or url_for('crm.firmalar'))


@crm_bp.route('/yetkili-sil/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('Firma Yetkilisi Silme')
def yetkili_sil(id):
    """Firma yetkilisini siler (soft delete)."""
    yetkili = db.session.get(FirmaYetkilisi, id)
    if yetkili:
        firma_id = yetkili.firma_id
        yetkili.aktif = False
        db.session.commit()
        flash('Yetkili silindi.', 'success')
        return redirect(url_for('crm.firma_detay', id=firma_id))
    
    flash('Yetkili bulunamadı.', 'danger')
    return redirect(request.referrer or url_for('crm.firmalar'))


@crm_bp.route('/iletisim-ekle', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('İletişim Kaydı Ekleme')
def iletisim_ekle():
    """Yeni iletişim geçmişi kaydı ekler."""
    form = IletisimForm()
    
    if form.validate_on_submit():
        iletisim = CrmIletisimGecmisi(
            ilgili_tip=form.ilgili_tip.data,
            ilgili_id=form.ilgili_id.data,
            iletisim_turu=form.iletisim_turu.data,
            konu=form.konu.data,
            detay=form.detay.data,
            sonuc=form.sonuc.data,
            yapan_id=current_user.id
        )
        db.session.add(iletisim)
        db.session.commit()
        flash('İletişim kaydı başarıyla eklendi.', 'success')
        
        if form.ilgili_tip.data == 'ortak':
            return redirect(url_for('crm.ortak_detay', id=form.ilgili_id.data))
        else:
            return redirect(url_for('crm.firma_detay', id=form.ilgili_id.data))
            
    flash('İletişim kaydı eklenemedi, verileri kontrol edin.', 'danger')
    return redirect(request.referrer or url_for('crm.index'))


# ==========================================
# HARİTA & EXCEL İŞLEMLERİ
# ==========================================

@crm_bp.route('/harita')
@login_required
@modul_erisim_gerekli('crm')
def harita():
    """Ortak ve firmaların harita üzerindeki görünümü."""
    return render_template('crm/harita.html')


@crm_bp.route('/api/harita-verileri')
@login_required
@modul_erisim_gerekli('crm')
def api_harita_verileri():
    """Harita modülü için JSON verisi sağlar."""
    veriler = crm_servisi.harita_verileri()
    return jsonify(veriler)


@crm_bp.route('/export/ortaklar')
@login_required
@modul_erisim_gerekli('crm')
@log_action('Ortak Listesi Excel Export')
def export_ortaklar():
    """Ortakları Excel olarak indir."""
    excel_data = crm_servisi.excel_export_ortaklar()
    
    if not excel_data:
        flash('Excel dışa aktarımı sırasında bir hata oluştu veya kütüphane eksik.', 'danger')
        return redirect(url_for('crm.ortaklar'))
        
    from io import BytesIO
    from flask import send_file
    
    tarih = datetime.now().strftime("%Y%m%d")
    return send_file(
        BytesIO(excel_data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'ortaklar_listesi_{tarih}.xlsx'
    )


@crm_bp.route('/export/firmalar')
@login_required
@modul_erisim_gerekli('crm')
@log_action('Firma Listesi Excel Export')
def export_firmalar():
    """Firmaları Excel olarak indir."""
    excel_data = crm_servisi.excel_export_firmalar()
    
    if not excel_data:
        flash('Excel dışa aktarımı sırasında bir hata oluştu veya kütüphane eksik.', 'danger')
        return redirect(url_for('crm.firmalar'))
        
    from io import BytesIO
    from flask import send_file
    
    tarih = datetime.now().strftime("%Y%m%d")
    return send_file(
        BytesIO(excel_data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'firmalar_listesi_{tarih}.xlsx'
    )


@crm_bp.route('/import', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('CRM Toplu Veri Aktarımı')
def import_excel():
    """Excel'den toplu ortak/firma içe aktarma."""
    if request.method == 'POST':
        if 'dosya' not in request.files:
            flash('Lütfen bir dosya seçin.', 'warning')
            return redirect(request.url)
            
        file = request.files['dosya']
        if file.filename == '':
            flash('Dosya seçilmedi.', 'warning')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            # Dosyayı geçici olarak kaydet
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, secure_filename(file.filename))
            file.save(temp_path)
            
            # Verileri içeri aktar
            import_tipi = request.form.get('import_tipi', 'ortak')
            
            if import_tipi == 'ortak':
                sonuc = crm_servisi.excel_import_ortaklar(temp_path)
            else:
                sonuc = crm_servisi.excel_import_firmalar(temp_path)
                
            # Geçici dosyayı sil
            try:
                os.remove(temp_path)
            except:
                pass
                
            if sonuc['basarili'] > 0:
                flash(f"{sonuc['basarili']} kayıt başarıyla içe aktarıldı.", 'success')
                
            if sonuc['hatali'] > 0:
                hata_msg = f"{sonuc['hatali']} kayıtta hata oluştu. Detaylar: "
                hata_msg += ", ".join(sonuc['hatalar'][:5])
                if len(sonuc['hatalar']) > 5:
                    hata_msg += "..."
                flash(hata_msg, 'danger')
                
            return redirect(url_for('crm.import_excel'))
            
        flash('Geçersiz dosya formatı. Lütfen .xlsx uzantılı dosya yükleyin.', 'danger')
        
    return render_template('crm/import.html')


@crm_bp.route('/arsiv')
@login_required
@modul_erisim_gerekli('crm')
def arsiv():
    """
    Belge Arşivi & OCR Arama (Arayüz).
    OCR servisi kullanılarak taranan belgeler aranabilir.
    """
    # Basit bir placeholder sayfa olacak, gelişmiş arşiv daha sonraki faza eklenebilir.
    from app.models.dosya import DosyaEki
    # DosyaEki kullanarak CRM ile ilişkili dosyaları çekebiliriz
    dosyalar = DosyaEki.query.filter(
        db.or_(
            DosyaEki.kaynak_tablo == 'ortak',
            DosyaEki.kaynak_tablo == 'firma'
        ),
        DosyaEki.aktif == True
    ).order_by(DosyaEki.olusturma_tarihi.desc()).all()
    
    return render_template('crm/arsiv.html', dosyalar=dosyalar)

@crm_bp.route('/arama')
@login_required
@modul_erisim_gerekli('crm')
def arama():
    """Genel CRM arama motoru."""
    q = request.args.get('q', '').strip()
    tip = request.args.get('tip', None)
    
    if not q:
        return render_template('crm/arama_sonuclari.html', sonuclar=None, q=q)
        
    sonuclar = crm_servisi.crm_arama(q, tip=tip)
    return render_template('crm/arama_sonuclari.html', sonuclar=sonuclar, q=q, tip=tip)

@crm_bp.route('/api/hizli-ekle', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
def api_hizli_ekle():
    """Hızlı firma/ortak ekleme (AJAX)."""
    data = request.get_json()
    if not data or not data.get('tip') or not data.get('isim'):
        return jsonify({'success': False, 'message': 'Eksik bilgi.'})
        
    isim = data.get('isim').strip()
    tip = data.get('tip')
    
    try:
        if tip == 'ortak':
            from app.models.crm import Ortak
            ortak = Ortak(ad_soyad=isim, ortak_no=crm_servisi.sonraki_ortak_no(), aktif=True)
            db.session.add(ortak)
            db.session.commit()
            return jsonify({'success': True, 'id': ortak.id, 'text': f"{ortak.ortak_no} - {ortak.ad_soyad}"})
        elif tip == 'firma':
            from app.models.crm import Firma
            firma = Firma(unvan=isim, firma_no=crm_servisi.sonraki_firma_no(), aktif=True)
            db.session.add(firma)
            db.session.commit()
            return jsonify({'success': True, 'id': firma.id, 'text': f"{firma.firma_no} - {firma.unvan}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
        
    return jsonify({'success': False, 'message': 'Geçersiz tip.'})

@crm_bp.route('/arsiv/yukle', methods=['POST'])
@login_required
@modul_erisim_gerekli('crm', 'yazma')
@log_action('CRM Arşiv Dosyası Yükleme')
def arsiv_yukle():
    """Arşive dosya yükler ve OCR taraması yapar."""
    if 'dosya' not in request.files:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('crm.arsiv'))
        
    file = request.files['dosya']
    if file.filename == '':
        flash('Geçersiz dosya.', 'warning')
        return redirect(url_for('crm.arsiv'))
        
    kaynak_tablo = request.form.get('kaynak_tablo', 'ortak')
    kaynak_id = request.form.get('kaynak_id', type=int)
    aciklama = request.form.get('aciklama', '').strip()
    
    if not kaynak_id:
        flash('Hedef kayıt seçilmedi.', 'warning')
        return redirect(url_for('crm.arsiv'))

    if file and allowed_file(file.filename):
        from app.models.dosya import DosyaEki
        from werkzeug.utils import secure_filename
        import os
        from flask import current_app
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'crm_arsiv')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        dosya_tipi = DosyaEki.dosya_tipi_bul(filename)
        
        # Dosya eki kaydı oluştur
        dosya = DosyaEki(
            dosya_adi=f"crm_arsiv/{unique_filename}",
            orijinal_adi=filename,
            dosya_tipi=dosya_tipi,
            kaynak_tablo=kaynak_tablo,
            kaynak_id=kaynak_id,
            yukleyen_id=current_user.id,
            aciklama=aciklama,
            dosya_boyutu=os.path.getsize(file_path)
        )
        
        # OCR İşlemi (Eğer resim veya pdf ise - pdf için ocr servisindeki desteğe bağlı)
        if dosya_tipi == 'image':
            from app.services.ocr_servisi import extract_text_from_image, clean_ocr_text
            ocr_text = extract_text_from_image(file_path)
            if ocr_text:
                # OCR metnini aciklamaya veya notlara ekleyelim
                temiz_text = clean_ocr_text(ocr_text)
                dosya.aciklama = (dosya.aciklama or "") + f" [OCR Metni: {temiz_text[:500]}]"
                
        db.session.add(dosya)
        db.session.commit()
        flash('Dosya başarıyla yüklendi.', 'success')
        
    return redirect(url_for('crm.arsiv'))
