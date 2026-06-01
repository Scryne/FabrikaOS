"""
FabrikaOS — DYS Demo Verisi (v2)
50+ örnek doküman kaydı (prosedür, talimat, form, rapor, sözleşme)
"""
import random
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.dys import Dokuman
from app.models.kullanici import Kullanici


def seed():
    print('[26/22] Doküman Yönetimi (DYS)...')

    kullanicilar = Kullanici.query.filter_by(aktif=True).all()
    if not kullanicilar:
        return

    dokumanlar = [
        # Prosedürler
        {'baslik': 'ISO 9001 Kalite Yönetim Prosedürü', 'kategori': 'prosedur', 'departman': 'kalite', 'etiketler': ['ISO9001', 'kalite', 'yonetim']},
        {'baslik': 'İş Sağlığı ve Güvenliği Genel Prosedürü', 'kategori': 'prosedur', 'departman': 'isg', 'etiketler': ['ISG', 'guvenlik']},
        {'baslik': 'Acil Durum Eylem Planı', 'kategori': 'prosedur', 'departman': 'isg', 'etiketler': ['acil', 'eylem', 'plan']},
        {'baslik': 'Satın Alma Prosedürü v3', 'kategori': 'prosedur', 'departman': 'muhasebe', 'etiketler': ['satin_alma', 'tedarik']},
        {'baslik': 'Personel İşe Alım Prosedürü', 'kategori': 'prosedur', 'departman': 'ik', 'etiketler': ['ise_alim', 'IK']},
        {'baslik': 'Üretim Kalite Kontrol Prosedürü', 'kategori': 'prosedur', 'departman': 'uretim', 'etiketler': ['kalite', 'kontrol']},
        {'baslik': 'Atık Yönetim Prosedürü', 'kategori': 'prosedur', 'departman': 'isg', 'etiketler': ['atik', 'cevre']},
        {'baslik': 'Bilgi Güvenliği Prosedürü', 'kategori': 'prosedur', 'departman': 'bilgi_islem', 'etiketler': ['bilgi_guvenligi', 'IT']},

        # Talimatlar
        {'baslik': 'Forklift Kullanım Talimatı', 'kategori': 'talimat', 'departman': 'uretim', 'etiketler': ['forklift', 'ekipman']},
        {'baslik': 'Yangın Söndürücü Kullanım Talimatı', 'kategori': 'talimat', 'departman': 'isg', 'etiketler': ['yangin', 'sondurme']},
        {'baslik': 'CNC Tezgah Operasyon Talimatı', 'kategori': 'talimat', 'departman': 'uretim', 'etiketler': ['CNC', 'makine']},
        {'baslik': 'Kimyasal Madde Saklama Talimatı', 'kategori': 'talimat', 'departman': 'isg', 'etiketler': ['kimyasal', 'depolama']},
        {'baslik': 'Torna Tezgahı Bakım Talimatı', 'kategori': 'talimat', 'departman': 'bakim', 'etiketler': ['torna', 'bakim']},
        {'baslik': 'Vinç Operasyon Talimatı', 'kategori': 'talimat', 'departman': 'uretim', 'etiketler': ['vinc', 'kaldirma']},

        # Formlar
        {'baslik': 'İzin Talep Formu (Boş)', 'kategori': 'form', 'departman': 'ik', 'etiketler': ['izin', 'form']},
        {'baslik': 'Staj Başvuru Formu', 'kategori': 'form', 'departman': 'ik', 'etiketler': ['staj', 'basvuru']},
        {'baslik': 'İş Kazası Bildirim Formu', 'kategori': 'form', 'departman': 'isg', 'etiketler': ['kaza', 'bildirim']},
        {'baslik': 'Arıza Bildirim Formu', 'kategori': 'form', 'departman': 'bakim', 'etiketler': ['ariza', 'bildirim']},
        {'baslik': 'Ziyaretçi Kayıt Formu', 'kategori': 'form', 'departman': 'idari', 'etiketler': ['ziyaretci', 'kayit']},
        {'baslik': 'Tedarikçi Değerlendirme Formu', 'kategori': 'form', 'departman': 'kalite', 'etiketler': ['tedarikci', 'degerlendirme']},
        {'baslik': 'Müşteri Memnuniyeti Anketi', 'kategori': 'form', 'departman': 'kalite', 'etiketler': ['musteri', 'anket']},
        {'baslik': 'Zimmet Teslim Tutanağı', 'kategori': 'form', 'departman': 'ik', 'etiketler': ['zimmet', 'tutanak']},

        # Raporlar
        {'baslik': '2026 Q1 Üretim Raporu', 'kategori': 'rapor', 'departman': 'uretim', 'etiketler': ['rapor', 'Q1', '2026']},
        {'baslik': 'Ocak 2026 Enerji Tüketim Raporu', 'kategori': 'rapor', 'departman': 'genel', 'etiketler': ['enerji', 'rapor']},
        {'baslik': '2025 Yıllık İSG İstatistik Raporu', 'kategori': 'rapor', 'departman': 'isg', 'etiketler': ['ISG', 'yillik']},
        {'baslik': 'Nisan 2026 Kalite İstatistikleri', 'kategori': 'rapor', 'departman': 'kalite', 'etiketler': ['kalite', 'istatistik']},
        {'baslik': '2026 Q1 Bakım Performans Raporu', 'kategori': 'rapor', 'departman': 'bakim', 'etiketler': ['bakim', 'performans']},
        {'baslik': '2025 İK Yıllık Değerlendirme', 'kategori': 'rapor', 'departman': 'ik', 'etiketler': ['IK', 'yillik']},
        {'baslik': 'Şubat 2026 OEE Raporu', 'kategori': 'rapor', 'departman': 'uretim', 'etiketler': ['OEE', 'verimlilik']},
        {'baslik': '2025 Mali Yıl Sonu Raporu', 'kategori': 'rapor', 'departman': 'muhasebe', 'etiketler': ['mali', 'yilsonu']},

        # Sözleşmeler
        {'baslik': 'Bakım Hizmet Sözleşmesi — TechServis A.Ş.', 'kategori': 'sozlesme', 'departman': 'genel', 'etiketler': ['sozlesme', 'bakim']},
        {'baslik': 'Güvenlik Hizmet Sözleşmesi 2026', 'kategori': 'sozlesme', 'departman': 'idari', 'etiketler': ['sozlesme', 'guvenlik']},
        {'baslik': 'Temizlik Hizmet Sözleşmesi', 'kategori': 'sozlesme', 'departman': 'idari', 'etiketler': ['sozlesme', 'temizlik']},
        {'baslik': 'IT Altyapı Bakım Sözleşmesi', 'kategori': 'sozlesme', 'departman': 'bilgi_islem', 'etiketler': ['IT', 'sozlesme']},
        {'baslik': 'Yangın Sigorta Poliçesi 2026', 'kategori': 'sozlesme', 'departman': 'muhasebe', 'etiketler': ['sigorta', 'yangin']},

        # Diğer
        {'baslik': 'Organizasyon Şeması 2026', 'kategori': 'diger', 'departman': 'ik', 'etiketler': ['organizasyon', 'sema']},
        {'baslik': 'Tesis Yerleşim Planı', 'kategori': 'diger', 'departman': 'genel', 'etiketler': ['tesis', 'plan']},
        {'baslik': 'Acil Çıkış Yol Haritası', 'kategori': 'diger', 'departman': 'isg', 'etiketler': ['acil', 'cikis']},
        {'baslik': 'Şirket Logo Kullanım Kılavuzu', 'kategori': 'diger', 'departman': 'genel', 'etiketler': ['logo', 'marka']},
        {'baslik': 'Kurumsal Sunum Şablonu', 'kategori': 'diger', 'departman': 'genel', 'etiketler': ['sunum', 'sablon']},
        {'baslik': 'Çalışan El Kitabı 2026', 'kategori': 'diger', 'departman': 'ik', 'etiketler': ['el_kitabi', 'rehber']},
        {'baslik': 'Atölye Güvenlik Panosu İçerikleri', 'kategori': 'diger', 'departman': 'isg', 'etiketler': ['pano', 'guvenlik']},
        {'baslik': 'Kurumsal Kimlik Rehberi', 'kategori': 'diger', 'departman': 'genel', 'etiketler': ['kurumsal', 'kimlik']},
        {'baslik': 'Yemekhane Menü Şablonu', 'kategori': 'diger', 'departman': 'idari', 'etiketler': ['yemekhane', 'menu']},
        {'baslik': 'Servis Güzergah Haritası', 'kategori': 'diger', 'departman': 'idari', 'etiketler': ['servis', 'guzergah']},
        {'baslik': 'Yangın Tatbikat Raporu — Mart 2026', 'kategori': 'rapor', 'departman': 'isg', 'etiketler': ['yangin', 'tatbikat']},
        {'baslik': 'Enerji Verimliliği Eylem Planı', 'kategori': 'diger', 'departman': 'genel', 'etiketler': ['enerji', 'verimlilik']},
        {'baslik': 'KKD Dağıtım Listesi', 'kategori': 'form', 'departman': 'isg', 'etiketler': ['KKD', 'dagitim']},
        {'baslik': 'Eğitim Katılım Formu', 'kategori': 'form', 'departman': 'ik', 'etiketler': ['egitim', 'katilim']},
        {'baslik': 'Risk Değerlendirme Matrisi — Kaynak Atölyesi', 'kategori': 'diger', 'departman': 'isg', 'etiketler': ['risk', 'kaynak']},
    ]

    onay_durumlari = ['taslak', 'onay_bekliyor', 'onaylandi', 'onaylandi', 'onaylandi']
    erisim_seviyeleri = ['herkese_acik', 'herkese_acik', 'herkese_acik', 'departman', 'yonetim']
    dosya_uzantilari = ['.pdf', '.docx', '.xlsx', '.pdf', '.pdf', '.docx', '.pptx', '.pdf']
    mime_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }

    for i, d_data in enumerate(dokumanlar):
        sahip = random.choice(kullanicilar)
        uzanti = random.choice(dosya_uzantilari)
        orijinal_adi = d_data['baslik'].replace(' ', '_').replace('—', '-')[:50] + uzanti
        onay = random.choice(onay_durumlari)

        tarih = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))

        dokuman = Dokuman(
            baslik=d_data['baslik'],
            kategori=d_data['kategori'],
            alt_kategori='',
            etiketler=d_data.get('etiketler', []),
            dosya_adi=f"dys/seed_{i:03d}_{orijinal_adi}",
            orijinal_adi=orijinal_adi,
            mime_type=mime_types.get(uzanti, 'application/pdf'),
            dosya_boyutu=random.randint(50000, 5000000),
            versiyon=random.randint(1, 3),
            sahip_id=sahip.id,
            departman=d_data.get('departman', 'genel'),
            erisim_seviyesi=random.choice(erisim_seviyeleri),
            onay_durumu=onay,
            onaylayan_id=kullanicilar[0].id if onay in ('onaylandi', 'reddedildi') else None,
            onay_tarihi=tarih if onay in ('onaylandi', 'reddedildi') else None,
            indirme_sayisi=random.randint(0, 45),
            aciklama=f'{d_data["baslik"]} ile ilgili detaylı açıklama.',
            olusturma_tarihi=tarih,
        )
        db.session.add(dokuman)

    db.session.flush()
    print('  OK\n')
