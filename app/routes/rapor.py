"""FDYS — Merkezi Raporlama Rotaları"""

from flask import Blueprint, render_template, send_file, request, flash, redirect, url_for
from flask_login import login_required
from app.models.makine import Makine, UretimVerisi
from app.models.stok import Malzeme
from app.models.kalite import HataKaydi
from app.models.personel import Calisan
from app.models.isg import IsKazasi
from app.models.enerji import EnerjiTuketimi
from app.utils.pdf_generator import PDFGenerator
from app.utils.excel_exporter import ExcelExporter
from app.utils.decorators import role_required
from datetime import datetime

rapor_bp = Blueprint('rapor', __name__, url_prefix='/rapor')
pdf_gen = PDFGenerator()
excel_exp = ExcelExporter()

@rapor_bp.route('/')
@login_required
@role_required('yonetici')
def index():
    """Raporlama merkezi ana sayfa."""
    makineler = Makine.query.filter_by(aktif=True).all()
    bugun = datetime.now()
    return render_template('rapor/index.html', makineler=makineler, yil=bugun.year, ay=bugun.month)

# ==================== PDF RAPORLARI ====================

@rapor_bp.route('/pdf/makine/<int:id>')
@login_required
@role_required('yonetici')
def pdf_makine(id):
    makine = Makine.query.get_or_404(id)
    veriler = makine.uretim_verileri.order_by(UretimVerisi.tarih.desc()).limit(50).all()
    
    pdf_buffer = pdf_gen.uretim_raporu(makine, veriler)
    filename = f"Uretim_Raporu_{makine.kod}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@rapor_bp.route('/pdf/kalite')
@login_required
@role_required('yonetici')
def pdf_kalite():
    ay = request.args.get('ay', datetime.now().month, type=int)
    yil = request.args.get('yil', datetime.now().year, type=int)
    
    # Gerçek uygulamada filter_by ay/yil yapılması gerekir. Şimdilik limit 100.
    hatalar = HataKaydi.query.order_by(HataKaydi.tarih.desc()).limit(100).all()
    
    pdf_buffer = pdf_gen.kalite_raporu(hatalar, ay, yil)
    filename = f"ISO9001_Kalite_Raporu_{yil}_{ay:02d}.pdf"
    
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@rapor_bp.route('/pdf/isg')
@login_required
@role_required('yonetici')
def pdf_isg():
    yil = request.args.get('yil', datetime.now().year, type=int)
    
    olaylar = IsKazasi.query.order_by(IsKazasi.tarih.desc()).limit(100).all()
    
    pdf_buffer = pdf_gen.isg_raporu(olaylar, yil)
    filename = f"ISO45001_ISG_Raporu_{yil}.pdf"
    
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@rapor_bp.route('/pdf/enerji')
@login_required
@role_required('yonetici')
def pdf_enerji():
    ay = request.args.get('ay', datetime.now().month, type=int)
    yil = request.args.get('yil', datetime.now().year, type=int)
    
    tuketimler = EnerjiTuketimi.query.order_by(EnerjiTuketimi.donem_baslangic.desc()).limit(100).all()
    
    pdf_buffer = pdf_gen.enerji_raporu(tuketimler, ay, yil)
    filename = f"ISO50001_Enerji_Raporu_{yil}_{ay:02d}.pdf"
    
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@rapor_bp.route('/pdf/sgk/<int:id>')
@login_required
@role_required('yonetici')
def pdf_sgk(id):
    olay = IsKazasi.query.get_or_404(id)
    pdf_buffer = pdf_gen.sgk_bildirim_formu(olay)
    filename = f"SGK_Bildirim_{olay.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

# ==================== EXCEL ÇIKTILARI ====================

@rapor_bp.route('/excel/stok')
@login_required
@role_required('yonetici')
def excel_stok():
    malzemeler = Malzeme.query.all()
    basliklar = ['Kod', 'Ad', 'Birim', 'Kategori', 'Mevcut Miktar', 'Kritik Seviye', 'Birim Fiyat']
    veriler = []
    for m in malzemeler:
        veriler.append([m.kod, m.ad, m.birim, m.kategori, m.mevcut_miktar, m.minimum_stok, m.birim_fiyat])
        
    excel_buffer = excel_exp.listeyi_disa_aktar(basliklar, veriler, "Stok_Listesi")
    return send_file(excel_buffer, as_attachment=True, download_name="Stok_Listesi.xlsx", 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@rapor_bp.route('/excel/personel')
@login_required
@role_required('yonetici')
def excel_personel():
    personel = Calisan.query.all()
    basliklar = ['Sicil No', 'Ad Soyad', 'E-posta', 'Departman', 'Pozisyon', 'İşe Başlama']
    veriler = []
    for p in personel:
        veriler.append([p.sicil_no, p.ad_soyad, p.eposta, p.departman, p.pozisyon, p.ise_baslama.strftime('%d.%m.%Y')])
        
    excel_buffer = excel_exp.listeyi_disa_aktar(basliklar, veriler, "Personel_Listesi")
    return send_file(excel_buffer, as_attachment=True, download_name="Personel_Listesi.xlsx", 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@rapor_bp.route('/excel/uretim')
@login_required
@role_required('yonetici')
def excel_uretim():
    veriler_db = UretimVerisi.query.order_by(UretimVerisi.tarih.desc()).limit(500).all()
    basliklar = ['Tarih', 'Vardiya', 'Makine Kodu', 'Planlanan Süre(Dk)', 'Gerçek Çalışma(Dk)', 'Duruş(Dk)', 'Üretim', 'Hata', 'OEE(%)']
    veriler = []
    for v in veriler_db:
        durus = (v.planlanan_sure_dk or 0) - (v.gercek_calisma_dk or 0)
        veriler.append([
            v.tarih.strftime('%d.%m.%Y'), v.vardiya.capitalize(), v.makine.kod if v.makine else "-", 
            v.planlanan_sure_dk, v.gercek_calisma_dk, durus, v.gercek_uretim, v.hatali_uretim, v.oee_yuzde
        ])
        
    excel_buffer = excel_exp.listeyi_disa_aktar(basliklar, veriler, "Uretim_Listesi")
    return send_file(excel_buffer, as_attachment=True, download_name="Uretim_Verileri.xlsx", 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@rapor_bp.route('/excel/kalite')
@login_required
@role_required('yonetici')
def excel_kalite():
    hatalar = HataKaydi.query.order_by(HataKaydi.tarih.desc()).limit(500).all()
    basliklar = ['Tarih', 'Makine Kodu', 'Hata Kategorisi', 'Hata Türü', 'Adet', 'Fire Oranı (%)']
    veriler = []
    for h in hatalar:
        veriler.append([
            h.tarih.strftime('%d.%m.%Y %H:%M'), h.makine.kod if h.makine else "-", 
            h.hata_kategorisi, h.hata_turu, h.adet, float(h.fire_orani or 0)
        ])
        
    excel_buffer = excel_exp.listeyi_disa_aktar(basliklar, veriler, "Kalite_Hatalari")
    return send_file(excel_buffer, as_attachment=True, download_name="Kalite_Raporu.xlsx", 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@rapor_bp.route('/excel/enerji')
@login_required
@role_required('yonetici')
def excel_enerji():
    tuketimler = EnerjiTuketimi.query.order_by(EnerjiTuketimi.donem_baslangic.desc()).limit(500).all()
    basliklar = ['Dönem', 'Makine Kodu', 'Enerji Türü', 'Tüketim', 'Birim', 'Birim Fiyat (TL)', 'Toplam Maliyet (TL)']
    veriler = []
    for t in tuketimler:
        veriler.append([
            t.donem_baslangic.strftime('%d.%m.%Y'), t.makine.kod if t.makine else "-", 
            t.enerji_turu, float(t.miktar), t.birim, float(t.birim_fiyat or 0), float(t.toplam_maliyet or 0)
        ])
        
    excel_buffer = excel_exp.listeyi_disa_aktar(basliklar, veriler, "Enerji_Tuketimleri")
    return send_file(excel_buffer, as_attachment=True, download_name="Enerji_Raporu.xlsx", 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@rapor_bp.route('/excel/isg')
@login_required
@role_required('yonetici')
def excel_isg():
    olaylar = IsKazasi.query.order_by(IsKazasi.tarih.desc()).limit(500).all()
    basliklar = ['Tarih', 'Olay Türü', 'Kategori', 'Şiddet', 'Kayıp Gün', 'Durum', 'Lokasyon', 'Açıklama']
    veriler = []
    for o in olaylar:
        olay_turu = 'Ramak Kala' if o.ramak_kala else 'İş Kazası'
        veriler.append([
            o.tarih.strftime('%d.%m.%Y %H:%M'), olay_turu, o.yaralanma_tipi, o.siddet, 
            o.kayip_gun, o.durum, o.yer, o.aciklama
        ])
        
    excel_buffer = excel_exp.listeyi_disa_aktar(basliklar, veriler, "ISG_Olaylari")
    return send_file(excel_buffer, as_attachment=True, download_name="ISG_Raporu.xlsx", 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ==================== GELİŞMİŞ RAPORLAMA ====================

@rapor_bp.route('/gelismis')
@login_required
@role_required('yonetici')
def gelismis():
    """Gelişmiş raporlama ana sayfası."""
    return render_template('rapor/gelismis.html')


@rapor_bp.route('/karsilastirma')
@login_required
@role_required('yonetici')
def karsilastirma():
    """Bu ay vs geçen ay karşılaştırmalı rapor."""
    from sqlalchemy import func
    from datetime import timedelta
    from app.models.makine import ArizaKaydi

    bugun = datetime.now().date()
    bu_ay_bas = bugun.replace(day=1)
    gecen_ay_son = bu_ay_bas - timedelta(days=1)
    gecen_ay_bas = gecen_ay_son.replace(day=1)

    def _donem_verileri(bas, son):
        uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim)).filter(
            UretimVerisi.tarih >= bas, UretimVerisi.tarih <= son).scalar() or 0
        oee = db.session.query(func.avg(UretimVerisi.oee_yuzde)).filter(
            UretimVerisi.tarih >= bas, UretimVerisi.tarih <= son).scalar() or 0
        hata_toplam = db.session.query(func.sum(UretimVerisi.hatali_uretim)).filter(
            UretimVerisi.tarih >= bas, UretimVerisi.tarih <= son).scalar() or 0
        ariza = ArizaKaydi.query.filter(ArizaKaydi.baslangic_zamani >= datetime.combine(bas, datetime.min.time()),
                                         ArizaKaydi.baslangic_zamani <= datetime.combine(son, datetime.max.time())).count()
        enerji_m = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet)).filter(
            EnerjiTuketimi.donem_baslangic >= bas, EnerjiTuketimi.donem_baslangic <= son).scalar() or 0
        return {'uretim': int(uretim), 'oee': round(float(oee), 1), 'hata': int(hata_toplam),
                'ariza': ariza, 'enerji': round(float(enerji_m), 2)}

    from app.extensions import db
    bu = _donem_verileri(bu_ay_bas, bugun)
    gecen = _donem_verileri(gecen_ay_bas, gecen_ay_son)

    def _degisim(bu_v, gecen_v):
        if gecen_v == 0:
            return 0
        return round(((bu_v - gecen_v) / gecen_v) * 100, 1)

    kpiler = [
        {'baslik': 'Toplam Üretim', 'bu_ay': f"{bu['uretim']:,}", 'gecen_ay': f"{gecen['uretim']:,}",
         'degisim': _degisim(bu['uretim'], gecen['uretim']), 'iyi_yonde': True},
        {'baslik': 'Ortalama OEE', 'bu_ay': f"%{bu['oee']}", 'gecen_ay': f"%{gecen['oee']}",
         'degisim': _degisim(bu['oee'], gecen['oee']), 'iyi_yonde': True},
        {'baslik': 'Hatalı Üretim', 'bu_ay': f"{bu['hata']:,}", 'gecen_ay': f"{gecen['hata']:,}",
         'degisim': _degisim(bu['hata'], gecen['hata']), 'iyi_yonde': False},
        {'baslik': 'Arıza Sayısı', 'bu_ay': str(bu['ariza']), 'gecen_ay': str(gecen['ariza']),
         'degisim': _degisim(bu['ariza'], gecen['ariza']), 'iyi_yonde': False},
        {'baslik': 'Enerji Maliyeti', 'bu_ay': f"₺{bu['enerji']:,.0f}", 'gecen_ay': f"₺{gecen['enerji']:,.0f}",
         'degisim': _degisim(bu['enerji'], gecen['enerji']), 'iyi_yonde': False},
    ]

    grafik_labels = [k['baslik'] for k in kpiler]
    grafik_gecen = [gecen['uretim'], gecen['oee'], gecen['hata'], gecen['ariza'], gecen['enerji']]
    grafik_bu = [bu['uretim'], bu['oee'], bu['hata'], bu['ariza'], bu['enerji']]

    return render_template('rapor/karsilastirma.html', kpiler=kpiler,
                           grafik_labels=grafik_labels, grafik_gecen=grafik_gecen, grafik_bu=grafik_bu)


@rapor_bp.route('/api/veri')
@login_required
@role_required('yonetici')
def api_rapor_veri():
    """AJAX ile tarih aralığına göre dinamik rapor verisi döner."""
    from flask import jsonify
    from sqlalchemy import func
    from app.models.makine import ArizaKaydi

    modul = request.args.get('modul', 'uretim')
    baslangic_str = request.args.get('baslangic', '')
    bitis_str = request.args.get('bitis', '')

    try:
        baslangic = datetime.strptime(baslangic_str, '%Y-%m-%d').date()
        bitis = datetime.strptime(bitis_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Geçersiz tarih formatı.'})

    from app.extensions import db

    if modul == 'uretim':
        veriler = db.session.query(
            UretimVerisi.tarih, func.sum(UretimVerisi.gercek_uretim), func.avg(UretimVerisi.oee_yuzde),
            func.sum(UretimVerisi.hatali_uretim)
        ).filter(UretimVerisi.tarih >= baslangic, UretimVerisi.tarih <= bitis
        ).group_by(UretimVerisi.tarih).order_by(UretimVerisi.tarih).all()

        toplam_u = sum(v[1] or 0 for v in veriler)
        ort_oee = round(sum(v[2] or 0 for v in veriler) / max(len(veriler), 1), 1)
        toplam_h = sum(v[3] or 0 for v in veriler)

        return jsonify({'success': True,
            'ozet': [
                {'baslik': 'Toplam Üretim', 'deger': f'{int(toplam_u):,}', 'renk': '#3b82f6'},
                {'baslik': 'Ort. OEE', 'deger': f'%{ort_oee}', 'renk': '#10b981' if ort_oee >= 85 else '#f59e0b'},
                {'baslik': 'Hatalı Üretim', 'deger': f'{int(toplam_h):,}', 'renk': '#ef4444'},
                {'baslik': 'Gün Sayısı', 'deger': str(len(veriler)), 'renk': '#8b5cf6'},
            ],
            'grafik': {
                'labels': [v[0].strftime('%d.%m') for v in veriler],
                'datasets': [
                    {'label': 'Üretim', 'data': [int(v[1] or 0) for v in veriler], 'color': '#3b82f6'},
                    {'label': 'OEE (%)', 'data': [round(float(v[2] or 0), 1) for v in veriler], 'color': '#10b981'},
                ]
            },
            'tablo': {
                'basliklar': ['Tarih', 'Üretim', 'OEE (%)', 'Hatalı'],
                'satirlar': [[v[0].strftime('%d.%m.%Y'), int(v[1] or 0), round(float(v[2] or 0), 1), int(v[3] or 0)] for v in veriler]
            }
        })

    elif modul == 'kalite':
        hatalar = HataKaydi.query.filter(HataKaydi.tarih >= datetime.combine(baslangic, datetime.min.time()),
                                          HataKaydi.tarih <= datetime.combine(bitis, datetime.max.time())
                                          ).order_by(HataKaydi.tarih.desc()).all()
        
        gunluk = {}
        for h in hatalar:
            t = h.tarih.date()
            if t not in gunluk: gunluk[t] = 0
            gunluk[t] += (h.adet or 0)
        gunler_sirali = sorted(gunluk.keys())
        
        return jsonify({'success': True,
            'ozet': [
                {'baslik': 'Toplam Hata Kaydı', 'deger': str(len(hatalar)), 'renk': '#ef4444'},
                {'baslik': 'Toplam Fire Adedi', 'deger': str(sum(h.adet or 0 for h in hatalar)), 'renk': '#f59e0b'},
            ],
            'grafik': {
                'labels': [g.strftime('%d.%m') for g in gunler_sirali],
                'datasets': [
                    {'label': 'Hata Adedi', 'data': [gunluk[g] for g in gunler_sirali], 'color': '#ef4444'}
                ]
            },
            'tablo': {
                'basliklar': ['Tarih', 'Makine', 'Hata Türü', 'Adet'],
                'satirlar': [[h.tarih.strftime('%d.%m.%Y'), h.makine.kod if h.makine else '-', h.hata_turu, h.adet] for h in hatalar[:100]]
            }
        })

    elif modul == 'enerji':
        tuketimler = EnerjiTuketimi.query.filter(
            EnerjiTuketimi.donem_baslangic >= baslangic, EnerjiTuketimi.donem_baslangic <= bitis
        ).order_by(EnerjiTuketimi.donem_baslangic).all()
        toplam_m = sum(float(t.toplam_maliyet or 0) for t in tuketimler)
        return jsonify({'success': True,
            'ozet': [
                {'baslik': 'Toplam Maliyet', 'deger': f'₺{toplam_m:,.0f}', 'renk': '#f59e0b'},
                {'baslik': 'Kayıt Sayısı', 'deger': str(len(tuketimler)), 'renk': '#3b82f6'},
            ],
            'grafik': {'labels': [t.donem_baslangic.strftime('%d.%m') for t in tuketimler],
                       'datasets': [{'label': 'Maliyet (₺)', 'data': [float(t.toplam_maliyet or 0) for t in tuketimler], 'color': '#f59e0b'}]},
            'tablo': {
                'basliklar': ['Dönem', 'Makine', 'Tür', 'Miktar', 'Maliyet (₺)'],
                'satirlar': [[t.donem_baslangic.strftime('%d.%m.%Y'), t.makine.kod if t.makine else '-', t.enerji_turu, float(t.miktar), float(t.toplam_maliyet or 0)] for t in tuketimler[:100]]
            }
        })

    elif modul == 'isg':
        olaylar = IsKazasi.query.filter(IsKazasi.tarih >= datetime.combine(baslangic, datetime.min.time()),
                                         IsKazasi.tarih <= datetime.combine(bitis, datetime.max.time())).order_by(IsKazasi.tarih.desc()).all()
        
        gunluk_kaza = {}
        gunluk_ramak = {}
        for o in olaylar:
            d = o.tarih.date()
            if o.ramak_kala:
                gunluk_ramak[d] = gunluk_ramak.get(d, 0) + 1
                if d not in gunluk_kaza: gunluk_kaza[d] = 0
            else:
                gunluk_kaza[d] = gunluk_kaza.get(d, 0) + 1
                if d not in gunluk_ramak: gunluk_ramak[d] = 0
                
        gunler_sirali = sorted(set(list(gunluk_kaza.keys()) + list(gunluk_ramak.keys())))
        
        return jsonify({'success': True,
            'ozet': [
                {'baslik': 'Toplam Olay', 'deger': str(len(olaylar)), 'renk': '#ef4444'},
                {'baslik': 'İş Kazası', 'deger': str(sum(1 for o in olaylar if not o.ramak_kala)), 'renk': '#dc2626'},
                {'baslik': 'Ramak Kala', 'deger': str(sum(1 for o in olaylar if o.ramak_kala)), 'renk': '#f59e0b'},
            ],
            'grafik': {
                'labels': [g.strftime('%d.%m') for g in gunler_sirali],
                'datasets': [
                    {'label': 'İş Kazası', 'data': [gunluk_kaza.get(g,0) for g in gunler_sirali], 'color': '#dc2626'},
                    {'label': 'Ramak Kala', 'data': [gunluk_ramak.get(g,0) for g in gunler_sirali], 'color': '#f59e0b'},
                ]
            },
            'tablo': {
                'basliklar': ['Tarih', 'Tür', 'Şiddet', 'Durum', 'Lokasyon'],
                'satirlar': [[o.tarih.strftime('%d.%m.%Y'), 'Ramak Kala' if o.ramak_kala else 'İş Kazası', o.siddet, o.durum, o.yer] for o in olaylar[:100]]
            }
        })
        
    elif modul == 'stok':
        from app.models.stok import StokHareketi
        hareketler = StokHareketi.query.filter(
            StokHareketi.tarih >= datetime.combine(baslangic, datetime.min.time()),
            StokHareketi.tarih <= datetime.combine(bitis, datetime.max.time())
        ).order_by(StokHareketi.tarih.desc()).all()
        
        gunluk_giris = {}
        gunluk_cikis = {}
        toplam_g = 0
        toplam_c = 0
        for h in hareketler:
            d = h.tarih.date()
            m = float(h.miktar or 0)
            if h.hareket_turu == 'giris':
                toplam_g += m
                gunluk_giris[d] = gunluk_giris.get(d, 0) + m
                if d not in gunluk_cikis: gunluk_cikis[d] = 0
            else:
                toplam_c += m
                gunluk_cikis[d] = gunluk_cikis.get(d, 0) + m
                if d not in gunluk_giris: gunluk_giris[d] = 0
                
        gunler_sirali = sorted(set(list(gunluk_giris.keys()) + list(gunluk_cikis.keys())))
        
        return jsonify({'success': True,
            'ozet': [
                {'baslik': 'Toplam Giriş', 'deger': f'{toplam_g:,.0f}', 'renk': '#10b981'},
                {'baslik': 'Toplam Çıkış', 'deger': f'{toplam_c:,.0f}', 'renk': '#ef4444'},
                {'baslik': 'Net Hareket', 'deger': f'{toplam_g - toplam_c:,.0f}', 'renk': '#3b82f6'},
            ],
            'grafik': {
                'labels': [g.strftime('%d.%m') for g in gunler_sirali],
                'datasets': [
                    {'label': 'Giriş', 'data': [gunluk_giris.get(g,0) for g in gunler_sirali], 'color': '#10b981'},
                    {'label': 'Çıkış', 'data': [gunluk_cikis.get(g,0) for g in gunler_sirali], 'color': '#ef4444'}
                ]
            },
            'tablo': {
                'basliklar': ['Tarih', 'Malzeme', 'Tür', 'Miktar', 'Neden'],
                'satirlar': [[h.tarih.strftime('%d.%m.%Y %H:%M'), h.malzeme.ad if h.malzeme else '-', h.hareket_turu.upper(), float(h.miktar), h.neden or '-'] for h in hareketler[:100]]
            }
        })
        
    elif modul == 'personel':
        from app.models.personel import VardiyaPlani, Calisan
        vardiyalar = VardiyaPlani.query.filter(
            VardiyaPlani.tarih >= baslangic, VardiyaPlani.tarih <= bitis
        ).order_by(VardiyaPlani.tarih.desc()).all()
        
        calisan_sayisi = Calisan.query.filter_by(aktif=True).count()
        toplam_vardiya = len(vardiyalar)
        
        gunluk = {}
        for v in vardiyalar:
            d = v.tarih
            if d not in gunluk:
                gunluk[d] = {'sabah': 0, 'ogleden_sonra': 0, 'gece': 0, 'off': 0}
            if v.vardiya_turu in gunluk[d]:
                gunluk[d][v.vardiya_turu] += 1
                
        gunler_sirali = sorted(gunluk.keys())
        
        return jsonify({'success': True,
            'ozet': [
                {'baslik': 'Aktif Personel', 'deger': str(calisan_sayisi), 'renk': '#3b82f6'},
                {'baslik': 'Toplam Vardiya Ataması', 'deger': str(toplam_vardiya), 'renk': '#8b5cf6'},
            ],
            'grafik': {
                'labels': [g.strftime('%d.%m') for g in gunler_sirali],
                'datasets': [
                    {'label': 'Sabah', 'data': [gunluk[g]['sabah'] for g in gunler_sirali], 'color': '#f59e0b'},
                    {'label': 'Öğle', 'data': [gunluk[g]['ogleden_sonra'] for g in gunler_sirali], 'color': '#3b82f6'},
                    {'label': 'Gece', 'data': [gunluk[g]['gece'] for g in gunler_sirali], 'color': '#1f2937'}
                ]
            },
            'tablo': {
                'basliklar': ['Tarih', 'Personel', 'Vardiya', 'Başlangıç-Bitiş'],
                'satirlar': [[v.tarih.strftime('%d.%m.%Y'), v.calisan.ad_soyad if v.calisan else '-', v.vardiya_turu.upper(), f"{v.baslangic.strftime('%H:%M')}-{v.bitis.strftime('%H:%M')}"] for v in vardiyalar[:100]]
            }
        })

    else:
        return jsonify({'success': True, 'ozet': [], 'grafik': {'labels': [], 'datasets': []},
                        'tablo': {'basliklar': [], 'satirlar': []}})
