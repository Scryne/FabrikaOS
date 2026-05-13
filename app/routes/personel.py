"""FDYS — Personel Yönetimi Rotaları"""

import os
from datetime import datetime, date, timedelta, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, log_action
from app.models.personel import Calisan, VardiyaPlani, IzinTalebi
from app.models.kullanici import Kullanici
from app.models.makine import Makine
from app.forms.personel import CalisanForm, VardiyaForm, IzinTalebiForm
from werkzeug.utils import secure_filename
from app.utils.security import is_secure_image

personel_bp = Blueprint('personel', __name__, url_prefix='/personel')


@personel_bp.route('/')
@login_required
@modul_erisim_gerekli('personel')
def index():
    """Çalışan listesi sayfası (arama, filtreleme, pagination)."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    departman = request.args.get('departman', '')
    
    query = Calisan.query.filter_by(aktif=True)
    
    if search:
        query = query.filter(or_(
            Calisan.ad_soyad.ilike(f'%{search}%'),
            Calisan.sicil_no.ilike(f'%{search}%')
        ))
    if departman:
        query = query.filter_by(departman=departman)
        
    calisanlar = query.order_by(Calisan.ad_soyad).paginate(page=page, per_page=10, error_out=False)
    
    departmanlar = db.session.query(Calisan.departman).distinct().all()
    departmanlar = [d[0] for d in departmanlar if d[0]]
    
    return render_template('personel/index.html', calisanlar=calisanlar, search=search, 
                           departman=departman, departmanlar=departmanlar)


@personel_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('Çalışan Ekleme')
def ekle():
    """Yeni çalışan ekleme sayfası."""
    form = CalisanForm()
    if form.validate_on_submit():
        if Calisan.query.filter_by(sicil_no=form.sicil_no.data).first():
            flash('Bu sicil numarası zaten kullanılıyor.', 'danger')
            return render_template('personel/form.html', form=form, title='Çalışan Ekle')
            
        calisan = Calisan(
            sicil_no=form.sicil_no.data,
            ad_soyad=form.ad_soyad.data,
            departman=form.departman.data,
            pozisyon=form.pozisyon.data,
            telefon=form.telefon.data,
            eposta=form.eposta.data,
            ise_baslama=form.ise_baslama.data,
            ucret=form.ucret.data,
            aktif=True
        )
        
        # Profil Fotoğrafı İşleme
        if 'fotograf' in request.files:
            file = request.files['fotograf']
            if file.filename != '':
                if is_secure_image(file, file.filename):
                    filename = secure_filename(f"{calisan.sicil_no}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    calisan.fotograf = filename
                else:
                    flash('Geçersiz dosya formatı. Sadece geçerli resim dosyaları (jpg, jpeg, png) yüklenebilir.', 'warning')
        
        db.session.add(calisan)
        db.session.commit()
        flash(f'Çalışan {calisan.ad_soyad} başarıyla eklendi.', 'success')
        return redirect(url_for('personel.index'))
        
    return render_template('personel/form.html', form=form, title='Çalışan Ekle')


@personel_bp.route('/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('Çalışan Düzenleme')
def duzenle(id):
    """Çalışan düzenleme sayfası."""
    calisan = Calisan.query.get_or_404(id)
    form = CalisanForm(obj=calisan)
    
    if form.validate_on_submit():
        if calisan.sicil_no != form.sicil_no.data and Calisan.query.filter_by(sicil_no=form.sicil_no.data).first():
            flash('Bu sicil numarası zaten kullanılıyor.', 'danger')
            return render_template('personel/form.html', form=form, calisan=calisan, title='Çalışan Düzenle')
            
        form.populate_obj(calisan)
        
        # Profil Fotoğrafı İşleme
        if 'fotograf' in request.files:
            file = request.files['fotograf']
            if file.filename != '':
                if is_secure_image(file, file.filename):
                    filename = secure_filename(f"{calisan.sicil_no}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    calisan.fotograf = filename
                else:
                    flash('Geçersiz dosya formatı. Sadece geçerli resim dosyaları (jpg, jpeg, png) yüklenebilir.', 'warning')
                    
        db.session.commit()
        flash(f'Çalışan {calisan.ad_soyad} başarıyla güncellendi.', 'success')
        return redirect(url_for('personel.detay', id=calisan.id))
        
    return render_template('personel/form.html', form=form, calisan=calisan, title='Çalışan Düzenle')


@personel_bp.route('/detay/<int:id>')
@login_required
@modul_erisim_gerekli('personel')
def detay(id):
    """Çalışan detay sayfası."""
    calisan = Calisan.query.get_or_404(id)
    makineler = Makine.query.filter_by(aktif=True).all()
    return render_template('personel/detay.html', calisan=calisan, makineler=makineler)


@personel_bp.route('/sil/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('Çalışan Silme (Soft Delete)')
def sil(id):
    """Çalışan silme (soft delete) işlemi. Sadece yöneticiler silebilir."""
    if not current_user.yonetici_mi():
        flash('Personel silme işlemi için yönetici yetkisi gereklidir.', 'danger')
        return redirect(url_for('personel.index'))
        
    calisan = Calisan.query.get_or_404(id)
    calisan.aktif = False
    db.session.commit()
    flash(f'Çalışan {calisan.ad_soyad} sistemden kaldırıldı.', 'success')
    return redirect(url_for('personel.index'))


@personel_bp.route('/vardiya', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('personel')
def vardiya():
    """Haftalık vardiya çizelgesi ve atama sayfası."""
    # Hafta hesaplaması
    today = date.today()
    start_date_str = request.args.get('start_date')
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=today.weekday()) # Monday
        
    end_date = start_date + timedelta(days=6)
    
    # Tüm aktif çalışanları getir
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    
    # Belirtilen haftanın vardiya planlarını getir
    vardiyalar_raw = VardiyaPlani.query.filter(
        VardiyaPlani.tarih >= start_date,
        VardiyaPlani.tarih <= end_date
    ).all()
    
    # Vardiyaları daha kolay göstermek için matrise dönüştür
    vardiya_matrisi = {}
    gunler = [start_date + timedelta(days=i) for i in range(7)]
    
    for c in calisanlar:
        vardiya_matrisi[c.id] = { gun: None for gun in gunler }
        
    for v in vardiyalar_raw:
        if v.calisan_id in vardiya_matrisi:
            vardiya_matrisi[v.calisan_id][v.tarih] = v

    return render_template('personel/vardiya.html', 
                           calisanlar=calisanlar, 
                           vardiya_matrisi=vardiya_matrisi,
                           gunler=gunler,
                           start_date=start_date,
                           end_date=end_date,
                           today=today)

@personel_bp.route('/vardiya/ata/<int:calisan_id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('Vardiya Atama')
def vardiya_ata(calisan_id):
    """Belirli bir çalışana vardiya atama sayfası."""
    calisan = Calisan.query.get_or_404(calisan_id)
    tarih_str = request.args.get('tarih')
    tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else date.today()
    
    mevcut_vardiya = VardiyaPlani.query.filter_by(calisan_id=calisan_id, tarih=tarih).first()
    
    form = VardiyaForm(obj=mevcut_vardiya)
    if request.method == 'GET' and not mevcut_vardiya:
        form.tarih.data = tarih
        
    if form.validate_on_submit():
        # Çakışma kontrolü
        # Bir kişinin o gün başka vardiyası olamaz, varsa güncelliyoruz. (Zaten filter_by yaptık)
        if mevcut_vardiya:
            mevcut_vardiya.vardiya_turu = form.vardiya_turu.data
            mevcut_vardiya.baslangic = form.baslangic.data
            mevcut_vardiya.bitis = form.bitis.data
            mevcut_vardiya.notlar = form.notlar.data
            flash(f'{calisan.ad_soyad} için {form.tarih.data} vardiyası güncellendi.', 'success')
        else:
            yeni_vardiya = VardiyaPlani(
                calisan_id=calisan_id,
                tarih=form.tarih.data,
                vardiya_turu=form.vardiya_turu.data,
                baslangic=form.baslangic.data,
                bitis=form.bitis.data,
                notlar=form.notlar.data
            )
            db.session.add(yeni_vardiya)
            flash(f'{calisan.ad_soyad} için {form.tarih.data} tarihine vardiya atandı.', 'success')
            
        db.session.commit()
        return redirect(url_for('personel.vardiya', start_date=(form.tarih.data - timedelta(days=form.tarih.data.weekday())).strftime('%Y-%m-%d')))
        
    return render_template('personel/vardiya_form.html', form=form, calisan=calisan, mevcut=mevcut_vardiya)

@personel_bp.route('/vardiya/sil/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('Vardiya Silme')
def vardiya_sil(id):
    vardiya = VardiyaPlani.query.get_or_404(id)
    db.session.delete(vardiya)
    db.session.commit()
    flash('Vardiya planı silindi.', 'success')
    return redirect(url_for('personel.vardiya'))

@personel_bp.route('/izinler', methods=['GET'])
@login_required
@modul_erisim_gerekli('personel')
def izinler():
    """Tüm izin talepleri."""
    durum = request.args.get('durum', 'bekliyor')
    page = request.args.get('page', 1, type=int)
    
    izinler_pagination = IzinTalebi.query.filter_by(durum=durum).order_by(IzinTalebi.baslangic_tarihi.desc()).paginate(
        page=page, per_page=15, error_out=False)
        
    return render_template('personel/izinler.html', 
                           izinler=izinler_pagination.items, 
                           pagination=izinler_pagination,
                           durum=durum)

@personel_bp.route('/izin/talep/<int:calisan_id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('İzin Talebi Oluşturma')
def izin_talep(calisan_id):
    calisan = Calisan.query.get_or_404(calisan_id)
    form = IzinTalebiForm()
    
    if form.validate_on_submit():
        talep = IzinTalebi(
            calisan_id=calisan_id,
            baslangic_tarihi=form.baslangic_tarihi.data,
            bitis_tarihi=form.bitis_tarihi.data,
            tur=form.tur.data,
            aciklama=form.aciklama.data,
            durum='bekliyor'
        )
        db.session.add(talep)
        db.session.commit()
        
        # Bildirim motoru - yöneticiye bildirim
        from app.services.bildirim_motoru import bildirim_motoru
        yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()
        for y in yoneticiler:
            bildirim_motoru.bildirim_olustur(
                kullanici_id=y.id,
                baslik='Yeni İzin Talebi',
                mesaj=f'{calisan.ad_soyad} yeni bir izin talebinde bulundu.',
                seviye='bilgi',
                modul='personel',
                url=url_for('personel.izinler')
            )
            
        flash('İzin talebi başarıyla oluşturuldu ve onaya gönderildi.', 'success')
        return redirect(url_for('personel.detay', id=calisan_id))
        
    return render_template('personel/izin_form.html', form=form, calisan=calisan)

@personel_bp.route('/izin/onayla/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('İzin Onaylama')
def izin_onayla(id):
    if not current_user.yonetici_mi():
        flash('İzin onaylamak için yönetici yetkisi gereklidir.', 'danger')
        return redirect(url_for('personel.izinler'))
        
    talep = IzinTalebi.query.get_or_404(id)
    talep.durum = 'onaylandi'
    talep.onaylayan_id = current_user.id
    talep.onay_tarihi = datetime.now(timezone.utc)
    db.session.commit()
    flash(f'{talep.calisan.ad_soyad} için izin talebi onaylandı.', 'success')
    return redirect(url_for('personel.izinler'))

@personel_bp.route('/izin/reddet/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('İzin Reddetme')
def izin_reddet(id):
    if not current_user.yonetici_mi():
        flash('İzin reddetmek için yönetici yetkisi gereklidir.', 'danger')
        return redirect(url_for('personel.izinler'))
        
    talep = IzinTalebi.query.get_or_404(id)
    red_nedeni = request.form.get('red_nedeni', '')
    talep.durum = 'reddedildi'
    talep.onaylayan_id = current_user.id
    talep.onay_tarihi = datetime.now(timezone.utc)
    talep.red_nedeni = red_nedeni
    db.session.commit()
    flash(f'{talep.calisan.ad_soyad} için izin talebi reddedildi.', 'warning')
    return redirect(url_for('personel.izinler'))

@personel_bp.route('/yetkinlik/<int:id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('personel')
@log_action('Yetkinlik Güncelleme')
def yetkinlik_guncelle(id):
    """Çalışan yetkinlik puanını günceller."""
    calisan = Calisan.query.get_or_404(id)
    makine_id = request.form.get('makine_id', type=int)
    puan = request.form.get('puan', type=int)
    
    if not makine_id or puan is None or puan < 0 or puan > 5:
        flash('Geçersiz yetkinlik verisi.', 'danger')
        return redirect(url_for('personel.detay', id=id))
        
    # Mevcut becerileri al veya yeni liste oluştur
    beceriler = calisan.beceri_json.copy() if calisan.beceri_json else []
    
    # İlgili makine_id varsa bul ve güncelle, yoksa ekle
    bulundu = False
    for b in beceriler:
        if b.get('makine_id') == makine_id:
            b['puan'] = puan
            bulundu = True
            break
            
    if not bulundu:
        beceriler.append({'makine_id': makine_id, 'puan': puan})
        
    # JSON verisini güncelle
    calisan.beceri_json = beceriler
    
    # SQLAlchemy JSON değişikliklerini bazen algılayamaz, explicitly markle
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(calisan, "beceri_json")
    
    db.session.commit()
    flash('Yetkinlik matrisi güncellendi.', 'success')
    return redirect(url_for('personel.detay', id=id))

@personel_bp.route('/oner', methods=['GET'])
@login_required
@modul_erisim_gerekli('personel')
def oner():
    """Kim Çalışabilir? Öneri algoritması."""
    makine_id = request.args.get('makine_id', type=int)
    tarih_str = request.args.get('tarih')
    vardiya_turu = request.args.get('vardiya_turu')
    
    makineler = Makine.query.filter_by(aktif=True).all()
    oneriler = []
    
    if makine_id and tarih_str and vardiya_turu:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
        
        calisanlar = Calisan.query.filter_by(aktif=True).all()
        for c in calisanlar:
            puan = c.yetkinlik_puani(makine_id)
            if puan > 0:
                # İzin kontrolü
                izinli_mi = IzinTalebi.query.filter(
                    IzinTalebi.calisan_id == c.id,
                    IzinTalebi.durum == 'onaylandi',
                    IzinTalebi.baslangic_tarihi <= tarih,
                    IzinTalebi.bitis_tarihi >= tarih
                ).first()
                
                if izinli_mi:
                    continue
                    
                # Başka vardiyada çalışıyor mu kontrolü
                baska_vardiya = VardiyaPlani.query.filter(
                    VardiyaPlani.calisan_id == c.id,
                    VardiyaPlani.tarih == tarih,
                    VardiyaPlani.vardiya_turu != 'off'
                ).first()
                
                durum = 'Müsait'
                if baska_vardiya:
                    if baska_vardiya.vardiya_turu == vardiya_turu:
                        durum = 'Zaten bu vardiyada'
                    else:
                        durum = f'Başka vardiyada ({baska_vardiya.vardiya_turu})'
                        
                oneriler.append({
                    'calisan': c,
                    'puan': puan,
                    'durum': durum
                })
                
        # Puana göre azalan sırala
        oneriler = sorted(oneriler, key=lambda x: x['puan'], reverse=True)
        
    return render_template('personel/oner.html', makineler=makineler, oneriler=oneriler, 
                           makine_id=makine_id, tarih=tarih_str, vardiya_turu=vardiya_turu)


@personel_bp.route('/izin/self-talep', methods=['POST'])
@login_required
def izin_self_talep():
    """Çalışanın kendi izin talebini oluşturması (operatör/teknisyen erişimli)."""
    if not current_user.calisan:
        flash('İzin talebi oluşturabilmek için sisteme bağlı bir çalışan kaydınız olmalıdır.', 'warning')
        return redirect(url_for('dashboard.index'))

    baslangic_str = request.form.get('baslangic_tarihi', '')
    bitis_str = request.form.get('bitis_tarihi', '')
    tur = request.form.get('tur', 'yillik')
    aciklama = request.form.get('aciklama', '')

    try:
        baslangic = datetime.strptime(baslangic_str, '%Y-%m-%d').date()
        bitis = datetime.strptime(bitis_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Geçersiz tarih formatı.', 'danger')
        return redirect(url_for('dashboard.index'))

    if bitis < baslangic:
        flash('Bitiş tarihi başlangıç tarihinden önce olamaz.', 'danger')
        return redirect(url_for('dashboard.index'))

    talep = IzinTalebi(
        calisan_id=current_user.calisan.id,
        baslangic_tarihi=baslangic,
        bitis_tarihi=bitis,
        tur=tur,
        aciklama=aciklama,
        durum='bekliyor'
    )
    db.session.add(talep)
    db.session.commit()

    # Yöneticiye bildirim
    from app.services.bildirim_motoru import bildirim_motoru
    yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()
    for y in yoneticiler:
        bildirim_motoru.bildirim_olustur(
            kullanici_id=y.id,
            baslik='Yeni İzin Talebi (Self-Service)',
            mesaj=f'{current_user.calisan.ad_soyad} — {tur} izni ({baslangic_str} — {bitis_str})',
            seviye='bilgi',
            modul='personel',
            url=url_for('personel.izinler')
        )

    flash('İzin talebiniz başarıyla oluşturuldu ve yönetici onayına gönderildi.', 'success')
    return redirect(url_for('dashboard.index'))
