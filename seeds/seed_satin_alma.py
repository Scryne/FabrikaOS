"""
FabrikaOS — Satın Alma Demo Verisi (v2)
Talepler, Siparişler, Teklif Karşılaştırmaları (Yeni Modül)
"""
import random
from datetime import datetime, timedelta, timezone, date
from app.extensions import db
from app.models.satin_alma import SatinAlmaTalebi, SatinAlmaSiparis, TeklifKarsilastirma
from app.models.stok import Malzeme, Tedarikci
from app.models.kullanici import Kullanici


def seed():
    print('[25/22] Satın Alma...')

    kullanicilar = Kullanici.query.filter_by(aktif=True).all()
    satin_almaci = Kullanici.query.filter_by(kullanici_adi='mustafa.sahin').first() or Kullanici.query.first()
    yonetici = Kullanici.query.filter_by(kullanici_adi='admin').first() or Kullanici.query.first()
    malzemeler = Malzeme.query.all()
    tedarikciler = Tedarikci.query.all()
    bugun = datetime.now(timezone.utc)

    if not malzemeler or not tedarikciler:
        print("  Uyarı: Malzeme veya Tedarikçi yok, atlanıyor.")
        return

    # ── SATIN ALMA TALEPLERİ (15 adet) ──
    talepler = []
    durumlar = ['bekliyor', 'onaylandi', 'reddedildi', 'siparis_verildi', 'teslim_alindi', 'iptal']
    weights = [0.1, 0.2, 0.1, 0.3, 0.2, 0.1]

    for i in range(15):
        m = random.choice(malzemeler)
        isteyen = random.choice(kullanicilar)
        durum = random.choices(durumlar, weights=weights)[0]
        miktar = random.randint(10, 200) if m.birim != 'adet' else random.randint(2, 50)
        
        olusturma = bugun - timedelta(days=random.randint(1, 45))
        onay_tarihi = olusturma + timedelta(days=random.randint(1, 3)) if durum in ['onaylandi', 'siparis_verildi', 'teslim_alindi'] else None

        talep = SatinAlmaTalebi(
            talep_no=f"SA-{bugun.year}-{i+1000}",
            talep_eden_id=isteyen.id,
            malzeme_hizmet='malzeme',
            kalem_adi=m.ad,
            miktar=miktar,
            birim='adet',
            tahmini_birim_fiyat=m.birim_fiyat,
            aciklama='Standart sipariş',
            gerekce='Stok seviyesi kritik.' if m.mevcut_miktar <= m.minimum_stok else 'Aylık planlı sarfiyat.',
            aciliyet='normal',
            durum=durum,
            onaylayan_id=yonetici.id if onay_tarihi else None,
            onay_tarihi=onay_tarihi,
            tedarikci_id=m.tedarikci_id,
            departman='Üretim',
            istenen_teslim_tarihi=date(olusturma.year, olusturma.month, olusturma.day) + timedelta(days=15),
            olusturma_tarihi=olusturma
        )
        db.session.add(talep)
        talepler.append(talep)

    db.session.flush()

    # ── TEKLİF KARŞILAŞTIRMALARI (5 adet) ──
    teklif_talepleri = [t for t in talepler if t.durum in ['onaylandi', 'siparis_verildi', 'teslim_alindi']]
    karsilastirmalar = []
    
    for i, t in enumerate(teklif_talepleri[:5]):
        teds = random.sample(tedarikciler, k=min(3, len(tedarikciler)))
        
        fiyat_1 = float(t.tahmini_birim_fiyat or 100) * random.uniform(0.9, 1.1)
        fiyat_2 = float(t.tahmini_birim_fiyat or 100) * random.uniform(0.9, 1.1)
        fiyat_3 = float(t.tahmini_birim_fiyat or 100) * random.uniform(0.9, 1.1)
        
        secilen = 1 if fiyat_1 <= fiyat_2 and fiyat_1 <= fiyat_3 else 2 if fiyat_2 <= fiyat_1 and fiyat_2 <= fiyat_3 else 3

        if len(teds) > 0:
            tk1 = TeklifKarsilastirma(
                talep_id=t.id,
                tedarikci_id=teds[0].id,
                birim_fiyat=fiyat_1,
                toplam_fiyat=fiyat_1 * float(t.miktar),
                teslimat_suresi=random.randint(3, 15),
                garanti_suresi=random.randint(6, 24),
                notlar='Uygun teklif' if secilen == 1 else '',
                secildi_mi=secilen == 1,
                olusturma_tarihi=t.onay_tarihi + timedelta(days=1)
            )
            db.session.add(tk1)
            karsilastirmalar.append(tk1)

        if len(teds) > 1:
            tk2 = TeklifKarsilastirma(
                talep_id=t.id,
                tedarikci_id=teds[1].id,
                birim_fiyat=fiyat_2,
                toplam_fiyat=fiyat_2 * float(t.miktar),
                teslimat_suresi=random.randint(3, 15),
                garanti_suresi=random.randint(6, 24),
                notlar='Uygun teklif' if secilen == 2 else '',
                secildi_mi=secilen == 2,
                olusturma_tarihi=t.onay_tarihi + timedelta(days=1)
            )
            db.session.add(tk2)
            karsilastirmalar.append(tk2)

        if len(teds) > 2:
            tk3 = TeklifKarsilastirma(
                talep_id=t.id,
                tedarikci_id=teds[2].id,
                birim_fiyat=fiyat_3,
                toplam_fiyat=fiyat_3 * float(t.miktar),
                teslimat_suresi=random.randint(3, 15),
                garanti_suresi=random.randint(6, 24),
                notlar='Uygun teklif' if secilen == 3 else '',
                secildi_mi=secilen == 3,
                olusturma_tarihi=t.onay_tarihi + timedelta(days=1)
            )
            db.session.add(tk3)
            karsilastirmalar.append(tk3)

    db.session.flush()

    # ── SATIN ALMA SİPARİŞLERİ (10 adet) ──
    # Bazıları teklif karşılaştırmasından, bazıları direkt
    siparis_talepleri = [t for t in talepler if t.durum in ['siparis_verildi', 'teslim_alindi']]
    
    for i, t in enumerate(siparis_talepleri):
        ted = t.tedarikci or random.choice(tedarikciler)
        s_durum = 'teslim_alindi' if t.durum == 'teslim_alindi' else 'siparis_verildi'
        
        olusturma = t.onay_tarihi + timedelta(days=2)
        teslim_tarihi = olusturma + timedelta(days=ted.ortalama_teslimat_gun or 5) if s_durum == 'teslim_alindi' else None

        birim_fiy = float(t.tahmini_birim_fiyat or 100)
        siparis = SatinAlmaSiparis(
            siparis_no=f"SAS-{bugun.year}-{i+5000}",
            talep_id=t.id,
            tedarikci_id=ted.id,
            birim_fiyat=birim_fiy,
            miktar=t.miktar,
            toplam_tutar=birim_fiy * float(t.miktar),
            kdv_orani=20,
            genel_toplam=(birim_fiy * float(t.miktar)) * 1.2,
            siparis_tarihi=olusturma,
            beklenen_teslim=date(olusturma.year, olusturma.month, olusturma.day) + timedelta(days=int(ted.ortalama_teslimat_gun or 5)),
            gercek_teslim=date(teslim_tarihi.year, teslim_tarihi.month, teslim_tarihi.day) if teslim_tarihi else None,
            durum=s_durum,
            olusturan_id=satin_almaci.id,
            teslim_alan_id=yonetici.id if s_durum == 'teslim_alindi' else None,
        )
        db.session.add(siparis)

    db.session.flush()
    print('  OK\n')
