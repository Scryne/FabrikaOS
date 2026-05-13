"""FDYS — Kalite Kontrol Modülü Rotaları (Faz 4 — Kurumsal)"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.kalite import HataKaydi, DuzelticiFaaliyet
from app.models.makine import Makine
from app.models.personel import Calisan
from app.models.kullanici import Kullanici
from app.forms.kalite_isg_enerji import HataKaydiForm, DuzelticiFaaliyetForm
from app.utils.decorators import modul_erisim_gerekli, log_action
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

kalite_bp = Blueprint('kalite', __name__, url_prefix='/kalite')


@kalite_bp.route('/')
@login_required
@modul_erisim_gerekli('kalite')
def index():
    """Kalite kontrol paneli — Pareto analizi, hata trendi, istatistikler."""
    sayfa = request.args.get('sayfa', 1, type=int)
    hata_kayitlari = HataKaydi.query.order_by(HataKaydi.tarih.desc()).paginate(
        page=sayfa, per_page=20, error_out=False
    )

    # Pareto verisi (Kategorilere göre hata toplamları)
    pareto_data = db.session.query(HataKaydi.hata_kategorisi, func.sum(HataKaydi.adet))\
        .group_by(HataKaydi.hata_kategorisi)\
        .order_by(func.sum(HataKaydi.adet).desc()).all()

    pareto_labels = [d[0] or 'Belirsiz' for d in pareto_data]
    pareto_values = [int(d[1]) for d in pareto_data]

    # Toplam hatalı ürün sayısı
    toplam_hata_adet = db.session.query(func.sum(HataKaydi.adet)).scalar() or 0

    # Son 7 gün trend (günlük hata toplamları)
    yedi_gun_once = datetime.now(timezone.utc) - timedelta(days=7)
    gunluk_trend = db.session.query(
        func.date(HataKaydi.tarih), func.sum(HataKaydi.adet)
    ).filter(HataKaydi.tarih >= yedi_gun_once)\
     .group_by(func.date(HataKaydi.tarih))\
     .order_by(func.date(HataKaydi.tarih)).all()

    trend_labels = [d[0] if isinstance(d[0], str) else d[0].strftime('%d.%m') if d[0] else '' for d in gunluk_trend]
    trend_values = [int(d[1]) for d in gunluk_trend]

    # Toplam kayıt sayısı
    toplam_kayit = HataKaydi.query.count()

    # Açık düzeltici faaliyetler
    acik_faaliyetler = DuzelticiFaaliyet.query.filter(
        DuzelticiFaaliyet.durum.in_(['acik', 'devam', 'dogrulama'])
    ).count()

    # En çok hata veren makine
    en_hatali_makine = db.session.query(Makine.ad, func.sum(HataKaydi.adet))\
        .join(HataKaydi, HataKaydi.makine_id == Makine.id)\
        .group_by(Makine.ad)\
        .order_by(func.sum(HataKaydi.adet).desc()).first()

    return render_template('kalite/index.html',
                           hata_kayitlari=hata_kayitlari,
                           pareto={'labels': pareto_labels, 'values': pareto_values},
                           trend={'labels': trend_labels, 'values': trend_values},
                           stats={
                               'toplam_kayit': toplam_kayit,
                               'toplam_hata_adet': toplam_hata_adet,
                               'acik_faaliyetler': acik_faaliyetler,
                               'en_hatali_makine': en_hatali_makine,
                           })


@kalite_bp.route('/hata-kaydet', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('kalite')
@log_action('Kalite Hata Kaydı')
def hata_kaydet():
    form = HataKaydiForm()
    form.makine_id.choices = [(0, '--- Seçiniz ---')] + [(m.id, m.ad) for m in Makine.query.filter_by(aktif=True).all()]
    form.calisan_id.choices = [(0, '--- Seçiniz ---')] + [(c.id, c.ad_soyad) for c in Calisan.query.filter_by(aktif=True).all()]

    if form.validate_on_submit():
        hata = HataKaydi(
            makine_id=form.makine_id.data if form.makine_id.data != 0 else None,
            calisan_id=form.calisan_id.data if form.calisan_id.data != 0 else None,
            urun_adi=form.urun_adi.data,
            parti_no=form.parti_no.data,
            hat=form.hat.data,
            tarih=datetime.combine(form.tarih.data, datetime.min.time()),
            hata_turu=form.hata_turu.data,
            hata_kategorisi=form.hata_kategorisi.data,
            hata_kaynagi=form.hata_kaynagi.data,
            adet=form.adet.data,
            fire_orani=form.fire_orani.data,
            vardiya=form.vardiya.data,
            aksiyon_karari=form.aksiyon_karari.data,
            aciklama=form.aciklama.data,
            kaydeden_id=current_user.id
        )
        db.session.add(hata)
        db.session.commit()

        # Eğer adet yüksekse bildirim gönder
        if hata.adet > 10 or (hata.fire_orani and float(hata.fire_orani) > 5.0):
            from app.services.bildirim_motoru import bildirim_motoru
            yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik="Yüksek Kalite Hatası!",
                    mesaj=f"{hata.urun_adi} ürününde {hata.adet} adet {hata.hata_kategorisi} hatası tespit edildi.",
                    seviye="uyari",
                    modul="kalite",
                    url=url_for('kalite.index')
                )

        flash('Hata kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('kalite.index'))

    return render_template('kalite/hata_form.html', form=form)


@kalite_bp.route('/duzeltici-faaliyetler')
@login_required
@modul_erisim_gerekli('kalite')
def faaliyetler():
    """Tüm düzeltici faaliyetlerin listesi."""
    durum_filtre = request.args.get('durum', 'tumu')

    query = DuzelticiFaaliyet.query
    if durum_filtre != 'tumu':
        query = query.filter_by(durum=durum_filtre)

    page = request.args.get('page', 1, type=int)
    liste_pagination = query.order_by(DuzelticiFaaliyet.olusturma_tarihi.desc()).paginate(
        page=page, per_page=15, error_out=False)

    # İstatistikler
    acik = DuzelticiFaaliyet.query.filter_by(durum='acik').count()
    devam = DuzelticiFaaliyet.query.filter_by(durum='devam').count()
    dogrulama = DuzelticiFaaliyet.query.filter_by(durum='dogrulama').count()
    kapandi = DuzelticiFaaliyet.query.filter_by(durum='kapandi').count()

    return render_template('kalite/faaliyetler.html',
                           faaliyetler=liste_pagination.items,
                           pagination=liste_pagination,
                           aktif_filtre=durum_filtre,
                           stats={'acik': acik, 'devam': devam, 'dogrulama': dogrulama, 'kapandi': kapandi})


@kalite_bp.route('/duzeltici-faaliyet-ekle/<int:hata_id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('kalite')
@log_action('Düzeltici Faaliyet Başlatma')
def faaliyet_ekle(hata_id):
    """Hata kaydına düzeltici faaliyet başlatır."""
    hata = HataKaydi.query.get_or_404(hata_id)
    form = DuzelticiFaaliyetForm()

    form.sorumlu_id.choices = [(u.id, u.ad_soyad) for u in Kullanici.query.filter_by(aktif=True).all()]
    form.ekip_lideri_id.choices = [(0, '--- Seçiniz ---')] + [(u.id, u.ad_soyad) for u in Kullanici.query.filter_by(aktif=True).all()]

    if form.validate_on_submit():
        faaliyet = DuzelticiFaaliyet(
            capa_no=form.capa_no.data,
            hata_kaydi_id=hata_id,
            ekip_lideri_id=form.ekip_lideri_id.data if form.ekip_lideri_id.data != 0 else None,
            kok_neden=form.kok_neden.data,
            neden_kategorisi=form.neden_kategorisi.data,
            gecici_onlem=form.gecici_onlem.data,
            faaliyet=form.faaliyet.data,
            sorumlu_id=form.sorumlu_id.data,
            hedef_tarih=form.hedef_tarih.data,
            durum='acik'
        )
        db.session.add(faaliyet)
        db.session.commit()
        flash('Düzeltici faaliyet başarıyla başlatıldı.', 'success')
        return redirect(url_for('kalite.faaliyetler'))

    return render_template('kalite/faaliyet_form.html', form=form, hata=hata)


@kalite_bp.route('/faaliyet-guncelle/<int:faaliyet_id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('kalite')
@log_action('Düzeltici Faaliyet Güncelleme')
def faaliyet_guncelle(faaliyet_id):
    """Düzeltici faaliyet durumunu günceller."""
    faaliyet = DuzelticiFaaliyet.query.get_or_404(faaliyet_id)
    yeni_durum = request.form.get('durum')

    if yeni_durum in ('acik', 'devam', 'dogrulama', 'kapandi', 'iptal'):
        faaliyet.durum = yeni_durum
        if yeni_durum == 'kapandi':
            faaliyet.tamamlanma_tarihi = datetime.now(timezone.utc).date()
            faaliyet.dogrulayan_id = current_user.id
        if yeni_durum == 'dogrulama':
            faaliyet.dogrulama_notu = request.form.get('dogrulama_notu', '')
        db.session.commit()
        flash('Faaliyet durumu güncellendi.', 'success')

    return redirect(url_for('kalite.faaliyetler'))
