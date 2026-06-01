"""
FDYS — İK (İnsan Kaynakları) Rotaları
Faz 1 — Tam Genişletme

20+ endpoint: Dashboard, Personel Kartı (360°), Savunma/Tutanak,
Fazla Mesai, Sertifika, Maaş Skalası, Zimmet, Giriş/Çıkış Evrak,
Raporlar, İzin Bakiye.
"""

import logging
from datetime import datetime, date, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, func, extract

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, yazma_izni_gerekli, log_action
from app.models.personel import Calisan, IzinTalebi
from app.models.ik import (
    SavunmaTutanak, FazlaMesai, SertifikaTakip,
    MaasSkalasi, ZimmetKaydi, GirisCikisEvrak
)
from app.forms.ik import (
    SavunmaTutanakForm, FazlaMesaiForm, SertifikaForm,
    MaasSkalasıForm, ZimmetForm, GirisCikisEvrakForm
)
from app.services.ik_servisi import (
    izin_bakiye_hesapla, kidem_hesapla, fazla_mesai_ozeti,
    sertifika_hatirlatma_kontrol, personel_360_rapor
)

logger = logging.getLogger(__name__)

ik_bp = Blueprint('ik', __name__, url_prefix='/ik')


# ══════════════════════════════════════════════════════════════════
# İK ANA DASHBOARD
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/')
@login_required
@modul_erisim_gerekli('ik')
def index():
    """İK ana panel — özet dashboard."""
    bugun = date.today()

    # KPI verileri
    toplam_personel = Calisan.query.filter_by(aktif=True).count()
    bekleyen_izin = IzinTalebi.query.filter_by(durum='bekliyor').count()

    # Süresi dolan sertifikalar
    suresi_dolan = sertifika_hatirlatma_kontrol()
    suresi_dolan_sayisi = len(suresi_dolan)

    # Bekleyen fazla mesai onayları
    bekleyen_mesai = FazlaMesai.query.filter_by(
        onay_durumu='bekliyor', aktif=True
    ).count()

    # Bu ayki toplam fazla mesai saati
    bu_ay_mesai = db.session.query(func.sum(FazlaMesai.toplam_saat)).filter(
        FazlaMesai.aktif == True,
        FazlaMesai.onay_durumu == 'onaylandi',
        extract('month', FazlaMesai.tarih) == bugun.month,
        extract('year', FazlaMesai.tarih) == bugun.year,
    ).scalar() or 0

    # Aktif zimmetler
    aktif_zimmet = ZimmetKaydi.query.filter_by(
        aktif=True, durum='teslim_edildi'
    ).filter(ZimmetKaydi.iade_tarihi.is_(None)).count()

    # Açık savunma/tutanaklar
    acik_savunma = SavunmaTutanak.query.filter_by(
        aktif=True, durum='acik'
    ).count()

    # Son eklenen savunmalar
    son_savunmalar = SavunmaTutanak.query.filter_by(aktif=True).order_by(
        SavunmaTutanak.olusturma_tarihi.desc()
    ).limit(5).all()

    # Son fazla mesai kayıtları
    son_mesailer = FazlaMesai.query.filter_by(aktif=True).order_by(
        FazlaMesai.tarih.desc()
    ).limit(5).all()

    # Personel kartı dropdown'ı için çalışan listesi
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()

    return render_template('ik/index.html',
                           toplam_personel=toplam_personel,
                           bekleyen_izin=bekleyen_izin,
                           suresi_dolan_sayisi=suresi_dolan_sayisi,
                           suresi_dolan_sertifikalar=suresi_dolan[:5],
                           bekleyen_mesai=bekleyen_mesai,
                           bu_ay_mesai=bu_ay_mesai,
                           aktif_zimmet=aktif_zimmet,
                           acik_savunma=acik_savunma,
                           son_savunmalar=son_savunmalar,
                           son_mesailer=son_mesailer,
                           calisanlar=calisanlar)


# ══════════════════════════════════════════════════════════════════
# 360° PERSONEL KARTI
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/personel-karti/<int:id>')
@login_required
@modul_erisim_gerekli('ik')
def personel_karti(id):
    """360° personel kartı — tek sayfada tüm İK bilgileri."""
    rapor = personel_360_rapor(id)
    if not rapor:
        flash('Çalışan bulunamadı.', 'danger')
        return redirect(url_for('ik.index'))

    return render_template('ik/personel_karti.html', **rapor)


# ══════════════════════════════════════════════════════════════════
# SAVUNMA / TUTANAK
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/savunma-tutanak')
@login_required
@modul_erisim_gerekli('ik')
def savunma_liste():
    """Savunma/tutanak listesi — filtreleme: tür, çalışan, tarih."""
    page = request.args.get('page', 1, type=int)
    tur = request.args.get('tur', '')
    calisan_id = request.args.get('calisan_id', 0, type=int)
    durum = request.args.get('durum', '')

    query = SavunmaTutanak.query.filter_by(aktif=True)

    if tur:
        query = query.filter(SavunmaTutanak.tur == tur)
    if calisan_id:
        query = query.filter(SavunmaTutanak.calisan_id == calisan_id)
    if durum:
        query = query.filter(SavunmaTutanak.durum == durum)

    savunmalar = query.order_by(
        SavunmaTutanak.olusturma_tarihi.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()

    return render_template('ik/savunma_liste.html',
                           savunmalar=savunmalar,
                           calisanlar=calisanlar,
                           tur=tur, calisan_id=calisan_id, durum=durum)


@ik_bp.route('/savunma-tutanak/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Savunma/Tutanak Ekleme')
def savunma_ekle():
    """Yeni savunma/tutanak oluşturma."""
    form = SavunmaTutanakForm()
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    if form.validate_on_submit():
        # Tanık bilgilerini JSON olarak topla
        taniklar = []
        if form.tanik_ad_soyad.data:
            taniklar.append({
                'ad_soyad': form.tanik_ad_soyad.data,
                'sicil_no': form.tanik_sicil_no.data or '',
            })

        savunma = SavunmaTutanak(
            calisan_id=form.calisan_id.data,
            tur=form.tur.data,
            konu=form.konu.data,
            icerik=form.icerik.data,
            karar=form.karar.data,
            karar_tarihi=form.karar_tarihi.data,
            durum=form.durum.data,
            olusturan_id=current_user.id,
            taniklar=taniklar,
        )
        db.session.add(savunma)
        db.session.commit()

        flash('Savunma/Tutanak kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ik.savunma_detay', id=savunma.id))

    return render_template('ik/savunma_form.html', form=form, title='Yeni Savunma/Tutanak')


@ik_bp.route('/savunma-tutanak/<int:id>')
@login_required
@modul_erisim_gerekli('ik')
def savunma_detay(id):
    """Savunma/tutanak detay görüntüleme."""
    savunma = SavunmaTutanak.query.get_or_404(id)
    return render_template('ik/savunma_detay.html', savunma=savunma)


@ik_bp.route('/savunma-tutanak/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Savunma/Tutanak Düzenleme')
def savunma_duzenle(id):
    """Savunma/tutanak düzenleme."""
    savunma = SavunmaTutanak.query.get_or_404(id)
    form = SavunmaTutanakForm(obj=savunma)
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    if form.validate_on_submit():
        savunma.calisan_id = form.calisan_id.data
        savunma.tur = form.tur.data
        savunma.konu = form.konu.data
        savunma.icerik = form.icerik.data
        savunma.karar = form.karar.data
        savunma.karar_tarihi = form.karar_tarihi.data
        savunma.durum = form.durum.data

        if form.tanik_ad_soyad.data:
            taniklar = savunma.taniklar or []
            taniklar.append({
                'ad_soyad': form.tanik_ad_soyad.data,
                'sicil_no': form.tanik_sicil_no.data or '',
            })
            savunma.taniklar = taniklar

        db.session.commit()
        flash('Savunma/Tutanak kaydı güncellendi.', 'success')
        return redirect(url_for('ik.savunma_detay', id=savunma.id))

    return render_template('ik/savunma_form.html', form=form, savunma=savunma,
                           title='Savunma/Tutanak Düzenle')


# ══════════════════════════════════════════════════════════════════
# FAZLA MESAİ
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/fazla-mesai')
@login_required
@modul_erisim_gerekli('ik')
def fazla_mesai_liste():
    """Fazla mesai listesi — aylık özet, onay bekleyen."""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum', '')
    ay = request.args.get('ay', date.today().month, type=int)
    yil = request.args.get('yil', date.today().year, type=int)

    query = FazlaMesai.query.filter_by(aktif=True)

    if durum:
        query = query.filter(FazlaMesai.onay_durumu == durum)

    if ay and ay != 0:
        query = query.filter(extract('month', FazlaMesai.tarih) == ay)
    if yil and yil != 0:
        query = query.filter(extract('year', FazlaMesai.tarih) == yil)

    mesailer = query.order_by(FazlaMesai.tarih.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Aylık toplamlar
    toplam_saat_query = db.session.query(func.sum(FazlaMesai.toplam_saat)).filter(FazlaMesai.aktif == True)
    onaylanan_saat_query = db.session.query(func.sum(FazlaMesai.toplam_saat)).filter(
        FazlaMesai.aktif == True, FazlaMesai.onay_durumu == 'onaylandi'
    )

    if ay and ay != 0:
        toplam_saat_query = toplam_saat_query.filter(extract('month', FazlaMesai.tarih) == ay)
        onaylanan_saat_query = onaylanan_saat_query.filter(extract('month', FazlaMesai.tarih) == ay)
    if yil and yil != 0:
        toplam_saat_query = toplam_saat_query.filter(extract('year', FazlaMesai.tarih) == yil)
        onaylanan_saat_query = onaylanan_saat_query.filter(extract('year', FazlaMesai.tarih) == yil)

    toplam_saat = toplam_saat_query.scalar() or 0
    onaylanan_saat = onaylanan_saat_query.scalar() or 0

    return render_template('ik/fazla_mesai_liste.html',
                           mesailer=mesailer,
                           durum=durum, ay=ay, yil=yil,
                           toplam_saat=toplam_saat,
                           onaylanan_saat=onaylanan_saat)


@ik_bp.route('/fazla-mesai/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Fazla Mesai Ekleme')
def fazla_mesai_ekle():
    """Yeni fazla mesai kaydı."""
    form = FazlaMesaiForm()
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    if form.validate_on_submit():
        mesai = FazlaMesai(
            calisan_id=form.calisan_id.data,
            tarih=form.tarih.data,
            baslangic_saati=form.baslangic_saati.data,
            bitis_saati=form.bitis_saati.data,
            mesai_turu=form.mesai_turu.data,
            neden=form.neden.data,
            onay_durumu='bekliyor',
        )
        mesai.hesapla_toplam_saat()
        mesai.varsayilan_carpan_belirle()

        db.session.add(mesai)
        db.session.commit()

        flash(f'Fazla mesai kaydı oluşturuldu ({mesai.toplam_saat} saat).', 'success')
        return redirect(url_for('ik.fazla_mesai_liste'))

    return render_template('ik/fazla_mesai_form.html', form=form, title='Yeni Fazla Mesai')


@ik_bp.route('/fazla-mesai/onayla/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Fazla Mesai Onaylama')
def fazla_mesai_onayla(id):
    """Fazla mesai onaylama."""
    mesai = FazlaMesai.query.get_or_404(id)
    if mesai.onay_durumu != 'bekliyor':
        flash('Bu mesai kaydı zaten işlenmiş.', 'warning')
        return redirect(url_for('ik.fazla_mesai_liste'))

    mesai.onay_durumu = 'onaylandi'
    mesai.onaylayan_id = current_user.id
    mesai.onay_tarihi = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'{mesai.calisan.ad_soyad} için fazla mesai onaylandı.', 'success')
    return redirect(url_for('ik.fazla_mesai_liste'))


@ik_bp.route('/fazla-mesai/reddet/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Fazla Mesai Reddetme')
def fazla_mesai_reddet(id):
    """Fazla mesai reddetme."""
    mesai = FazlaMesai.query.get_or_404(id)
    if mesai.onay_durumu != 'bekliyor':
        flash('Bu mesai kaydı zaten işlenmiş.', 'warning')
        return redirect(url_for('ik.fazla_mesai_liste'))

    mesai.onay_durumu = 'reddedildi'
    mesai.onaylayan_id = current_user.id
    mesai.onay_tarihi = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'{mesai.calisan.ad_soyad} için fazla mesai reddedildi.', 'warning')
    return redirect(url_for('ik.fazla_mesai_liste'))


# ══════════════════════════════════════════════════════════════════
# SERTİFİKA TAKİP
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/sertifikalar')
@login_required
@modul_erisim_gerekli('ik')
def sertifika_liste():
    """Tüm sertifikalar — süresi dolanlar vurgulu."""
    page = request.args.get('page', 1, type=int)
    kategori = request.args.get('kategori', '')
    durum = request.args.get('durum', '')

    query = SertifikaTakip.query.filter_by(aktif=True)

    if kategori:
        query = query.filter(SertifikaTakip.kategori == kategori)
    if durum:
        if durum == 'suresi_doldu_yaklasan':
            from app.services.ik_servisi import sertifika_hatirlatma_kontrol
            suresi_dolanlar = sertifika_hatirlatma_kontrol()
            ids = [s['sertifika'].id for s in suresi_dolanlar]
            # Use `in_` filter. If the list is empty, `in_([])` evaluates to false, which is what we want.
            query = query.filter(SertifikaTakip.id.in_(ids))
        else:
            query = query.filter(SertifikaTakip.durum == durum)

    sertifikalar = query.order_by(
        SertifikaTakip.gecerlilik_bitis.asc().nullslast()
    ).paginate(page=page, per_page=15, error_out=False)

    return render_template('ik/sertifika_liste.html',
                           sertifikalar=sertifikalar,
                           kategori=kategori, durum=durum)


@ik_bp.route('/sertifika/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Sertifika Ekleme')
def sertifika_ekle():
    """Yeni sertifika kaydı."""
    form = SertifikaForm()
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    if form.validate_on_submit():
        sertifika = SertifikaTakip(
            calisan_id=form.calisan_id.data,
            sertifika_adi=form.sertifika_adi.data,
            veren_kurum=form.veren_kurum.data,
            sertifika_no=form.sertifika_no.data,
            kategori=form.kategori.data,
            verilis_tarihi=form.verilis_tarihi.data,
            gecerlilik_bitis=form.gecerlilik_bitis.data,
            hatirlatma_gun=form.hatirlatma_gun.data or 30,
            notlar=form.notlar.data,
            durum='gecerli',
        )
        db.session.add(sertifika)
        db.session.commit()

        flash('Sertifika kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ik.sertifika_liste'))

    return render_template('ik/sertifika_form.html', form=form, title='Yeni Sertifika')


@ik_bp.route('/sertifika/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Sertifika Düzenleme')
def sertifika_duzenle(id):
    """Sertifika düzenleme."""
    sertifika = SertifikaTakip.query.get_or_404(id)
    form = SertifikaForm(obj=sertifika)
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    if form.validate_on_submit():
        sertifika.calisan_id = form.calisan_id.data
        sertifika.sertifika_adi = form.sertifika_adi.data
        sertifika.veren_kurum = form.veren_kurum.data
        sertifika.sertifika_no = form.sertifika_no.data
        sertifika.kategori = form.kategori.data
        sertifika.verilis_tarihi = form.verilis_tarihi.data
        sertifika.gecerlilik_bitis = form.gecerlilik_bitis.data
        sertifika.hatirlatma_gun = form.hatirlatma_gun.data or 30
        sertifika.notlar = form.notlar.data

        db.session.commit()
        flash('Sertifika kaydı güncellendi.', 'success')
        return redirect(url_for('ik.sertifika_liste'))

    return render_template('ik/sertifika_form.html', form=form, sertifika=sertifika,
                           title='Sertifika Düzenle')


# ══════════════════════════════════════════════════════════════════
# MAAŞ SKALASI
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/maas-skalasi/<int:calisan_id>')
@login_required
@modul_erisim_gerekli('ik')
def maas_gecmisi(calisan_id):
    """Çalışan maaş geçmişi — grafik + tablo."""
    calisan = Calisan.query.get_or_404(calisan_id)
    maaslar = MaasSkalasi.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(MaasSkalasi.donem_baslangic.desc()).all()

    return render_template('ik/maas_gecmisi.html', calisan=calisan, maaslar=maaslar)


@ik_bp.route('/maas-skalasi/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Maaş Kaydı Ekleme')
def maas_ekle():
    """Yeni maaş kaydı."""
    form = MaasSkalasıForm()
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    calisan_id = request.args.get('calisan_id', 0, type=int)
    if calisan_id and request.method == 'GET':
        form.calisan_id.data = calisan_id

        # Önceki dönem maaşını otomatik yükle
        onceki = MaasSkalasi.query.filter_by(
            calisan_id=calisan_id, aktif=True, donem_bitis=None
        ).first()
        if onceki:
            form.brut_maas.data = onceki.brut_maas
            form.net_maas.data = onceki.net_maas

    if form.validate_on_submit():
        # Önceki dönemin bitiş tarihini güncelle
        onceki_donem = MaasSkalasi.query.filter_by(
            calisan_id=form.calisan_id.data, aktif=True, donem_bitis=None
        ).first()

        if onceki_donem:
            from datetime import timedelta
            onceki_donem.donem_bitis = form.donem_baslangic.data - timedelta(days=1)

            # Artış oranı hesapla
            if onceki_donem.brut_maas and onceki_donem.brut_maas > 0:
                artis = ((form.brut_maas.data - onceki_donem.brut_maas) / onceki_donem.brut_maas) * 100
            else:
                artis = None
        else:
            artis = None

        maas = MaasSkalasi(
            calisan_id=form.calisan_id.data,
            donem_baslangic=form.donem_baslangic.data,
            donem_bitis=form.donem_bitis.data,
            brut_maas=form.brut_maas.data,
            net_maas=form.net_maas.data,
            ek_odeme=form.ek_odeme.data or 0,
            ek_odeme_aciklama=form.ek_odeme_aciklama.data,
            artis_orani=form.artis_orani.data or artis,
            derece=form.derece.data,
            kademe=form.kademe.data,
            notlar=form.notlar.data,
        )
        db.session.add(maas)
        db.session.commit()

        flash('Maaş kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ik.maas_gecmisi', calisan_id=form.calisan_id.data))

    return render_template('ik/maas_form.html', form=form, title='Yeni Maaş Kaydı')


# ══════════════════════════════════════════════════════════════════
# ZİMMET
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/zimmet')
@login_required
@modul_erisim_gerekli('ik')
def zimmet_liste():
    """Zimmet listesi — iade edilmemişler vurgulu."""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum', '')
    kategori = request.args.get('kategori', '')

    query = ZimmetKaydi.query.filter_by(aktif=True)

    if durum:
        query = query.filter(ZimmetKaydi.durum == durum)
    if kategori:
        query = query.filter(ZimmetKaydi.kategori == kategori)

    zimmetler = query.order_by(
        ZimmetKaydi.teslim_tarihi.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    return render_template('ik/zimmet_liste.html',
                           zimmetler=zimmetler,
                           durum=durum, kategori=kategori)


@ik_bp.route('/zimmet/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Zimmet Ekleme')
def zimmet_ekle():
    """Yeni zimmet kaydı."""
    form = ZimmetForm()
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    if form.validate_on_submit():
        zimmet = ZimmetKaydi(
            calisan_id=form.calisan_id.data,
            demirbas_adi=form.demirbas_adi.data,
            demirbas_kodu=form.demirbas_kodu.data,
            seri_no=form.seri_no.data,
            kategori=form.kategori.data,
            teslim_tarihi=form.teslim_tarihi.data,
            deger=form.deger.data,
            notlar=form.notlar.data,
            teslim_alan_imza=form.teslim_alan_imza.data,
            durum='teslim_edildi',
        )
        db.session.add(zimmet)
        db.session.commit()

        flash('Zimmet kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ik.zimmet_liste'))

    return render_template('ik/zimmet_form.html', form=form, title='Yeni Zimmet')


@ik_bp.route('/zimmet/iade/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Zimmet İade')
def zimmet_iade(id):
    """Zimmet iade işlemi."""
    zimmet = ZimmetKaydi.query.get_or_404(id)
    zimmet.durum = 'iade_edildi'
    zimmet.iade_tarihi = date.today()
    db.session.commit()

    flash(f'{zimmet.demirbas_adi} iade edildi.', 'success')
    return redirect(url_for('ik.zimmet_liste'))


# ══════════════════════════════════════════════════════════════════
# GİRİŞ / ÇIKIŞ EVRAKLARI
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/giris-cikis/<int:calisan_id>')
@login_required
@modul_erisim_gerekli('ik')
def giris_cikis(calisan_id):
    """Çalışanın giriş/çıkış evrakları — tamamlanma yüzdesi ile."""
    calisan = Calisan.query.get_or_404(calisan_id)

    giris_evraklar = GirisCikisEvrak.query.filter_by(
        calisan_id=calisan_id, aktif=True, evrak_turu='ise_giris'
    ).all()
    cikis_evraklar = GirisCikisEvrak.query.filter_by(
        calisan_id=calisan_id, aktif=True, evrak_turu='isten_cikis'
    ).all()

    def tamamlanma_yuzdesi(evraklar):
        if not evraklar:
            return 0
        return round(sum(1 for e in evraklar if e.durum == 'tamamlandi') / len(evraklar) * 100)

    return render_template('ik/giris_cikis.html',
                           calisan=calisan,
                           giris_evraklar=giris_evraklar,
                           cikis_evraklar=cikis_evraklar,
                           giris_tamamlanma=tamamlanma_yuzdesi(giris_evraklar),
                           cikis_tamamlanma=tamamlanma_yuzdesi(cikis_evraklar))


@ik_bp.route('/giris-cikis/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Evrak Ekleme')
def giris_cikis_ekle():
    """Yeni evrak kaydı veya standart evrak listesi oluşturma."""
    form = GirisCikisEvrakForm()
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()
    form.calisan_id.choices = [(c.id, f'{c.sicil_no} — {c.ad_soyad}') for c in calisanlar]

    # Standart evrak oluşturma modu
    standart = request.args.get('standart', '')
    calisan_id = request.args.get('calisan_id', 0, type=int)

    if standart and calisan_id:
        evraklar = GirisCikisEvrak.standart_evrak_olustur(calisan_id, standart)
        for e in evraklar:
            db.session.add(e)
        db.session.commit()
        flash(f'{len(evraklar)} adet standart evrak kaydı oluşturuldu.', 'success')
        return redirect(url_for('ik.giris_cikis', calisan_id=calisan_id))

    if form.validate_on_submit():
        evrak = GirisCikisEvrak(
            calisan_id=form.calisan_id.data,
            evrak_turu=form.evrak_turu.data,
            evrak_adi=form.evrak_adi.data,
            durum=form.durum.data,
            notlar=form.notlar.data,
            sorumlu_id=current_user.id,
        )
        db.session.add(evrak)
        db.session.commit()

        flash('Evrak kaydı başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ik.giris_cikis', calisan_id=form.calisan_id.data))

    return render_template('ik/giris_cikis.html', form=form, title='Yeni Evrak')


@ik_bp.route('/giris-cikis/durum-guncelle/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('ik')
@log_action('Evrak Durum Güncelleme')
def evrak_durum_guncelle(id):
    """Evrak durumunu güncelleme (AJAX destekli)."""
    evrak = GirisCikisEvrak.query.get_or_404(id)
    yeni_durum = request.form.get('durum', '')

    if yeni_durum in ['bekliyor', 'tamamlandi', 'eksik']:
        evrak.durum = yeni_durum
        if yeni_durum == 'tamamlandi':
            evrak.tamamlama_tarihi = date.today()
        db.session.commit()
        flash('Evrak durumu güncellendi.', 'success')
    else:
        flash('Geçersiz durum.', 'danger')

    return redirect(url_for('ik.giris_cikis', calisan_id=evrak.calisan_id))


# ══════════════════════════════════════════════════════════════════
# RAPORLAR
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/raporlar')
@login_required
@modul_erisim_gerekli('ik')
def raporlar():
    """İK raporları dashboard'u — devamsızlık, fazla mesai, izin analizi."""
    bugun = date.today()
    yil = request.args.get('yil', bugun.year, type=int)

    # Departman bazlı çalışan sayıları
    departman_dagilimi_rows = db.session.query(
        Calisan.departman, func.count(Calisan.id)
    ).filter(Calisan.aktif == True).group_by(Calisan.departman).all()
    departman_dagilimi = [list(r) for r in departman_dagilimi_rows]

    # Aylık fazla mesai toplamları (grafik)
    aylik_mesai = []
    for ay in range(1, 13):
        toplam = db.session.query(func.sum(FazlaMesai.toplam_saat)).filter(
            FazlaMesai.aktif == True,
            FazlaMesai.onay_durumu == 'onaylandi',
            extract('month', FazlaMesai.tarih) == ay,
            extract('year', FazlaMesai.tarih) == yil,
        ).scalar() or 0
        aylik_mesai.append(float(toplam))

    # İzin türü dağılımı (bu yıl)
    izin_dagilimi_rows = db.session.query(
        IzinTalebi.tur, func.count(IzinTalebi.id)
    ).filter(
        IzinTalebi.durum == 'onaylandi',
        extract('year', IzinTalebi.baslangic_tarihi) == yil,
    ).group_by(IzinTalebi.tur).all()
    izin_dagilimi = [list(r) for r in izin_dagilimi_rows]

    # Savunma/tutanak türü dağılımı
    savunma_dagilimi_rows = db.session.query(
        SavunmaTutanak.tur, func.count(SavunmaTutanak.id)
    ).filter(SavunmaTutanak.aktif == True).group_by(SavunmaTutanak.tur).all()
    savunma_dagilimi = [list(r) for r in savunma_dagilimi_rows]

    return render_template('ik/raporlar.html',
                           yil=yil,
                           departman_dagilimi=departman_dagilimi,
                           aylik_mesai=aylik_mesai,
                           izin_dagilimi=izin_dagilimi,
                           savunma_dagilimi=savunma_dagilimi)


# ══════════════════════════════════════════════════════════════════
# İZİN BAKİYE
# ══════════════════════════════════════════════════════════════════

@ik_bp.route('/izin-bakiye')
@login_required
@modul_erisim_gerekli('ik')
def izin_bakiye():
    """Tüm çalışanların izin bakiyeleri."""
    yil = request.args.get('yil', date.today().year, type=int)
    calisanlar = Calisan.query.filter_by(aktif=True).order_by(Calisan.ad_soyad).all()

    bakiyeler = []
    for c in calisanlar:
        bakiye = izin_bakiye_hesapla(c.id, yil)
        if bakiye:
            bakiyeler.append({
                'calisan': c,
                'kidem': kidem_hesapla(c.id),
                'bakiye': bakiye,
            })

    return render_template('ik/izin_bakiye.html',
                           bakiyeler=bakiyeler, yil=yil)
