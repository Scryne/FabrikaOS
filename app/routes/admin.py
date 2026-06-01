"""FDYS — Admin (Sistem Ayarları) Rotaları"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.kullanici import Kullanici, DenetimIzi
from app.forms.admin import KullaniciEkleForm, KullaniciDuzenleForm
from app.utils.decorators import role_required, log_action

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@role_required('yonetici')
def index():
    """Admin paneli ana sayfası (Kullanıcı Listesi)."""
    page = request.args.get('page', 1, type=int)
    kullanicilar_pagination = Kullanici.query.order_by(Kullanici.id.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/index.html',
                           kullanicilar=kullanicilar_pagination.items,
                           pagination=kullanicilar_pagination)


@admin_bp.route('/kullanici/ekle', methods=['GET', 'POST'])
@login_required
@role_required('yonetici')
@log_action('Yeni Kullanıcı Ekleme')
def kullanici_ekle():
    form = KullaniciEkleForm()
    if form.validate_on_submit():
        modul_erisim = {
            'personel': {'okuma': form.modul_personel.data, 'yazma': form.modul_personel.data, 'silme': form.modul_personel.data},
            'makine': {'okuma': form.modul_makine.data, 'yazma': form.modul_makine.data, 'silme': form.modul_makine.data},
            'stok': {'okuma': form.modul_stok.data, 'yazma': form.modul_stok.data, 'silme': form.modul_stok.data},
            'kalite': {'okuma': form.modul_kalite.data, 'yazma': form.modul_kalite.data, 'silme': form.modul_kalite.data},
            'enerji': {'okuma': form.modul_enerji.data, 'yazma': form.modul_enerji.data, 'silme': form.modul_enerji.data},
            'isg': {'okuma': form.modul_isg.data, 'yazma': form.modul_isg.data, 'silme': form.modul_isg.data},
            'ik': {'okuma': form.modul_ik.data, 'yazma': form.modul_ik.data, 'silme': form.modul_ik.data},
            'crm': {'okuma': form.modul_crm.data, 'yazma': form.modul_crm.data, 'silme': form.modul_crm.data},
            'sozlesme': {'okuma': form.modul_sozlesme.data, 'yazma': form.modul_sozlesme.data, 'silme': form.modul_sozlesme.data},
            'talep': {'okuma': form.modul_talep.data, 'yazma': form.modul_talep.data, 'silme': form.modul_talep.data},
            'satin_alma': {'okuma': form.modul_satin_alma.data, 'yazma': form.modul_satin_alma.data, 'silme': form.modul_satin_alma.data},
            'dys': {'okuma': form.modul_dys.data, 'yazma': form.modul_dys.data, 'silme': form.modul_dys.data},
            'duyuru': {'okuma': form.modul_duyuru.data, 'yazma': form.modul_duyuru.data, 'silme': form.modul_duyuru.data}
        }
        
        kullanici = Kullanici(
            ad_soyad=form.ad_soyad.data,
            kullanici_adi=form.kullanici_adi.data,
            rol=form.rol.data,
            departman=form.departman.data,
            modul_erisim=modul_erisim,
            aktif=form.aktif.data
        )
        kullanici.sifre_belirle(form.sifre.data)
        
        db.session.add(kullanici)
        db.session.commit()
        flash(f'Kullanıcı {kullanici.kullanici_adi} başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.index'))
        
    return render_template('admin/form.html', form=form, title='Yeni Kullanıcı Ekle')


@admin_bp.route('/kullanici/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('yonetici')
@log_action('Kullanıcı Düzenleme')
def kullanici_duzenle(id):
    kullanici = Kullanici.query.get_or_404(id)
    form = KullaniciDuzenleForm(obj=kullanici)
    
    if request.method == 'GET':
        # Modül erişimlerini forma doldur
        form.departman.data = kullanici.departman
        form.modul_personel.data = kullanici.modul_erisim_var_mi('personel')
        form.modul_makine.data = kullanici.modul_erisim_var_mi('makine')
        form.modul_stok.data = kullanici.modul_erisim_var_mi('stok')
        form.modul_kalite.data = kullanici.modul_erisim_var_mi('kalite')
        form.modul_enerji.data = kullanici.modul_erisim_var_mi('enerji')
        form.modul_isg.data = kullanici.modul_erisim_var_mi('isg')
        form.modul_ik.data = kullanici.modul_erisim_var_mi('ik')
        form.modul_crm.data = kullanici.modul_erisim_var_mi('crm')
        form.modul_sozlesme.data = kullanici.modul_erisim_var_mi('sozlesme')
        form.modul_talep.data = kullanici.modul_erisim_var_mi('talep')
        form.modul_satin_alma.data = kullanici.modul_erisim_var_mi('satin_alma')
        form.modul_dys.data = kullanici.modul_erisim_var_mi('dys')
        form.modul_duyuru.data = kullanici.modul_erisim_var_mi('duyuru')
        
    if form.validate_on_submit():
        # Kullanıcı adı çakışma kontrolü
        if kullanici.kullanici_adi != form.kullanici_adi.data:
            if Kullanici.query.filter_by(kullanici_adi=form.kullanici_adi.data).first():
                flash('Bu kullanıcı adı zaten alınmış.', 'danger')
                return render_template('admin/form.html', form=form, title='Kullanıcı Düzenle')
                
        kullanici.ad_soyad = form.ad_soyad.data
        kullanici.kullanici_adi = form.kullanici_adi.data
        kullanici.rol = form.rol.data
        kullanici.departman = form.departman.data
        kullanici.aktif = form.aktif.data
        
        # Hesap kilitliyse ve işareti kaldırılmışsa sıfırla
        if kullanici.hesap_kilitli and not form.hesap_kilitli.data:
            kullanici.basarisiz_giris = 0
            kullanici.kilit_zamani = None
        kullanici.hesap_kilitli = form.hesap_kilitli.data
        
        # Şifre değiştirilmişse
        if form.sifre.data:
            kullanici.sifre_belirle(form.sifre.data)
            
        # Modül erişimlerini güncelle
        modul_erisim = {
            'personel': {'okuma': form.modul_personel.data, 'yazma': form.modul_personel.data, 'silme': form.modul_personel.data},
            'makine': {'okuma': form.modul_makine.data, 'yazma': form.modul_makine.data, 'silme': form.modul_makine.data},
            'stok': {'okuma': form.modul_stok.data, 'yazma': form.modul_stok.data, 'silme': form.modul_stok.data},
            'kalite': {'okuma': form.modul_kalite.data, 'yazma': form.modul_kalite.data, 'silme': form.modul_kalite.data},
            'enerji': {'okuma': form.modul_enerji.data, 'yazma': form.modul_enerji.data, 'silme': form.modul_enerji.data},
            'isg': {'okuma': form.modul_isg.data, 'yazma': form.modul_isg.data, 'silme': form.modul_isg.data},
            'ik': {'okuma': form.modul_ik.data, 'yazma': form.modul_ik.data, 'silme': form.modul_ik.data},
            'crm': {'okuma': form.modul_crm.data, 'yazma': form.modul_crm.data, 'silme': form.modul_crm.data},
            'sozlesme': {'okuma': form.modul_sozlesme.data, 'yazma': form.modul_sozlesme.data, 'silme': form.modul_sozlesme.data},
            'talep': {'okuma': form.modul_talep.data, 'yazma': form.modul_talep.data, 'silme': form.modul_talep.data},
            'satin_alma': {'okuma': form.modul_satin_alma.data, 'yazma': form.modul_satin_alma.data, 'silme': form.modul_satin_alma.data},
            'dys': {'okuma': form.modul_dys.data, 'yazma': form.modul_dys.data, 'silme': form.modul_dys.data},
            'duyuru': {'okuma': form.modul_duyuru.data, 'yazma': form.modul_duyuru.data, 'silme': form.modul_duyuru.data}
        }
        kullanici.modul_erisim = modul_erisim
        
        # SQLAlchemy JSON güncellemelerini yakalaması için
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(kullanici, "modul_erisim")
        
        db.session.commit()
        flash(f'Kullanıcı {kullanici.kullanici_adi} güncellendi.', 'success')
        return redirect(url_for('admin.index'))
        
    return render_template('admin/form.html', form=form, title='Kullanıcı Düzenle')


@admin_bp.route('/denetim-izleri')
@login_required
@role_required('yonetici')
def denetim_izleri():
    """Sistem logları."""
    page = request.args.get('page', 1, type=int)
    loglar = DenetimIzi.query.order_by(DenetimIzi.tarih.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/loglar.html', loglar=loglar)


# ══════════════════════════════════════
#  Veritabanı Yedekleme
# ══════════════════════════════════════

@admin_bp.route('/yedekleme')
@login_required
@role_required('yonetici')
def yedekleme():
    """Veritabanı yedekleme yönetimi sayfası."""
    from app.utils.yedekleme import yedekleri_listele, veritabani_boyutu
    from flask import current_app
    yedekler = yedekleri_listele()
    db_boyut = veritabani_boyutu(current_app)
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_turu = 'PostgreSQL' if ('postgresql' in db_uri or 'postgres' in db_uri) else 'SQLite'
    return render_template('admin/yedekleme.html',
                           yedekler=yedekler,
                           db_boyut=db_boyut,
                           db_turu=db_turu)


@admin_bp.route('/yedekleme/olustur', methods=['POST'])
@login_required
@role_required('yonetici')
@log_action('Veritabanı Yedekleme')
def yedekleme_olustur():
    """Yeni veritabanı yedeği oluşturur."""
    from app.utils.yedekleme import yedek_olustur
    from flask import current_app
    sonuc = yedek_olustur(current_app)
    if sonuc['basarili']:
        flash(sonuc['mesaj'], 'success')
    else:
        flash(sonuc['mesaj'], 'danger')
    return redirect(url_for('admin.yedekleme'))


@admin_bp.route('/yedekleme/indir/<dosya_adi>')
@login_required
@role_required('yonetici')
def yedekleme_indir(dosya_adi):
    """Yedek dosyasını indirir."""
    from app.utils.yedekleme import yedek_yolu
    from flask import send_file
    yol = yedek_yolu(dosya_adi)
    if not yol:
        flash('Yedek dosyası bulunamadı.', 'danger')
        return redirect(url_for('admin.yedekleme'))
    return send_file(yol, as_attachment=True, download_name=dosya_adi)


@admin_bp.route('/yedekleme/sil/<dosya_adi>', methods=['POST'])
@login_required
@role_required('yonetici')
@log_action('Yedek Silme')
def yedekleme_sil(dosya_adi):
    """Yedek dosyasını siler."""
    from app.utils.yedekleme import yedek_sil
    sonuc = yedek_sil(dosya_adi)
    if sonuc['basarili']:
        flash(sonuc['mesaj'], 'info')
    else:
        flash(sonuc['mesaj'], 'danger')
    return redirect(url_for('admin.yedekleme'))


# ══════════════════════════════════════
#  Toplu İçe Aktarma (Import)
# ══════════════════════════════════════

@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
@role_required('yonetici')
def import_sayfa():
    """Toplu içe aktarma sayfası."""
    sonuc = None
    if request.method == 'POST':
        tip = request.form.get('tip', 'malzeme')
        dosya = request.files.get('dosya')
        if not dosya or dosya.filename == '':
            flash('Dosya seçilmedi.', 'warning')
            return render_template('admin/import.html', sonuc=None)

        from app.services.import_service import import_service
        if tip == 'malzeme':
            sonuc = import_service.import_malzeme(dosya)
        elif tip == 'calisan':
            sonuc = import_service.import_calisan(dosya)
        elif tip == 'makine':
            sonuc = import_service.import_makine(dosya)
        else:
            flash('Geçersiz veri türü.', 'danger')
            return render_template('admin/import.html', sonuc=None)

        if sonuc.basarili_mi:
            flash(f'{sonuc.basarili_sayisi} kayıt başarıyla içe aktarıldı.', 'success')
        elif sonuc.hatali_sayisi > 0:
            flash(f'{sonuc.hatali_sayisi} satırda hata bulundu.', 'warning')

    return render_template('admin/import.html', sonuc=sonuc)


@admin_bp.route('/import/sablon/<tip>')
@login_required
@role_required('yonetici')
def import_sablon(tip):
    """Import şablonu indir."""
    from flask import send_file
    from app.utils.import_templates import sablon_olustur
    try:
        buffer = sablon_olustur(tip)
        return send_file(buffer, as_attachment=True,
                         download_name=f'{tip}_import_sablonu.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.import_sayfa'))


# ══════════════════════════════════════
#  E-posta Ayarları
# ══════════════════════════════════════

@admin_bp.route('/eposta')
@login_required
@role_required('yonetici')
def eposta():
    """E-posta ayarları sayfası."""
    from app.models.eposta import EpostaAyarlari
    ayarlar = EpostaAyarlari.ayarlari_getir()
    return render_template('admin/eposta.html', ayarlar=ayarlar)


@admin_bp.route('/eposta/kaydet', methods=['POST'])
@login_required
@role_required('yonetici')
@log_action('E-posta Ayarları Güncelleme')
def eposta_kaydet():
    """E-posta SMTP ayarlarını kaydeder."""
    from app.models.eposta import EpostaAyarlari
    ayarlar = EpostaAyarlari.ayarlari_getir()

    ayarlar.smtp_host = request.form.get('smtp_host', '').strip()
    ayarlar.smtp_port = int(request.form.get('smtp_port', 587))
    ayarlar.smtp_kullanici = request.form.get('smtp_kullanici', '').strip()
    sifre = request.form.get('smtp_sifre', '').strip()
    if sifre:
        ayarlar.smtp_sifre = sifre
    ayarlar.ssl_aktif = 'ssl_aktif' in request.form
    ayarlar.tls_aktif = 'tls_aktif' in request.form
    ayarlar.gonderici_ad = request.form.get('gonderici_ad', 'FDYS Bildirim Sistemi').strip()
    ayarlar.gonderici_eposta = request.form.get('gonderici_eposta', '').strip()
    ayarlar.aktif = 'aktif' in request.form
    ayarlar.kritik_uyari_aktif = 'kritik_uyari_aktif' in request.form
    ayarlar.ariza_uyari_aktif = 'ariza_uyari_aktif' in request.form
    ayarlar.stok_uyari_aktif = 'stok_uyari_aktif' in request.form
    ayarlar.gunluk_ozet_aktif = 'gunluk_ozet_aktif' in request.form
    ayarlar.haftalik_ozet_aktif = 'haftalik_ozet_aktif' in request.form

    alicilar_str = request.form.get('ozet_alicilar', '').strip()
    ayarlar.ozet_alici_epostalar = [e.strip() for e in alicilar_str.split('\n') if e.strip()] if alicilar_str else []

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(ayarlar, 'ozet_alici_epostalar')

    db.session.commit()
    flash('E-posta ayarları kaydedildi.', 'success')
    return redirect(url_for('admin.eposta'))


@admin_bp.route('/eposta/test', methods=['POST'])
@login_required
@role_required('yonetici')
def eposta_test():
    """SMTP bağlantı testi."""
    from flask import jsonify
    from app.services.eposta_servisi import eposta_servisi
    sonuc = eposta_servisi.test_baglantisi()
    return jsonify(sonuc)

# ══════════════════════════════════════
#  Kurumsal Ayarlar (White-Labeling)
# ══════════════════════════════════════

@admin_bp.route('/kurumsal', methods=['GET', 'POST'])
@login_required
@role_required('yonetici')
@log_action('Kurumsal Ayarlar Güncelleme')
def kurumsal():
    from app.models.kurumsal import KurumsalAyarlar
    from flask import current_app
    import os
    from werkzeug.utils import secure_filename
    
    ayarlar = KurumsalAyarlar.ayarlari_getir()

    if request.method == 'POST':
        ayarlar.sirket_adi = request.form.get('sirket_adi', 'FabrikaOS')
        ayarlar.ana_renk = request.form.get('ana_renk', '#0d6efd')
        
        logo = request.files.get('logo')
        if logo and logo.filename != '':
            filename = secure_filename(logo.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            logo.save(file_path)
            ayarlar.logo_path = f'img/uploads/{filename}'
            
        db.session.commit()
        flash('Kurumsal ayarlar başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.kurumsal'))

    return render_template('admin/kurumsal.html', ayarlar=ayarlar)


# ══════════════════════════════════════
#  Entegrasyon Merkezi
# ══════════════════════════════════════

@admin_bp.route('/entegrasyon')
@login_required
@role_required('yonetici')
def entegrasyon():
    return render_template('admin/entegrasyon.html')


# ══════════════════════════════════════
#  Kapsamlı Rol ve Yetki Matrisi
# ══════════════════════════════════════

@admin_bp.route('/yetki-matrisi', methods=['GET', 'POST'])
@login_required
@role_required('yonetici')
@log_action('Yetki Matrisi Güncelleme')
def yetki_matrisi():
    kullanicilar = Kullanici.query.filter(Kullanici.rol != 'yonetici').all()
    moduller = ['personel', 'makine', 'stok', 'kalite', 'enerji', 'isg', 'ik', 'crm', 'sozlesme', 'talep', 'satin_alma', 'dys', 'duyuru']
    
    if request.method == 'POST':
        from sqlalchemy.orm.attributes import flag_modified
        for k in kullanicilar:
            yeni_erisim = {}
            for m in moduller:
                # Checkbox name format: user_ID_module
                checkbox_name = f"user_{k.id}_{m}"
                secili = checkbox_name in request.form
                yeni_erisim[m] = {'okuma': secili, 'yazma': secili, 'silme': secili}
            
            k.modul_erisim = yeni_erisim
            flag_modified(k, 'modul_erisim')
            
        db.session.commit()
        flash('Yetki matrisi başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.yetki_matrisi'))
        
    return render_template('admin/yetki_matrisi.html', kullanicilar=kullanicilar, moduller=moduller)
