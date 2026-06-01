"""FDYS — İSG (İş Sağlığı ve Güvenliği) Modülü Rotaları (Faz 4 — Kurumsal)"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi, SaglikMuayenesi, IsgDokumani
from app.models.personel import Calisan
from app.forms.kalite_isg_enerji import IsKazasiForm, RiskDegerlendirmeForm, IsgEgitimiForm, SaglikMuayenesiForm, IsgDokumaniForm
from app.utils.decorators import modul_erisim_gerekli, log_action
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

isg_bp = Blueprint('isg', __name__, url_prefix='/isg')


@isg_bp.route('/')
@login_required
@modul_erisim_gerekli('isg')
def index():
    """İSG ana sayfa — Olaylar, Riskler, Eğitimler ve İstatistikler."""
    page_olay = request.args.get('page_olay', 1, type=int)
    page_risk = request.args.get('page_risk', 1, type=int)
    olaylar_pagination = IsKazasi.query.order_by(IsKazasi.tarih.desc()).paginate(
        page=page_olay, per_page=15, error_out=False)
    riskler_pagination = RiskDegerlendirme.query.order_by(RiskDegerlendirme.olusturma_tarihi.desc()).paginate(
        page=page_risk, per_page=15, error_out=False)

    # İstatistikler
    toplam_olay = olaylar_pagination.total
    is_kazasi_sayisi = IsKazasi.query.filter_by(ramak_kala=False).count()
    ramak_kala_sayisi = IsKazasi.query.filter_by(ramak_kala=True).count()
    toplam_kayip_gun = db.session.query(func.sum(IsKazasi.kayip_gun)).scalar() or 0

    # Risk istatistikleri
    kritik_risk = RiskDegerlendirme.query.filter_by(risk_seviyesi='kritik').count()
    yuksek_risk = RiskDegerlendirme.query.filter_by(risk_seviyesi='yuksek').count()
    orta_risk = RiskDegerlendirme.query.filter_by(risk_seviyesi='orta').count()
    dusuk_risk = RiskDegerlendirme.query.filter_by(risk_seviyesi='dusuk').count()
    acik_riskler = RiskDegerlendirme.query.filter(
        RiskDegerlendirme.durum.in_(['acik', 'devam'])
    ).count()

    # Eğitim istatistikleri
    suresi_dolan_egitimler = IsgEgitimi.query.filter(
        IsgEgitimi.gecerlilik_bitis < datetime.now(timezone.utc).date(),
        IsgEgitimi.durum == 'gecerli'
    ).count()

    # Şiddet dağılımı (pie chart)
    siddet_dagilimi = db.session.query(
        IsKazasi.siddet, func.count(IsKazasi.id)
    ).group_by(IsKazasi.siddet).all()

    siddet_labels = [d[0] for d in siddet_dagilimi]
    siddet_values = [d[1] for d in siddet_dagilimi]

    # Aylık olay trendi (son 12 ay)
    on_iki_ay_once = datetime.now(timezone.utc) - timedelta(days=365)
    aylik_olay = db.session.query(
        func.strftime('%Y-%m', IsKazasi.tarih),
        func.count(IsKazasi.id)
    ).filter(IsKazasi.tarih >= on_iki_ay_once)\
     .group_by(func.strftime('%Y-%m', IsKazasi.tarih))\
     .order_by(func.strftime('%Y-%m', IsKazasi.tarih)).all()

    trend_labels = [d[0] for d in aylik_olay]
    trend_values = [d[1] for d in aylik_olay]

    return render_template('isg/index.html',
                           olaylar=olaylar_pagination.items,
                           olaylar_pagination=olaylar_pagination,
                           riskler=riskler_pagination.items,
                           riskler_pagination=riskler_pagination,
                           stats={
                               'toplam_olay': toplam_olay,
                               'is_kazasi': is_kazasi_sayisi,
                               'ramak_kala': ramak_kala_sayisi,
                               'kayip_gun': toplam_kayip_gun,
                               'kritik_risk': kritik_risk,
                               'yuksek_risk': yuksek_risk,
                               'orta_risk': orta_risk,
                               'dusuk_risk': dusuk_risk,
                               'acik_riskler': acik_riskler,
                               'suresi_dolan_egitim': suresi_dolan_egitimler,
                           },
                           siddet_chart={'labels': siddet_labels, 'values': siddet_values},
                           trend_chart={'labels': trend_labels, 'values': trend_values})


@isg_bp.route('/olay-bildir', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('isg')
@log_action('İSG Olay Bildirimi')
def olay_bildir():
    form = IsKazasiForm()
    form.calisan_id.choices = [(0, '--- Seçiniz ---')] + \
        [(c.id, c.ad_soyad) for c in Calisan.query.filter_by(aktif=True).all()]

    if form.validate_on_submit():
        ramak_kala = form.olay_turu.data == 'ramak_kala'

        olay = IsKazasi(
            olay_no=form.olay_no.data,
            calisan_id=form.calisan_id.data,
            tarih=datetime.combine(form.tarih.data, datetime.min.time()),
            vardiya=form.vardiya.data,
            yer=form.yer.data,
            yaralanma_tipi=form.yaralanma_tipi.data,
            uzuv=form.uzuv.data,
            siddet=form.siddet.data,
            kaza_sekli=form.kaza_sekli.data,
            kok_neden=form.kok_neden.data,
            aciklama=form.aciklama.data,
            duzeltici_faaliyet=form.duzeltici_faaliyet.data,
            kayip_gun=form.kayip_gun.data or 0,
            ramak_kala=ramak_kala,
            bildiren_id=current_user.id
        )
        db.session.add(olay)
        db.session.commit()

        # Kritik Bildirim (İş Kazası ise)
        if not ramak_kala:
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici
            yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik="ACİL: İş Kazası Bildirimi!",
                    mesaj=f"{olay.calisan.ad_soyad} isimli çalışan {olay.yer} bölgesinde kaza geçirmiştir!",
                    seviye="kritik",
                    modul="isg",
                    url=url_for('isg.index')
                )

        flash('Olay bildirimi kaydedildi.', 'warning')
        return redirect(url_for('isg.index'))

    return render_template('isg/olay_form.html', form=form)


@isg_bp.route('/risk-ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('isg')
@log_action('Risk Değerlendirme Kaydı')
def risk_ekle():
    form = RiskDegerlendirmeForm()
    if form.validate_on_submit():
        risk = RiskDegerlendirme(
            bolum=form.bolum.data,
            faaliyet=form.faaliyet.data,
            tehlike=form.tehlike.data,
            risk=form.risk.data,
            olasilik=int(form.olasilik.data),
            siddet=int(form.siddet.data),
            mevcut_onlem=form.mevcut_onlem.data,
            ek_onlem=form.ek_onlem.data,
            sorumlu=form.sorumlu.data,
            hedef_tarih=form.hedef_tarih.data
        )
        # Risk Puanı hesapla
        risk.hesapla_risk()

        db.session.add(risk)
        db.session.commit()
        flash('Risk değerlendirmesi kaydedildi.', 'success')
        return redirect(url_for('isg.index'))

    return render_template('isg/risk_form.html', form=form)


@isg_bp.route('/risk-guncelle/<int:risk_id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('isg')
@log_action('Risk Durumu Güncelleme')
def risk_guncelle(risk_id):
    """Risk durumunu günceller."""
    risk = RiskDegerlendirme.query.get_or_404(risk_id)
    yeni_durum = request.form.get('durum')

    if yeni_durum in ('acik', 'devam', 'kapandi'):
        risk.durum = yeni_durum
        db.session.commit()
        flash('Risk durumu güncellendi.', 'success')

    return redirect(url_for('isg.index'))


@isg_bp.route('/egitimler')
@login_required
@modul_erisim_gerekli('isg')
def egitimler():
    """İSG eğitimleri listesi."""
    page = request.args.get('page', 1, type=int)
    egitim_pagination = IsgEgitimi.query.order_by(IsgEgitimi.egitim_tarihi.desc()).paginate(
        page=page, per_page=20, error_out=False)
    egitim_listesi = egitim_pagination.items

    # Süresi dolmuş eğitimleri otomatik güncelle
    bugun = datetime.now(timezone.utc).date()
    for e in egitim_listesi:
        if e.gecerlilik_bitis and e.gecerlilik_bitis < bugun and e.durum == 'gecerli':
            e.durum = 'suresi_doldu'
    db.session.commit()

    # İstatistikler
    gecerli = sum(1 for e in egitim_listesi if e.durum == 'gecerli')
    suresi_doldu = sum(1 for e in egitim_listesi if e.durum == 'suresi_doldu')

    return render_template('isg/egitimler.html',
                           egitimler=egitim_listesi,
                           pagination=egitim_pagination,
                           stats={'gecerli': gecerli, 'suresi_doldu': suresi_doldu})


@isg_bp.route('/egitim-ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('isg')
@log_action('İSG Eğitim Kaydı')
def egitim_ekle():
    """Yeni İSG eğitimi kaydı ekler."""
    form = IsgEgitimiForm()
    form.calisan_id.choices = [(c.id, c.ad_soyad) for c in Calisan.query.filter_by(aktif=True).all()]

    if form.validate_on_submit():
        egitim = IsgEgitimi(
            calisan_id=form.calisan_id.data,
            egitim_kategorisi=form.egitim_kategorisi.data,
            egitim_adi=form.egitim_adi.data,
            egitim_suresi=form.egitim_suresi.data,
            egitim_tarihi=form.egitim_tarihi.data,
            gecerlilik_bitis=form.gecerlilik_bitis.data,
            sertifika_no=form.sertifika_no.data,
            egitmen=form.egitmen.data,
            durum='gecerli'
        )
        db.session.add(egitim)
        db.session.commit()
        flash('Eğitim kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('isg.egitimler'))

    return render_template('isg/egitim_form.html', form=form)


@isg_bp.route('/saglik-muayeneleri')
@login_required
@modul_erisim_gerekli('isg')
def saglik_muayeneleri():
    """Çalışan periyodik sağlık muayenesi listesi."""
    page = request.args.get('page', 1, type=int)
    muayene_pagination = SaglikMuayenesi.query.order_by(SaglikMuayenesi.muayene_tarihi.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('isg/muayeneler.html', 
                           muayeneler=muayene_pagination.items,
                           pagination=muayene_pagination)


@isg_bp.route('/saglik-muayene/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('isg', 'yazma')
@log_action('Sağlık Muayenesi Kaydı')
def muayene_ekle():
    """Yeni sağlık muayenesi kaydı."""
    form = SaglikMuayenesiForm()
    form.calisan_id.choices = [(c.id, c.ad_soyad) for c in Calisan.query.filter_by(aktif=True).all()]
    
    if form.validate_on_submit():
        muayene = SaglikMuayenesi(
            calisan_id=form.calisan_id.data,
            muayene_turu=form.muayene_turu.data,
            muayene_tarihi=form.muayene_tarihi.data,
            sonraki_muayene_tarihi=form.sonraki_muayene_tarihi.data,
            hastane_adi=form.hastane_adi.data,
            doktor_adi=form.doktor_adi.data,
            sonuc=form.sonuc.data,
            kisitlamalar=form.kisitlamalar.data,
            hatirlatma_gun=form.hatirlatma_gun.data,
            notlar=form.notlar.data
        )
        db.session.add(muayene)
        db.session.commit()
        flash('Sağlık muayenesi başarıyla kaydedildi.', 'success')
        return redirect(url_for('isg.saglik_muayeneleri'))
        
    return render_template('isg/muayene_form.html', form=form)


@isg_bp.route('/dokumanlar')
@login_required
@modul_erisim_gerekli('isg')
def dokumanlar():
    """İSG Doküman arşivi."""
    page = request.args.get('page', 1, type=int)
    dokuman_pagination = IsgDokumani.query.order_by(IsgDokumani.olusturma_tarihi.desc()).paginate(
        page=page, per_page=20, error_out=False)
        
    return render_template('isg/dokumanlar.html', 
                           dokumanlar=dokuman_pagination.items,
                           pagination=dokuman_pagination)


@isg_bp.route('/dokuman/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('isg', 'yazma')
@log_action('İSG Dokümanı Ekleme')
def dokuman_ekle():
    """Yeni İSG dokümanı ekleme."""
    form = IsgDokumaniForm()
    
    if form.validate_on_submit():
        dokuman = IsgDokumani(
            baslik=form.baslik.data,
            kategori=form.kategori.data,
            aciklama=form.aciklama.data,
            ilgili_bolum=form.ilgili_bolum.data,
            gecerlilik_tarihi=form.gecerlilik_tarihi.data,
            versiyon=form.versiyon.data,
            onay_durumu=form.onay_durumu.data or 'taslak',
            sorumlu_id=current_user.id
        )
        db.session.add(dokuman)
        db.session.commit()
        flash('İSG dokümanı başarıyla kaydedildi.', 'success')
        return redirect(url_for('isg.dokumanlar'))
        
    return render_template('isg/dokuman_form.html', form=form)


@isg_bp.route('/dokuman/onayla/<int:dokuman_id>', methods=['POST'])
@login_required
@modul_erisim_gerekli('isg', 'yazma')
@log_action('İSG Doküman Onayı')
def dokuman_onayla(dokuman_id):
    """Doküman onay durumu güncelleme."""
    dokuman = IsgDokumani.query.get_or_404(dokuman_id)
    yeni_durum = request.form.get('durum')
    
    if yeni_durum in dict(IsgDokumani.ONAY_DURUMLARI).keys():
        dokuman.onay_durumu = yeni_durum
        if yeni_durum == 'onaylandi':
            dokuman.onaylayan_id = current_user.id
            dokuman.onay_tarihi = datetime.now(timezone.utc)
        db.session.commit()
        flash('Doküman durumu güncellendi.', 'success')
        
    return redirect(url_for('isg.dokumanlar'))


@isg_bp.route('/hatirlatmalar')
@login_required
@modul_erisim_gerekli('isg')
def hatirlatmalar():
    """Tüm İSG hatırlatmaları dashboard'u."""
    from app.services.isg_hatirlatici import tum_hatirlatmalar
    
    hatirlatma_verisi = tum_hatirlatmalar()
    return render_template('isg/hatirlatmalar.html', veriler=hatirlatma_verisi)
