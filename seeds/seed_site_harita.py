"""
FabrikaOS — Site Haritası Demo Verisi (v2)
"""
from app.extensions import db
from app.models.kurumsal import SiteHaritasi


def seed():
    print('[29/22] Site Haritası...') # Sembolik
    
    # Mevcutları sil
    SiteHaritasi.query.delete()

    harita_data = [
        # ── ANA MENÜLER ──
        {'baslik': 'Dashboard', 'url': '/', 'ikon': 'bi-speedometer2', 'sira': 10},
        
        # ── ÜRETİM ──
        {'baslik': 'Üretim', 'url': '#', 'ikon': 'bi-gear-wide-connected', 'sira': 20, 'alt_menuler': [
            {'baslik': 'Makine Parkı', 'url': '/makine', 'ikon': 'bi-hdd-network', 'sira': 21},
            {'baslik': 'Üretim Verileri', 'url': '/uretim', 'ikon': 'bi-activity', 'sira': 22},
            {'baslik': 'Vardiya Planı', 'url': '/vardiya', 'ikon': 'bi-clock-history', 'sira': 23},
        ]},
        
        # ── BAKIM VE İŞ EMİRLERİ ──
        {'baslik': 'Bakım', 'url': '#', 'ikon': 'bi-tools', 'sira': 30, 'alt_menuler': [
            {'baslik': 'Arıza Kayıtları', 'url': '/ariza', 'ikon': 'bi-exclamation-triangle', 'sira': 31},
            {'baslik': 'Bakım Planları', 'url': '/bakim', 'ikon': 'bi-calendar-check', 'sira': 32},
            {'baslik': 'İş Emirleri', 'url': '/is-emri', 'ikon': 'bi-journal-text', 'sira': 33},
        ]},

        # ── STOK VE SATIN ALMA ──
        {'baslik': 'Lojistik', 'url': '#', 'ikon': 'bi-box-seam', 'sira': 40, 'alt_menuler': [
            {'baslik': 'Stok Yönetimi', 'url': '/stok', 'ikon': 'bi-boxes', 'sira': 41},
            {'baslik': 'Satın Alma', 'url': '/satin-alma', 'ikon': 'bi-cart3', 'sira': 42},
            {'baslik': 'Tedarikçiler', 'url': '/stok/tedarikci', 'ikon': 'bi-truck', 'sira': 43},
        ]},

        # ── KALİTE VE İSG ──
        {'baslik': 'Kalite & İSG', 'url': '#', 'ikon': 'bi-shield-check', 'sira': 50, 'alt_menuler': [
            {'baslik': 'Kalite Kontrol', 'url': '/kalite', 'ikon': 'bi-check2-square', 'sira': 51},
            {'baslik': 'Düzeltici Faaliyetler (CAPA)', 'url': '/kalite/capa', 'ikon': 'bi-arrow-repeat', 'sira': 52},
            {'baslik': 'İş Güvenliği (İSG)', 'url': '/isg', 'ikon': 'bi-hard-hat', 'sira': 53},
        ]},

        # ── İNSAN KAYNAKLARI ──
        {'baslik': 'İnsan Kaynakları', 'url': '#', 'ikon': 'bi-people', 'sira': 60, 'alt_menuler': [
            {'baslik': 'Personel Listesi', 'url': '/personel', 'ikon': 'bi-person-badge', 'sira': 61},
            {'baslik': 'İzin Yönetimi', 'url': '/izin', 'ikon': 'bi-calendar2-range', 'sira': 62},
            {'baslik': 'Fazla Mesai', 'url': '/ik/mesai', 'ikon': 'bi-stopwatch', 'sira': 63},
            {'baslik': 'Performans & Eğitim', 'url': '/ik', 'ikon': 'bi-mortarboard', 'sira': 64},
        ]},

        # ── KURUMSAL (CRM, DYS, Finans) ──
        {'baslik': 'Kurumsal', 'url': '#', 'ikon': 'bi-building', 'sira': 70, 'alt_menuler': [
            {'baslik': 'CRM (İş Ortakları)', 'url': '/crm', 'ikon': 'bi-briefcase', 'sira': 71},
            {'baslik': 'Doküman Yönetimi (DYS)', 'url': '/dys', 'ikon': 'bi-folder2-open', 'sira': 72},
            {'baslik': 'Sözleşme Yönetimi', 'url': '/sozlesme', 'ikon': 'bi-file-earmark-text', 'sira': 73},
            {'baslik': 'Finans & Cari', 'url': '/dis-kullanici', 'ikon': 'bi-currency-exchange', 'sira': 74},
        ]},

        # ── GENEL VE ANALİTİK ──
        {'baslik': 'Sistem', 'url': '#', 'ikon': 'bi-laptop', 'sira': 80, 'alt_menuler': [
            {'baslik': 'Enerji Yönetimi', 'url': '/enerji', 'ikon': 'bi-lightning', 'sira': 81},
            {'baslik': 'KPI ve Analitik', 'url': '/analitik', 'ikon': 'bi-graph-up', 'sira': 82},
            {'baslik': 'İç Talepler', 'url': '/talep', 'ikon': 'bi-headset', 'sira': 83},
            {'baslik': 'Duyurular', 'url': '/duyuru', 'ikon': 'bi-megaphone', 'sira': 84},
        ]},
    ]

    for item in harita_data:
        alt_menuler = item.pop('alt_menuler', [])
        
        ana_menu = SiteHaritasi(
            baslik=item['baslik'],
            url=item['url'],
            ikon=item['ikon'],
            sira=item['sira'],
            aktif=True
        )
        db.session.add(ana_menu)
        db.session.flush() # ID almak için

        for alt in alt_menuler:
            alt_menu = SiteHaritasi(
                baslik=alt['baslik'],
                url=alt['url'],
                ikon=alt['ikon'],
                sira=alt['sira'],
                ust_id=ana_menu.id,
                aktif=True
            )
            db.session.add(alt_menu)

    db.session.flush()
    print('  OK\n')
