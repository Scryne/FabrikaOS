"""FDYS — Dashboard (Ana Kontrol Paneli) Rotaları (Faz 3 — Profesyonel)"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db, cache
from app.models.personel import Calisan, IzinTalebi, VardiyaPlani
from app.models.makine import Makine, UretimVerisi, ArizaKaydi
from app.models.stok import Malzeme
from app.models.bildirim import Bildirim
from app.models.kalite import HataKaydi, DuzelticiFaaliyet
from app.models.enerji import EnerjiTuketimi
from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Ana dashboard sayfası — KPI şerit + modül kartları + grafikler."""
    if current_user.rol == 'operator':
        return operator_dashboard()
    elif current_user.rol == 'teknisyen':
        return teknisyen_dashboard()

    # Yönetici Dashboard'u için veri hazırlığı
    bugun = datetime.now(timezone.utc).date()
    yedi_gun_once = bugun - timedelta(days=7)
    otuz_gun_once = bugun - timedelta(days=30)

    # ── Personel ──
    aktif_calisan = Calisan.query.filter_by(aktif=True).count()
    bekleyen_izin = IzinTalebi.query.filter_by(durum='bekliyor').count()

    # ── Makine & OEE ──
    aktif_makine = Makine.query.filter_by(aktif=True, durum='aktif').count()
    toplam_makine = Makine.query.filter_by(aktif=True).count()
    arizali_makine = Makine.query.filter_by(aktif=True, durum='arizali').count()
    acik_ariza = ArizaKaydi.query.filter_by(durum='acik').count()

    # Ortalama OEE (Son 7 gün)
    ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde))\
        .filter(UretimVerisi.tarih >= yedi_gun_once).scalar() or 0
    ort_oee = round(float(ort_oee), 1)

    # Bugünkü toplam üretim
    bugun_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
        .filter(UretimVerisi.tarih == bugun).scalar() or 0

    # ── Stok ──
    kritik_stok = Malzeme.query.filter(Malzeme.mevcut_miktar <= Malzeme.minimum_stok).count()

    # ── Kalite ──
    # Son 30 gün hata oranı (toplam hatalı / toplam üretim)
    toplam_uretim_30g = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
        .filter(UretimVerisi.tarih >= otuz_gun_once).scalar() or 1
    toplam_hata_30g = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
        .filter(UretimVerisi.tarih >= otuz_gun_once).scalar() or 0
    hata_orani = round((int(toplam_hata_30g) / int(toplam_uretim_30g)) * 100, 2) if toplam_uretim_30g else 0

    acik_faaliyetler = DuzelticiFaaliyet.query.filter(
        DuzelticiFaaliyet.durum.in_(['acik', 'devam'])
    ).count()

    # ── Enerji ──
    # Son ay enerji maliyeti
    son_ay_maliyet = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet))\
        .filter(EnerjiTuketimi.donem_baslangic >= otuz_gun_once).scalar() or 0

    # Hedef sapma ortalama
    hedef_sapmalar = db.session.query(EnerjiTuketimi.miktar, EnerjiTuketimi.hedef_miktar)\
        .filter(
            EnerjiTuketimi.hedef_miktar.isnot(None),
            EnerjiTuketimi.hedef_miktar > 0,
            EnerjiTuketimi.donem_baslangic >= otuz_gun_once
        ).all()

    enerji_sapma = 0
    if hedef_sapmalar:
        sapmalar = [((float(m) - float(h)) / float(h)) * 100 for m, h in hedef_sapmalar if h]
        enerji_sapma = round(sum(sapmalar) / len(sapmalar), 1) if sapmalar else 0

    # Faz 3: Enerji İsrafı Hesaplama (Mock)
    enerji_israf_tl = round((toplam_makine - aktif_makine) * 2450.50 + arizali_makine * 1250, 2)
    if enerji_israf_tl < 1000:
        enerji_israf_tl = 14550.00

    # ── İSG ──
    yil_basi = datetime(bugun.year, 1, 1)
    is_kazasi_sayisi = IsKazasi.query.filter(
        IsKazasi.tarih >= yil_basi,
        IsKazasi.ramak_kala == False
    ).count()
    ramak_kala_sayisi = IsKazasi.query.filter(
        IsKazasi.tarih >= yil_basi,
        IsKazasi.ramak_kala == True
    ).count()
    yuksek_risk = RiskDegerlendirme.query.filter_by(
        risk_seviyesi='yuksek', durum='acik'
    ).count()
    suresi_dolan_egitim = IsgEgitimi.query.filter(
        IsgEgitimi.gecerlilik_bitis < bugun,
        IsgEgitimi.durum == 'gecerli'
    ).count()

    # Bakımı geciken makine sayısı
    tum_makineler = Makine.query.filter_by(aktif=True).all()
    bakim_geciken = sum(1 for m in tum_makineler if m.bakim_gecikti_mi)

    # ── OEE Trend (Son 7 gün — Mini Grafik) ──
    oee_trend = db.session.query(
        UretimVerisi.tarih, func.avg(UretimVerisi.oee_yuzde)
    ).filter(UretimVerisi.tarih >= yedi_gun_once)\
     .group_by(UretimVerisi.tarih)\
     .order_by(UretimVerisi.tarih).all()

    oee_trend_labels = [d[0].strftime('%d.%m') for d in oee_trend]
    oee_trend_values = [round(float(d[1]), 1) if d[1] else 0 for d in oee_trend]

    # ── Son 5 Bildirim ──
    son_bildirimler = Bildirim.query.order_by(Bildirim.olusturma_tarihi.desc()).limit(5).all()

    # Son işe başlayanlar
    yeni_personeller = Calisan.query.filter_by(aktif=True)\
        .order_by(Calisan.ise_baslama.desc()).limit(5).all()

    stats = {
        'aktif_calisan': aktif_calisan,
        'bekleyen_izin': bekleyen_izin,
        'aktif_makine': aktif_makine,
        'toplam_makine': toplam_makine,
        'arizali_makine': arizali_makine,
        'acik_ariza': acik_ariza,
        'ort_oee': ort_oee,
        'bugun_uretim': bugun_uretim,
        'kritik_stok': kritik_stok,
        'hata_orani': hata_orani,
        'acik_faaliyetler': acik_faaliyetler,
        'son_ay_maliyet': round(float(son_ay_maliyet), 2),
        'enerji_sapma': enerji_sapma,
        'is_kazasi': is_kazasi_sayisi,
        'ramak_kala': ramak_kala_sayisi,
        'yuksek_risk': yuksek_risk,
        'suresi_dolan_egitim': suresi_dolan_egitim,
        'bakim_geciken': bakim_geciken,
        'enerji_israf_tl': enerji_israf_tl,
    }

    # ── AI Tahminleme Özeti ──
    ai_ozet = None
    try:
        from app.services.tahmin_motoru import tahmin_motoru
        ai_ozet = tahmin_motoru.dashboard_ozeti()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"AI modülü yüklenemedi: {e}")

    return render_template('dashboard/index.html',
                           stats=stats,
                           oee_trend={'labels': oee_trend_labels, 'values': oee_trend_values},
                           son_bildirimler=son_bildirimler,
                           yeni_personeller=yeni_personeller,
                           ai_ozet=ai_ozet)

@dashboard_bp.route('/kiosk')
@login_required
def kiosk():
    """Kiosk modu — TV/Büyük ekranlar için tam ekran veri gösterimi."""
    bugun = datetime.now(timezone.utc).date()
    yedi_gun_once = bugun - timedelta(days=7)

    bugun_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim)).filter(
        UretimVerisi.tarih == bugun).scalar() or 0

    ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde)).filter(
        UretimVerisi.tarih >= yedi_gun_once).scalar() or 0

    aktif_makine = Makine.query.filter_by(aktif=True, durum='aktif').count()
    toplam_makine = Makine.query.filter_by(aktif=True).count()
    acik_ariza = ArizaKaydi.query.filter_by(durum='acik').count()

    stats = {
        'bugun_uretim': bugun_uretim,
        'ort_oee': round(float(ort_oee), 1),
        'aktif_makine': aktif_makine,
        'toplam_makine': toplam_makine,
        'acik_ariza': acik_ariza,
    }

    son_bildirimler = Bildirim.query.order_by(Bildirim.olusturma_tarihi.desc()).limit(5).all()

    return render_template('dashboard/kiosk.html', stats=stats, son_bildirimler=son_bildirimler)


@dashboard_bp.route('/bildirimler')
@login_required
def bildirimler():
    """Tüm bildirimlerin listelendiği sayfa."""
    page = request.args.get('page', 1, type=int)
    bildirimler_pagination = Bildirim.query.filter_by(
        kullanici_id=current_user.id
    ).order_by(
        Bildirim.okundu_mu.asc(), 
        Bildirim.olusturma_tarihi.desc()
    ).paginate(page=page, per_page=15, error_out=False)
    
    return render_template('dashboard/bildirimler.html', bildirimler=bildirimler_pagination)



@dashboard_bp.route('/api/bildirimler')
@login_required
def api_bildirimler():
    """Kullanıcının okunmamış bildirimlerini döndürür (AJAX/Polling)."""
    bildirimler = Bildirim.query.filter_by(
        kullanici_id=current_user.id,
        okundu_mu=False
    ).order_by(Bildirim.olusturma_tarihi.desc()).limit(10).all()

    data = []
    for b in bildirimler:
        data.append({
            'id': b.id,
            'baslik': b.baslik,
            'mesaj': b.mesaj,
            'seviye': b.seviye,
            'url': b.url,
            'tarih': b.olusturma_tarihi.strftime('%d.%m.%Y %H:%M')
        })

    return jsonify({
        'okunmamis_sayisi': Bildirim.query.filter_by(kullanici_id=current_user.id, okundu_mu=False).count(),
        'bildirimler': data
    })


@dashboard_bp.route('/api/bildirim/okundu', methods=['POST'])
@login_required
def api_bildirim_okundu():
    """Belirli bir bildirimi okundu olarak işaretler."""
    bildirim_id = request.json.get('id')

    if bildirim_id == 'all':
        bildirimler = Bildirim.query.filter_by(kullanici_id=current_user.id, okundu_mu=False).all()
        for b in bildirimler:
            b.okundu_mu = True
    else:
        bildirim = Bildirim.query.get(bildirim_id)
        if bildirim and bildirim.kullanici_id == current_user.id:
            bildirim.okundu_mu = True

    db.session.commit()
    return jsonify({'status': 'success'})


@dashboard_bp.route('/api/dashboard/realtime')
@login_required
def api_dashboard_realtime():
    """Gerçek zamanlı OEE ve üretim verileri (polling ile)."""
    bugun = datetime.now(timezone.utc).date()
    yedi_gun_once = bugun - timedelta(days=7)

    bugun_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim)).filter(
        UretimVerisi.tarih == bugun).scalar() or 0

    ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde)).filter(
        UretimVerisi.tarih >= yedi_gun_once).scalar() or 0

    aktif_makine = Makine.query.filter_by(aktif=True, durum='aktif').count()
    arizali_makine = Makine.query.filter_by(aktif=True, durum='arizali').count()
    acik_ariza = ArizaKaydi.query.filter_by(durum='acik').count()
    kritik_stok = Malzeme.query.filter(Malzeme.mevcut_miktar <= Malzeme.minimum_stok).count()

    return jsonify({
        'bugun_uretim': int(bugun_uretim),
        'ort_oee': round(float(ort_oee), 1),
        'aktif_makine': aktif_makine,
        'arizali_makine': arizali_makine,
        'acik_ariza': acik_ariza,
        'kritik_stok': kritik_stok,
        'zaman': datetime.now().strftime('%H:%M:%S')
    })


@dashboard_bp.route('/api/dashboard/layout', methods=['POST'])
@login_required
def api_dashboard_layout():
    """Widget düzenini kullanıcı bazında kaydeder."""
    from sqlalchemy.orm.attributes import flag_modified

    layout = request.json.get('layout', {})
    current_user.dashboard_layout = layout
    flag_modified(current_user, 'dashboard_layout')
    db.session.commit()

    return jsonify({'status': 'success'})


def operator_dashboard():
    """Operatörler için özel gösterge paneli."""
    bugun = datetime.now(timezone.utc).date()
    
    izinler = []
    vardiyalar = []
    haftalik_program = []
    is_emirleri = []
    izin_bakiye = {'toplam': 14, 'kullanilan': 0, 'kalan': 14, 'yuzde': 0}
    
    if current_user.calisan:
        # İzin talepleri
        izinler = IzinTalebi.query.filter_by(calisan_id=current_user.calisan.id).order_by(IzinTalebi.olusturma_tarihi.desc()).limit(5).all()
        # Bugünkü vardiyası
        vardiyalar = current_user.calisan.vardiya_planlari.filter(VardiyaPlani.tarih == bugun).all()
        
        # İzin bakiyesi hesaplama
        yillik_hak = 14
        kullanilan = IzinTalebi.query.filter(
            IzinTalebi.calisan_id == current_user.calisan.id,
            IzinTalebi.durum == 'onaylandi',
            IzinTalebi.tur == 'yillik',
            IzinTalebi.baslangic_tarihi >= datetime(bugun.year, 1, 1).date()
        ).all()
        kullanilan_gun = sum((iz.bitis_tarihi - iz.baslangic_tarihi).days + 1 for iz in kullanilan)
        kalan = max(yillik_hak - kullanilan_gun, 0)
        izin_bakiye = {
            'toplam': yillik_hak,
            'kullanilan': kullanilan_gun,
            'kalan': kalan,
            'yuzde': round((kullanilan_gun / yillik_hak) * 100) if yillik_hak else 0
        }
        
        # Haftalık vardiya programı
        hafta_bas = bugun - timedelta(days=bugun.weekday())
        gun_adlari = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
        renk_map = {'sabah': '#3b82f6', 'ogleden_sonra': '#f59e0b', 'gece': '#8b5cf6', 'off': '#6b7280'}
        tur_map = {'sabah': 'Sabah', 'ogleden_sonra': 'Öğle S.', 'gece': 'Gece', 'off': 'İzin'}
        
        for i in range(7):
            gun = hafta_bas + timedelta(days=i)
            v = VardiyaPlani.query.filter_by(calisan_id=current_user.calisan.id, tarih=gun).first()
            haftalik_program.append({
                'gun_adi': gun_adlari[i],
                'tarih': gun.strftime('%d.%m'),
                'bugun': gun == bugun,
                'vardiya': tur_map.get(v.vardiya_turu, v.vardiya_turu) if v else None,
                'renk': renk_map.get(v.vardiya_turu, '#6b7280') if v else '#6b7280'
            })
    
    # Atanan iş emirleri
    try:
        from app.models.is_emri import IsEmri
        is_emirleri = IsEmri.query.filter_by(
            atanan_id=current_user.id
        ).filter(IsEmri.durum.in_(['acik', 'devam'])).order_by(IsEmri.olusturma_tarihi.desc()).limit(5).all()
    except Exception:
        pass
        
    # Üretim KPI (Eğer bugüne ait veri yoksa, demo ortamı için kullanıcının son verilerini göster)
    uretim_kpi = {'oee': 0.0, 'uretim': 0, 'kalite': 0.0}
    if current_user.calisan:
        bugun_uretim_kayitlari = UretimVerisi.query.filter_by(calisan_id=current_user.calisan.id, tarih=bugun).all()
        
        # Bugüne ait kayıt yoksa, en son kayıt girilen günü bul
        if not bugun_uretim_kayitlari:
            son_kayit = UretimVerisi.query.filter_by(calisan_id=current_user.calisan.id).order_by(UretimVerisi.tarih.desc()).first()
            if son_kayit:
                bugun_uretim_kayitlari = UretimVerisi.query.filter_by(calisan_id=current_user.calisan.id, tarih=son_kayit.tarih).all()
                
        oee_liste = [float(u.oee_yuzde) for u in bugun_uretim_kayitlari if u.oee_yuzde]
        kalite_liste = [float(u.kalite) for u in bugun_uretim_kayitlari if u.kalite]
        uretim_kpi = {
            'oee': round(sum(oee_liste)/len(oee_liste), 1) if oee_liste else 0.0,
            'uretim': sum(u.gercek_uretim for u in bugun_uretim_kayitlari),
            'kalite': round(sum(kalite_liste)/len(kalite_liste), 1) if kalite_liste else 0.0,
        }

    aktif_makine = Makine.query.filter_by(aktif=True, durum='aktif').count()
    toplam_makine = Makine.query.filter_by(aktif=True).count()
    arizali_makine = Makine.query.filter_by(aktif=True, durum='arizali').count()
    makine_durum = {'aktif': aktif_makine, 'arizali': arizali_makine, 'toplam': toplam_makine}

    kritik_stok = Malzeme.query.filter(Malzeme.mevcut_miktar <= Malzeme.minimum_stok).count()
    
    yil_basi = datetime(bugun.year, 1, 1)
    isg_verisi = {
        'acik_risk': RiskDegerlendirme.query.filter_by(risk_seviyesi='yuksek', durum='acik').count(),
        'suresi_dolan_egitim': IsgEgitimi.query.filter(IsgEgitimi.gecerlilik_bitis < bugun, IsgEgitimi.durum == 'gecerli').count(),
        'yillik_olay': IsKazasi.query.filter(IsKazasi.tarih >= yil_basi).count()
    }
    
    bugun_hata = db.session.query(func.sum(UretimVerisi.hatali_uretim)).filter(UretimVerisi.tarih == bugun).scalar() or 0
    kalite_verisi = {'bugun_hata': int(bugun_hata)}
    
    son_bildirimler = Bildirim.query.filter_by(kullanici_id=current_user.id).order_by(Bildirim.olusturma_tarihi.desc()).limit(5).all()

    return render_template('dashboard/operator.html', bugun=bugun, izinler=izinler, vardiyalar=vardiyalar,
                           haftalik_program=haftalik_program, izin_bakiye=izin_bakiye, is_emirleri=is_emirleri,
                           uretim_kpi=uretim_kpi, makine_durum=makine_durum, kritik_stok=kritik_stok,
                           isg_verisi=isg_verisi, kalite_verisi=kalite_verisi, son_bildirimler=son_bildirimler)

def teknisyen_dashboard():
    """Teknisyenler için arıza ve bakım odaklı gösterge paneli."""
    bugun = datetime.now(timezone.utc).date()
    otuz_gun_once = bugun - timedelta(days=30)
    
    # Atanan Arızalar
    atanan_arizalar = ArizaKaydi.query.filter_by(
        atanan_teknisyen_id=current_user.id, 
        durum='acik'
    ).order_by(
        db.case(
            (ArizaKaydi.oncelik == 'kritik', 1),
            (ArizaKaydi.oncelik == 'yuksek', 2),
            (ArizaKaydi.oncelik == 'normal', 3),
            (ArizaKaydi.oncelik == 'dusuk', 4),
            else_=5
        ),
        ArizaKaydi.baslangic_zamani.asc()
    ).all()
    
    # Bugünkü bakım takvimi
    tum_makineler = Makine.query.filter_by(aktif=True).all()
    bakimi_gelen_makineler = [m for m in tum_makineler if m.sonraki_bakim_tarihi and m.sonraki_bakim_tarihi <= bugun]
    
    # Arıza çözme hızı (Son 30 gün)
    cozulenler = ArizaKaydi.query.filter(
        ArizaKaydi.atanan_teknisyen_id == current_user.id,
        ArizaKaydi.durum == 'cozuldu',
        ArizaKaydi.bitis_zamani >= otuz_gun_once
    ).all()
    
    ort_mudahale = 0
    if cozulenler:
        toplam_sure = sum(a.mudahale_suresi_dk or 0 for a in cozulenler)
        ort_mudahale = round(toplam_sure / len(cozulenler))
    
    # Performans istatistikleri
    toplam_cozulen = ArizaKaydi.query.filter(
        ArizaKaydi.atanan_teknisyen_id == current_user.id,
        ArizaKaydi.durum == 'cozuldu'
    ).count()
    
    son_30_cozulen = len(cozulenler)
    
    # Yaklaşan bakımlar (7 gün)
    yedi_gun_sonra = bugun + timedelta(days=7)
    yaklasan_bakimlar = [m for m in tum_makineler 
                         if m.sonraki_bakim_tarihi and bugun < m.sonraki_bakim_tarihi <= yedi_gun_sonra]

    # Makine Sağlık
    aktif_makine = sum(1 for m in tum_makineler if m.durum == 'aktif')
    toplam_makine = len(tum_makineler)
    bakim_geciken = sum(1 for m in tum_makineler if m.bakim_gecikti_mi)
    saglik_yuzdesi = round((aktif_makine / toplam_makine * 100) if toplam_makine > 0 else 0)
    makine_saglik = {
        'saglik_yuzdesi': saglik_yuzdesi,
        'aktif': aktif_makine,
        'toplam': toplam_makine,
        'bakim_geciken': bakim_geciken
    }
    
    # İSG Verisi
    yil_basi = datetime(bugun.year, 1, 1)
    isg_verisi = {
        'acik_risk': RiskDegerlendirme.query.filter_by(risk_seviyesi='yuksek', durum='acik').count(),
        'suresi_dolan_egitim': IsgEgitimi.query.filter(IsgEgitimi.gecerlilik_bitis < bugun, IsgEgitimi.durum == 'gecerli').count(),
        'is_kazasi': IsKazasi.query.filter(IsKazasi.tarih >= yil_basi, IsKazasi.ramak_kala == False).count(),
        'ramak_kala': IsKazasi.query.filter(IsKazasi.tarih >= yil_basi, IsKazasi.ramak_kala == True).count()
    }
    
    # Kritik Stok
    kritik_stoklar = Malzeme.query.filter(Malzeme.mevcut_miktar <= Malzeme.minimum_stok).all()
    kritik_stok_sayisi = len(kritik_stoklar)
    kritik_stok_listesi = kritik_stoklar[:5]
    
    # İş Emirleri
    try:
        from app.models.is_emri import IsEmri
        teknisyen_is_emirleri = IsEmri.query.filter_by(atanan_id=current_user.id).filter(IsEmri.durum.in_(['acik', 'devam'])).order_by(IsEmri.olusturma_tarihi.desc()).limit(5).all()
    except Exception:
        teknisyen_is_emirleri = []
        
    # Enerji Özeti
    aylik_maliyet = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet)).filter(EnerjiTuketimi.donem_baslangic >= otuz_gun_once).scalar() or 0
    aylik_karbon = db.session.query(func.sum(EnerjiTuketimi.karbon_salinimi)).filter(EnerjiTuketimi.donem_baslangic >= otuz_gun_once).scalar() or 0
    enerji_ozet = {'aylik_maliyet': aylik_maliyet, 'aylik_karbon': aylik_karbon}
    
    # Son Bildirimler
    son_bildirimler = Bildirim.query.filter_by(kullanici_id=current_user.id).order_by(Bildirim.olusturma_tarihi.desc()).limit(5).all()

    return render_template('dashboard/teknisyen.html', 
                           atanan_arizalar=atanan_arizalar,
                           bakimi_gelen_makineler=bakimi_gelen_makineler,
                           ort_mudahale=ort_mudahale,
                           toplam_cozulen=toplam_cozulen,
                           son_30_cozulen=son_30_cozulen,
                           yaklasan_bakimlar=yaklasan_bakimlar,
                           makine_saglik=makine_saglik,
                           isg_verisi=isg_verisi,
                           kritik_stok_sayisi=kritik_stok_sayisi,
                           kritik_stok_listesi=kritik_stok_listesi,
                           teknisyen_is_emirleri=teknisyen_is_emirleri,
                           enerji_ozet=enerji_ozet,
                           son_bildirimler=son_bildirimler,
                           bugun=bugun)

@dashboard_bp.route('/api/dashboard/insights')
@login_required
def api_dashboard_insights():
    """Faz 3: AI Darboğaz Analizi İçgörüleri (Mock)"""
    import random
    insights = [
        {"tip": "uyari", "ikon": "bi-exclamation-triangle-fill", "renk": "text-warning", "mesaj": "Dikkat: CNC-02 makinesi son 2 haftada paketleme hattından daha hızlı çalışarak yığılmaya sebep oluyor."},
        {"tip": "oneri", "ikon": "bi-lightbulb-fill", "renk": "text-success", "mesaj": "Öneri: Gece vardiyasında kalite hataları %40 artıyor. Aydınlatma veya yorgunluk kontrolü önerilir."},
        {"tip": "bilgi", "ikon": "bi-info-circle-fill", "renk": "text-info", "mesaj": "İçgörü: Pres-1 makinesinde hammadde besleme gecikmeleri OEE'yi %12 düşürüyor."},
        {"tip": "firsat", "ikon": "bi-graph-up-arrow", "renk": "text-primary", "mesaj": "Fırsat: Abkant-1 makinesinin bekleme süresini optimize etmek aylık %4 enerji tasarrufu sağlayabilir."},
        {"tip": "tehlike", "ikon": "bi-shield-fill-exclamation", "renk": "text-danger", "mesaj": "Risk: Planlı bakımı yaklaşan 2 makinede geçmişe göre titreşim artışı saptandı."}
    ]
    random.shuffle(insights)
    return jsonify({'insights': insights[:3]})
