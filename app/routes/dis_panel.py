"""
FDYS — Dış Kullanıcı Paneli Route'ları
Faz 4 — Müşteri/Ortak Portalı (Borç & Talep Takibi)
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, current_user

from app.extensions import db
from app.models.dis_kullanici import DisKullanici, Borc, Tahsilat
from app.models.talep import Talep
from app.forms.dis_panel import DisKullaniciLoginForm, SifreDegistirForm, ProfilGuncelleForm
from app.forms.talep import TalepForm, MemnuniyetForm
from app.services import talep_servisi, sms_servisi

dis_panel_bp = Blueprint('dis_panel', __name__, url_prefix='/panel')


# ──────────────────────────────────────────────
# KİMLİK DOĞRULAMA & GÜVENLİK
# ──────────────────────────────────────────────

def dis_kullanici_gerekli(f):
    """Sadece dış kullanıcıların erişimini sağlar."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Normal kullanici_id session'da yoksa veya dış kullanıcı değilse
        if not session.get('dis_kullanici_id'):
            flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('dis_panel.giris', next=request.url))
            
        # Kullanıcı veritabanında var mı kontrolü
        dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
        if not dk:
            session.pop('dis_kullanici_id', None)
            flash('Oturumunuz geçersiz veya kullanıcı silinmiş. Lütfen tekrar giriş yapın.', 'danger')
            return redirect(url_for('dis_panel.giris'))
            
        # Şifre değiştirme zorunluluğu kontrolü
        if dk.gecici_sifre and request.endpoint != 'dis_panel.sifre_degistir' and request.endpoint != 'dis_panel.cikis':
            flash('Güvenliğiniz için geçici şifrenizi değiştirmelisiniz.', 'warning')
            return redirect(url_for('dis_panel.sifre_degistir'))
            
        return f(*args, **kwargs)
    return decorated_function


@dis_panel_bp.context_processor
def inject_dis_kullanici():
    """Tüm dış panel template'lerine dış kullanıcıyı enjekte eder."""
    dk = None
    if session.get('dis_kullanici_id'):
        dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    return dict(dis_kullanici=dk)


@dis_panel_bp.route('/giris', methods=['GET', 'POST'])
def giris():
    """Dış kullanıcı giriş sayfası."""
    if session.get('dis_kullanici_id'):
        return redirect(url_for('dis_panel.index'))

    form = DisKullaniciLoginForm()
    if form.validate_on_submit():
        dk = DisKullanici.query.filter_by(kullanici_adi=form.kullanici_adi.data, aktif=True).first()

        if dk and dk.sifre_dogrula(form.sifre.data):
            dk.giris_basarili()
            db.session.commit()
            
            # Kendi session mekanizmamızı kullanalım (dahili sistemle karışmaması için)
            session['dis_kullanici_id'] = dk.id
            session.permanent = form.hatirla.data
            
            return redirect(url_for('dis_panel.index'))
            
        flash('Geçersiz kullanıcı adı veya şifre.', 'danger')

    return render_template('dis_panel/giris.html', form=form)


@dis_panel_bp.route('/cikis')
def cikis():
    """Çıkış yap."""
    session.pop('dis_kullanici_id', None)
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('dis_panel.giris'))


@dis_panel_bp.route('/sifre-degistir', methods=['GET', 'POST'])
@dis_kullanici_gerekli
def sifre_degistir():
    """Geçici şifreyi değiştirme."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    form = SifreDegistirForm()
    
    if form.validate_on_submit():
        if dk.sifre_dogrula(form.eski_sifre.data):
            dk.sifre_belirle(form.yeni_sifre.data)
            dk.gecici_sifre = False
            db.session.commit()
            
            flash('Şifreniz başarıyla güncellendi.', 'success')
            return redirect(url_for('dis_panel.index'))
        else:
            flash('Mevcut şifrenizi yanlış girdiniz.', 'danger')
            
    return render_template('dis_panel/sifre_degistir.html', form=form)


# ──────────────────────────────────────────────
# DASHBOARD & PROFİL
# ──────────────────────────────────────────────

@dis_panel_bp.route('/')
@dis_kullanici_gerekli
def index():
    """Dış kullanıcı ana paneli (Dashboard)."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    stats = talep_servisi.dis_panel_dashboard(dk)
    return render_template('dis_panel/index.html', stats=stats)


@dis_panel_bp.route('/profil', methods=['GET', 'POST'])
@dis_kullanici_gerekli
def profil():
    """Profil bilgilerini görüntüleme ve güncelleme."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    form = ProfilGuncelleForm(obj=dk)
    
    if form.validate_on_submit():
        form.populate_obj(dk)
        db.session.commit()
        flash('Profil bilgileriniz güncellendi.', 'success')
        return redirect(url_for('dis_panel.profil'))
        
    return render_template('dis_panel/profil.html', form=form)


# ──────────────────────────────────────────────
# TALEP İŞLEMLERİ
# ──────────────────────────────────────────────

@dis_panel_bp.route('/taleplerim')
@dis_kullanici_gerekli
def taleplerim():
    """Kullanıcının kendi talepleri."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    
    # Kendi ID'si veya bağlı olduğu ortak/firma ID'si ile açılan talepler
    from sqlalchemy import or_, and_
    talepler = Talep.query.filter(
        Talep.aktif == True,
        or_(
            and_(Talep.talep_eden_tip == Talep.TIP_DIS_KULLANICI, Talep.talep_eden_id == dk.id),
            and_(Talep.talep_eden_tip == Talep.TIP_ORTAK, Talep.talep_eden_id == dk.ortak_id) if dk.ortak_id else False,
            and_(Talep.talep_eden_tip == Talep.TIP_FIRMA, Talep.talep_eden_id == dk.firma_id) if dk.firma_id else False,
        )
    ).order_by(Talep.olusturma_tarihi.desc()).all()
    
    return render_template('dis_panel/taleplerim.html', talepler=talepler)


@dis_panel_bp.route('/yeni-talep', methods=['GET', 'POST'])
@dis_kullanici_gerekli
def yeni_talep():
    """Yeni talep/şikayet oluştur."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    form = TalepForm()
    
    if form.validate_on_submit():
        talep = Talep(
            talep_eden_tip=Talep.TIP_DIS_KULLANICI,
            talep_eden_id=dk.id,
            talep_eden_adi=dk.ad_soyad,
            baslik=form.baslik.data,
            aciklama=form.aciklama.data,
            kategori=form.kategori.data,
            oncelik=Talep.ONCELIK_NORMAL,  # Dış kullanıcı her zaman normal açar (idari karar verebilir)
            sms_bildirim=True,
        )
        
        talep = talep_servisi.talep_olustur(talep, yapan_id=None, yapan_adi=dk.ad_soyad)
        
        # Kullanıcıya SMS gönder (opsiyonel)
        if dk.telefon:
            sms_servisi.talep_olusturuldu_sms(dk.telefon, talep.talep_no, talep.baslik)
            
        flash(f'Talebiniz başarıyla oluşturuldu. Takip Numarası: {talep.talep_no}', 'success')
        return redirect(url_for('dis_panel.talep_detay', id=talep.id))
        
    return render_template('dis_panel/yeni_talep.html', form=form)


@dis_panel_bp.route('/taleplerim/<int:id>', methods=['GET', 'POST'])
@dis_kullanici_gerekli
def talep_detay(id):
    """Talep detayı ve memnuniyet anketi."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    talep = db.session.get(Talep, id)
    
    # Güvenlik kontrolü
    if not talep or not (
        (talep.talep_eden_tip == Talep.TIP_DIS_KULLANICI and talep.talep_eden_id == dk.id) or
        (talep.talep_eden_tip == Talep.TIP_ORTAK and talep.talep_eden_id == dk.ortak_id) or
        (talep.talep_eden_tip == Talep.TIP_FIRMA and talep.talep_eden_id == dk.firma_id)
    ):
        flash('Talep bulunamadı veya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dis_panel.taleplerim'))
        
    memnuniyet_form = MemnuniyetForm()
    memnuniyet_form.talep_id.data = talep.id
    
    if memnuniyet_form.validate_on_submit() and talep.durum == Talep.DURUM_TAMAMLANDI:
        talep.memnuniyet_puani = memnuniyet_form.puan.data
        if memnuniyet_form.yorum.data:
            talep_servisi.talep_yorum_ekle(
                talep.id, 
                f"Memnuniyet Puanı: {talep.memnuniyet_puani}/5. Görüş: {memnuniyet_form.yorum.data}",
                yapan_adi=dk.ad_soyad
            )
        
        # Talebi tamamen kapat
        talep.durum = Talep.DURUM_KAPANDI
        db.session.commit()
        flash('Değerlendirmeniz için teşekkür ederiz.', 'success')
        return redirect(url_for('dis_panel.talep_detay', id=talep.id))
        
    return render_template('dis_panel/talep_detay.html', talep=talep, form=memnuniyet_form)


# ──────────────────────────────────────────────
# BORÇ & ÖDEME İŞLEMLERİ
# ──────────────────────────────────────────────

@dis_panel_bp.route('/borclarim')
@dis_kullanici_gerekli
def borclarim():
    """Bağlı ortak/firmanın borç tablosu."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    
    borc_ozeti = {'toplam_kalan': 0, 'borclar': []}
    if dk.ortak_id:
        borc_ozeti = talep_servisi.kisi_borc_ozeti('ortak', dk.ortak_id)
    elif dk.firma_id:
        borc_ozeti = talep_servisi.kisi_borc_ozeti('firma', dk.firma_id)
        
    return render_template('dis_panel/borclarim.html', ozet=borc_ozeti)


@dis_panel_bp.route('/odeme/<int:borc_id>')
@dis_kullanici_gerekli
def odeme(borc_id):
    """Sanal POS simülasyon sayfası."""
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    borc = db.session.get(Borc, borc_id)
    
    if not borc or float(borc.kalan_tutar) <= 0:
        flash('Geçersiz işlem veya borç zaten ödenmiş.', 'danger')
        return redirect(url_for('dis_panel.borclarim'))
        
    # Güvenlik
    if (borc.ilgili_tip == 'ortak' and borc.ilgili_id != dk.ortak_id) or \
       (borc.ilgili_tip == 'firma' and borc.ilgili_id != dk.firma_id):
        flash('Bu işleme yetkiniz yok.', 'danger')
        return redirect(url_for('dis_panel.borclarim'))
        
    return render_template('dis_panel/odeme.html', borc=borc)


@dis_panel_bp.route('/odeme-basarili/<int:borc_id>', methods=['POST'])
@dis_kullanici_gerekli
def odeme_basarili(borc_id):
    """Sanal POS başarılı dönüş (simülasyon)."""
    # Gerçek sistemde bu uç nokta POS sağlayıcısından callback alır
    dk = db.session.get(DisKullanici, session['dis_kullanici_id'])
    borc = db.session.get(Borc, borc_id)
    
    if borc:
        tutar = request.form.get('tutar', type=float)
        if tutar and tutar > 0:
            talep_servisi.tahsilat_kaydet(
                borc.id, 
                tutar, 
                Tahsilat.TUR_CEVRIMICI, 
                aciklama='Online panel üzerinden ödeme',
                kaydeden_id=None
            )
            flash('Ödemeniz başarıyla alındı. Teşekkür ederiz.', 'success')
            
    return redirect(url_for('dis_panel.borclarim'))
