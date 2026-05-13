"""FDYS — Makine ve Üretim Takip Rotaları (Faz 3 — Profesyonel)"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
from app.models.personel import Calisan
from app.forms.makine import (MakineForm, UretimGirisForm, ArizaBildirimForm,
                               ArizaCozumForm, DurusKaydiForm, BakimKaydiForm)
from app.utils.decorators import modul_erisim_gerekli, log_action
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc

makine_bp = Blueprint('makine', __name__, url_prefix='/makine')


@makine_bp.route('/')
@login_required
@modul_erisim_gerekli('makine')
def index():
    """Makine listesi ve genel durum dashboard."""
    page = request.args.get('page', 1, type=int)
    makineler_pagination = Makine.query.filter_by(aktif=True).order_by(Makine.kod).paginate(
        page=page, per_page=15, error_out=False)
    makineler = makineler_pagination.items

    # Genel istatistikler
    toplam_makine = makineler_pagination.total
    arizali_sayisi = Makine.query.filter_by(durum='arizali', aktif=True).count()
    bakimdaki_sayisi = Makine.query.filter_by(durum='bakimda', aktif=True).count()
    calisir_sayisi = toplam_makine - arizali_sayisi - bakimdaki_sayisi

    # Ortalama OEE (Son 7 gün)
    yedi_gun_once = datetime.now(timezone.utc).date() - timedelta(days=7)
    ortalama_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde))\
        .filter(UretimVerisi.tarih >= yedi_gun_once).scalar() or 0

    # Bugünkü üretim toplamı
    bugun = datetime.now(timezone.utc).date()
    bugunun_uretimi = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
        .filter(UretimVerisi.tarih == bugun).scalar() or 0

    # Açık arıza sayısı
    acik_ariza_sayisi = ArizaKaydi.query.filter_by(durum='acik').count()

    # Bakımı geciken makineler (tüm aktif makineler üzerinden)
    tum_makineler = Makine.query.filter_by(aktif=True).all()
    bakim_geciken = [m for m in tum_makineler if m.bakim_gecikti_mi]

    return render_template('makine/index.html',
                           makineler=makineler,
                           pagination=makineler_pagination,
                           stats={
                               'toplam': toplam_makine,
                               'calisir': calisir_sayisi,
                               'arizali': arizali_sayisi,
                               'bakimda': bakimdaki_sayisi,
                               'ort_oee': round(float(ortalama_oee), 1),
                               'bugun_uretim': bugunun_uretimi,
                               'acik_ariza': acik_ariza_sayisi,
                               'bakim_geciken': len(bakim_geciken)
                           })


@makine_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Makine Ekleme')
def ekle():
    form = MakineForm()
    if form.validate_on_submit():
        yeni_makine = Makine(
            ad=form.ad.data,
            kod=form.kod.data,
            model=form.model.data,
            marka=form.marka.data,
            teorik_kapasite=form.teorik_kapasite.data,
            hedef_oee=form.hedef_oee.data,
            satin_alma_tarihi=form.satin_alma_tarihi.data,
            garantisi_bitis=form.garantisi_bitis.data,
            periyodik_bakim_gun=form.periyodik_bakim_gun.data,
            lokasyon=form.lokasyon.data,
            durum=form.durum.data
        )

        # Auto-assign factory map position
        from app.routes.fabrika_harita import otomatik_konum_ata
        otomatik_konum_ata(yeni_makine)

        db.session.add(yeni_makine)
        db.session.commit()
        flash(f'{yeni_makine.ad} başarıyla eklendi.', 'success')
        return redirect(url_for('makine.index'))

    return render_template('makine/form.html', form=form, title="Yeni Makine Ekle")


@makine_bp.route('/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Makine Düzenleme')
def duzenle(id):
    """Mevcut makine bilgilerini düzenle."""
    makine = Makine.query.get_or_404(id)
    form = MakineForm(obj=makine)

    if form.validate_on_submit():
        makine.ad = form.ad.data
        makine.kod = form.kod.data
        makine.model = form.model.data
        makine.marka = form.marka.data
        makine.teorik_kapasite = form.teorik_kapasite.data
        makine.hedef_oee = form.hedef_oee.data
        makine.satin_alma_tarihi = form.satin_alma_tarihi.data
        makine.garantisi_bitis = form.garantisi_bitis.data
        makine.periyodik_bakim_gun = form.periyodik_bakim_gun.data
        makine.lokasyon = form.lokasyon.data
        makine.durum = form.durum.data
        db.session.commit()
        flash(f'{makine.ad} bilgileri güncellendi.', 'success')
        return redirect(url_for('makine.detay', id=id))

    return render_template('makine/form.html', form=form, title=f"{makine.ad} — Düzenle", makine=makine)


@makine_bp.route('/detay/<int:id>')
@login_required
@modul_erisim_gerekli('makine')
def detay(id):
    makine = Makine.query.get_or_404(id)
    son_uretimler = makine.uretim_verileri.order_by(UretimVerisi.tarih.desc()).limit(15).all()
    acik_arizalar = makine.ariza_kayitlari.filter_by(durum='acik').all()
    son_bakimlar = makine.bakim_kayitlari.order_by(BakimKaydi.tarih.desc()).limit(5).all()
    son_duruslar = makine.durus_kayitlari.order_by(DurusKaydi.baslangic.desc()).limit(10).all()

    # OEE Verileri (Son 30 gün — Grafik için)
    oee_data = db.session.query(UretimVerisi.tarih, UretimVerisi.oee_yuzde,
                                 UretimVerisi.kullanilabilirlik,
                                 UretimVerisi.performans,
                                 UretimVerisi.kalite)\
        .filter(UretimVerisi.makine_id == id)\
        .order_by(UretimVerisi.tarih.asc())\
        .limit(30).all()

    labels = [d[0].strftime('%d.%m') for d in oee_data]
    oee_values = [float(d[1]) if d[1] else 0 for d in oee_data]
    k_values = [float(d[2]) if d[2] else 0 for d in oee_data]
    p_values = [float(d[3]) if d[3] else 0 for d in oee_data]
    q_values = [float(d[4]) if d[4] else 0 for d in oee_data]

    # Ortalama OEE hesapla
    ort_oee = round(sum(oee_values) / len(oee_values), 1) if oee_values else 0

    # Duruş kategorileri dağılımı (Pie chart)
    durus_dagilimi = db.session.query(DurusKaydi.kategori, func.sum(DurusKaydi.sure_dk))\
        .filter(DurusKaydi.makine_id == id)\
        .group_by(DurusKaydi.kategori).all()

    durus_labels = [d[0] for d in durus_dagilimi]
    durus_values = [int(d[1]) if d[1] else 0 for d in durus_dagilimi]

    # Toplam arıza sayısı
    toplam_ariza = makine.ariza_kayitlari.count()
    kapanan_ariza = makine.ariza_kayitlari.filter_by(durum='kapali').count()

    # Üretim toplamları (Son 30 gün)
    otuz_gun_once = datetime.now(timezone.utc).date() - timedelta(days=30)
    aylik_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
        .filter(UretimVerisi.makine_id == id, UretimVerisi.tarih >= otuz_gun_once).scalar() or 0
    aylik_hata = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
        .filter(UretimVerisi.makine_id == id, UretimVerisi.tarih >= otuz_gun_once).scalar() or 0

    # ── AI Tahminleme Verileri ──
    ai_bakim = None
    ai_oee = None
    try:
        from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
        ai_bakim = kestirimci_bakim_servisi.makine_tahmini(id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"AI bakım tahmini yüklenemedi: {e}")
    try:
        from app.services.ai.oee_tahmin import oee_tahmin_servisi
        ai_oee = oee_tahmin_servisi.makine_tahmini(id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"AI OEE tahmini yüklenemedi: {e}")

    return render_template('makine/detay.html',
                           makine=makine,
                           son_uretimler=son_uretimler,
                           acik_arizalar=acik_arizalar,
                           son_bakimlar=son_bakimlar,
                           son_duruslar=son_duruslar,
                           oee_chart={
                               'labels': labels,
                               'oee': oee_values,
                               'kullanilabilirlik': k_values,
                               'performans': p_values,
                               'kalite': q_values,
                           },
                           ort_oee=ort_oee,
                           durus_chart={'labels': durus_labels, 'values': durus_values},
                           toplam_ariza=toplam_ariza,
                           kapanan_ariza=kapanan_ariza,
                           aylik_uretim=aylik_uretim,
                           aylik_hata=aylik_hata,
                           ai_bakim=ai_bakim,
                           ai_oee=ai_oee)


@makine_bp.route('/uretim-girisi/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Üretim Verisi Girişi')
def uretim_girisi(id):
    makine = Makine.query.get_or_404(id)
    form = UretimGirisForm()

    # Operatör listesini doldur
    form.calisan_id.choices = [(c.id, c.ad_soyad) for c in Calisan.query.filter_by(aktif=True).all()]

    if form.validate_on_submit():
        uretim = UretimVerisi(
            makine_id=id,
            calisan_id=form.calisan_id.data,
            vardiya=form.vardiya.data,
            tarih=form.tarih.data,
            planlanan_sure_dk=form.planlanan_sure_dk.data,
            gercek_calisma_dk=form.gercek_calisma_dk.data,
            gercek_uretim=form.gercek_uretim.data,
            hatali_uretim=form.hatali_uretim.data,
            notlar=form.notlar.data
        )
        # OEE Hesapla
        uretim.hesapla_oee(makine.teorik_kapasite)

        db.session.add(uretim)
        db.session.commit()

        # OEE düşükse bildirim
        if uretim.oee_yuzde and float(uretim.oee_yuzde) < float(makine.hedef_oee) * 0.9:
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici
            yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik="OEE Düşük Uyarısı",
                    mesaj=f"{makine.ad} — OEE: %{uretim.oee_yuzde} (Hedef: %{makine.hedef_oee})",
                    seviye="uyari",
                    modul="makine",
                    url=url_for('makine.detay', id=id)
                )

        flash(f'Üretim verisi kaydedildi. OEE: %{uretim.oee_yuzde}', 'success')
        return redirect(url_for('makine.detay', id=id))

    return render_template('makine/uretim_form.html', form=form, makine=makine)


@makine_bp.route('/ariza-bildir/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Arıza Bildirimi')
def ariza_bildir(id):
    makine = Makine.query.get_or_404(id)
    form = ArizaBildirimForm()

    if form.validate_on_submit():
        ariza = ArizaKaydi(
            makine_id=id,
            bildiren_id=current_user.id,
            ariza_turu=form.ariza_turu.data,
            oncelik=form.oncelik.data,
            aciklama=form.aciklama.data,
            durum='acik'
        )
        makine.durum = 'arizali'
        db.session.add(ariza)
        db.session.commit()

        # Bildirim Oluştur (Merkezi motor üzerinden)
        from app.services.bildirim_motoru import bildirim_motoru
        from app.models.kullanici import Kullanici
        yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
        for y in yoneticiler:
            bildirim_motoru.bildirim_olustur(
                kullanici_id=y.id,
                baslik="Yeni Arıza Bildirimi",
                mesaj=f"{makine.ad} makinesinde {ariza.ariza_turu} arızası bildirildi.",
                seviye="kritik" if ariza.oncelik == 'kritik' else "uyari",
                modul="makine",
                url=url_for('makine.detay', id=id)
            )

        flash('Arıza bildirimi yapıldı. Teknik ekip bilgilendirildi.', 'warning')

        # Otomatik İş Emri Oluştur (Kategori 6 — İş Akışı Otomasyonu)
        try:
            from app.services.otomasyon_motoru import otomasyon_motoru
            otomasyon_motoru.ariza_is_emri_olustur(ariza)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Otomasyon iş emri tetikleme hatası: {e}")

        return redirect(url_for('makine.detay', id=id))

    return render_template('makine/ariza_form.html', form=form, makine=makine)


@makine_bp.route('/ariza-coz/<int:ariza_id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Arıza Çözümü')
def ariza_coz(ariza_id):
    ariza = ArizaKaydi.query.get_or_404(ariza_id)
    form = ArizaCozumForm()

    if form.validate_on_submit():
        ariza.cozum = form.cozum.data
        ariza.durum = form.durum.data
        ariza.bitis_zamani = datetime.now(timezone.utc)
        ariza.atanan_teknisyen_id = current_user.id

        # Müdahale süresi hesapla
        b_zamani = ariza.baslangic_zamani.replace(tzinfo=timezone.utc) if ariza.baslangic_zamani.tzinfo is None else ariza.baslangic_zamani
        diff = ariza.bitis_zamani - b_zamani
        ariza.mudahale_suresi_dk = int(diff.total_seconds() / 60)

        if ariza.durum == 'kapali':
            # Makineyi tekrar aktif yap (başka açık arıza yoksa)
            diger_arizalar = ArizaKaydi.query.filter(
                ArizaKaydi.makine_id == ariza.makine_id,
                ArizaKaydi.durum == 'acik',
                ArizaKaydi.id != ariza.id
            ).count()
            if diger_arizalar == 0:
                ariza.makine.durum = 'aktif'

        db.session.commit()
        flash('Arıza kaydı güncellendi.', 'success')
        return redirect(url_for('makine.detay', id=ariza.makine_id))

    return render_template('makine/ariza_cozum_form.html', form=form, ariza=ariza)


@makine_bp.route('/bakim-kaydi/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Bakım Kaydı')
def bakim_kaydi(id):
    """Makineye yeni bakım kaydı ekler."""
    makine = Makine.query.get_or_404(id)
    form = BakimKaydiForm()

    if form.validate_on_submit():
        bakim = BakimKaydi(
            makine_id=id,
            bakim_turu=form.bakim_turu.data,
            yapilan_islem=form.yapilan_islem.data,
            teknisyen_id=current_user.id,
            tarih=form.tarih.data,
            sure_dk=form.sure_dk.data,
            maliyet=form.maliyet.data,
            notlar=form.notlar.data
        )
        # Makine bilgilerini güncelle
        makine.son_bakim_tarihi = form.tarih.data
        bakim.sonraki_bakim_tarihi = form.tarih.data + timedelta(days=makine.periyodik_bakim_gun)

        # Bakımdaysa aktife al
        if makine.durum == 'bakimda':
            makine.durum = 'aktif'

        db.session.add(bakim)
        db.session.commit()
        flash('Bakım kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('makine.detay', id=id))

    return render_template('makine/bakim_form.html', form=form, makine=makine)


@makine_bp.route('/durus-kaydi/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine')
@log_action('Duruş Kaydı')
def durus_kaydi(id):
    """Makineye duruş kaydı ekler (Altı Büyük Kayıp)."""
    makine = Makine.query.get_or_404(id)
    form = DurusKaydiForm()

    if form.validate_on_submit():
        durus = DurusKaydi(
            makine_id=id,
            baslangic=form.baslangic.data,
            bitis=form.bitis.data,
            neden=form.neden.data,
            kategori=form.kategori.data,
            aciklama=getattr(form, 'aciklama', None) and form.aciklama.data
        )
        durus.hesapla_sure()
        db.session.add(durus)
        db.session.commit()
        flash('Duruş kaydı başarıyla eklendi.', 'success')
        return redirect(url_for('makine.detay', id=id))

    return render_template('makine/durus_form.html', form=form, makine=makine)


@makine_bp.route('/arizalar')
@login_required
@modul_erisim_gerekli('makine')
def arizalar():
    """Arıza listesi için İş Emri modülüne yönlendirme."""
    return redirect(url_for('is_emri.index', kategori='makine'))

