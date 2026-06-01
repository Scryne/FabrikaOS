"""
FDYS — Talep & İş Takip Servisi
Faz 4 — Talep yönetimi, yönlendirme, SMS/e-posta bilgilendirme ve raporlama

Fonksiyonlar:
    - Talep no üretimi
    - Dashboard istatistikleri
    - Talep oluşturma, durum güncelleme, yönlendirme
    - SMS/e-posta bildirim tetikleme
    - Talep raporları ve analizler
    - İş emri dönüşümü
    - Borç/tahsilat yönetimi
"""

import logging
from datetime import datetime, timezone, timedelta, date
from sqlalchemy import func, extract, and_, or_, case

from app.extensions import db
from app.models.talep import Talep, TalepGecmisi
from app.models.dis_kullanici import DisKullanici, Borc, Tahsilat

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# TALEP NO ÜRETİMİ
# ──────────────────────────────────────────────

def sonraki_talep_no():
    """Otomatik talep numarası üretir: TLP-YYYY-NNNNN"""
    yil = datetime.now().year
    prefix = f'TLP-{yil}-'

    son = (
        db.session.query(func.max(Talep.talep_no))
        .filter(Talep.talep_no.like(f'{prefix}%'))
        .scalar()
    )

    if son:
        try:
            son_sayi = int(son.split('-')[-1])
            return f'{prefix}{son_sayi + 1:05d}'
        except (ValueError, IndexError):
            pass

    return f'{prefix}00001'


# ──────────────────────────────────────────────
# DASHBOARD İSTATİSTİKLERİ
# ──────────────────────────────────────────────

def talep_dashboard_istatistik():
    """Talep dashboard'u için tüm istatistikleri döner."""
    bugun = date.today()
    bu_ay_baslangic = bugun.replace(day=1)
    onceki_ay_bitis = bu_ay_baslangic - timedelta(days=1)
    onceki_ay_baslangic = onceki_ay_bitis.replace(day=1)

    # Toplam talepler (durum bazlı)
    toplam = Talep.query.filter_by(aktif=True).count()
    acik = Talep.query.filter(
        Talep.aktif == True,
        Talep.durum.in_([Talep.DURUM_ACIK, Talep.DURUM_YONLENDIRILDI, Talep.DURUM_DEVAM])
    ).count()
    tamamlanan = Talep.query.filter(
        Talep.aktif == True,
        Talep.durum.in_([Talep.DURUM_TAMAMLANDI, Talep.DURUM_KAPANDI])
    ).count()
    reddedilen = Talep.query.filter(
        Talep.aktif == True,
        Talep.durum == Talep.DURUM_REDDEDILDI
    ).count()

    # Bu ay oluşturulan
    bu_ay_toplam = Talep.query.filter(
        Talep.aktif == True,
        func.date(Talep.olusturma_tarihi) >= bu_ay_baslangic
    ).count()

    # Kategori dağılımı
    kategori_dagilimi = (
        db.session.query(
            Talep.kategori,
            func.count(Talep.id)
        )
        .filter(Talep.aktif == True)
        .group_by(Talep.kategori)
        .all()
    )

    # Öncelik dağılımı
    oncelik_dagilimi = (
        db.session.query(
            Talep.oncelik,
            func.count(Talep.id)
        )
        .filter(Talep.aktif == True)
        .group_by(Talep.oncelik)
        .all()
    )

    # Durum dağılımı
    durum_dagilimi = (
        db.session.query(
            Talep.durum,
            func.count(Talep.id)
        )
        .filter(Talep.aktif == True)
        .group_by(Talep.durum)
        .all()
    )

    # Son 10 talep
    son_talepler = (
        Talep.query
        .filter_by(aktif=True)
        .order_by(Talep.olusturma_tarihi.desc())
        .limit(10)
        .all()
    )

    # Acil talepler
    acil_talepler = (
        Talep.query
        .filter(
            Talep.aktif == True,
            Talep.oncelik == Talep.ONCELIK_ACIL,
            Talep.durum.in_([Talep.DURUM_ACIK, Talep.DURUM_YONLENDIRILDI, Talep.DURUM_DEVAM])
        )
        .order_by(Talep.olusturma_tarihi.desc())
        .all()
    )

    # Ortalama çözüm süresi (dakika)
    tamamlanmis_talepler = Talep.query.filter(
        Talep.aktif == True,
        Talep.kapanma_tarihi.isnot(None)
    ).all()
    toplam_sure = sum(t.cozum_suresi_dk or 0 for t in tamamlanmis_talepler)
    ort_cozum_suresi = round(toplam_sure / len(tamamlanmis_talepler), 1) if tamamlanmis_talepler else 0

    # Ortalama memnuniyet
    ort_memnuniyet = (
        db.session.query(func.avg(Talep.memnuniyet_puani))
        .filter(Talep.aktif == True, Talep.memnuniyet_puani.isnot(None))
        .scalar()
    )

    return {
        'toplam': toplam,
        'acik': acik,
        'tamamlanan': tamamlanan,
        'reddedilen': reddedilen,
        'bu_ay_toplam': bu_ay_toplam,
        'kategori_dagilimi': [(Talep.KATEGORILER.get(k, k), v) for k, v in kategori_dagilimi],
        'oncelik_dagilimi': [(Talep.ONCELIKLER.get(k, k), v) for k, v in oncelik_dagilimi],
        'durum_dagilimi': [(Talep.DURUMLAR.get(k, k), v) for k, v in durum_dagilimi],
        'son_talepler': son_talepler,
        'acil_talepler': acil_talepler,
        'ort_cozum_suresi_dk': ort_cozum_suresi,
        'ort_memnuniyet': round(float(ort_memnuniyet), 1) if ort_memnuniyet else 0,
    }


# ──────────────────────────────────────────────
# TALEP İŞLEMLERİ
# ──────────────────────────────────────────────

def talep_olustur(talep, yapan_id=None, yapan_adi=None):
    """Yeni talep oluşturur ve geçmiş kaydı ekler."""
    if not talep.talep_no:
        talep.talep_no = sonraki_talep_no()

    db.session.add(talep)
    db.session.flush()

    # Oluşturma geçmişi
    gecmis = TalepGecmisi(
        talep_id=talep.id,
        islem_turu=TalepGecmisi.ISLEM_OLUSTURMA,
        yapan_id=yapan_id,
        yapan_adi=yapan_adi or talep.talep_eden_adi,
        aciklama=f'Talep oluşturuldu: {talep.baslik}',
        yeni_durum=talep.durum,
    )
    db.session.add(gecmis)
    db.session.commit()

    logger.info(f'Talep oluşturuldu: {talep.talep_no}')
    return talep


def durum_guncelle(talep_id, yeni_durum, yapan_id=None, yapan_adi=None, aciklama=None):
    """Talep durumunu günceller, geçiş geçerliliğini kontrol eder."""
    talep = db.session.get(Talep, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'

    if not talep.gecis_gecerli_mi(yeni_durum):
        return None, f"'{talep.durum_adi}' → '{Talep.DURUMLAR.get(yeni_durum, yeni_durum)}' geçişi geçerli değil."

    eski_durum = talep.durum
    talep.durum = yeni_durum

    # Kapanma zamanı
    if yeni_durum in (Talep.DURUM_KAPANDI, Talep.DURUM_TAMAMLANDI):
        talep.kapanma_tarihi = datetime.now(timezone.utc)

    gecmis = TalepGecmisi(
        talep_id=talep.id,
        islem_turu=TalepGecmisi.ISLEM_DURUM_DEGISIKLIGI,
        yapan_id=yapan_id,
        yapan_adi=yapan_adi,
        aciklama=aciklama or f'Durum değişikliği: {Talep.DURUMLAR.get(eski_durum, eski_durum)} → {Talep.DURUMLAR.get(yeni_durum, yeni_durum)}',
        eski_durum=eski_durum,
        yeni_durum=yeni_durum,
    )
    db.session.add(gecmis)
    db.session.commit()

    logger.info(f'Talep {talep.talep_no}: {eski_durum} → {yeni_durum}')
    return talep, None


def talep_yonlendir(talep_id, departman, atanan_id=None, yapan_id=None, yapan_adi=None, aciklama=None):
    """Talebi bir departman/kişiye yönlendirir."""
    talep = db.session.get(Talep, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'

    talep.atanan_departman = departman
    talep.atanan_id = atanan_id

    if talep.durum == Talep.DURUM_ACIK:
        eski_durum = talep.durum
        talep.durum = Talep.DURUM_YONLENDIRILDI

        gecmis = TalepGecmisi(
            talep_id=talep.id,
            islem_turu=TalepGecmisi.ISLEM_YONLENDIRME,
            yapan_id=yapan_id,
            yapan_adi=yapan_adi,
            aciklama=aciklama or f'Talep {Talep.DEPARTMANLAR.get(departman, departman)} departmanına yönlendirildi.',
            eski_durum=eski_durum,
            yeni_durum=Talep.DURUM_YONLENDIRILDI,
        )
        db.session.add(gecmis)
    else:
        gecmis = TalepGecmisi(
            talep_id=talep.id,
            islem_turu=TalepGecmisi.ISLEM_YONLENDIRME,
            yapan_id=yapan_id,
            yapan_adi=yapan_adi,
            aciklama=aciklama or f'Talep {Talep.DEPARTMANLAR.get(departman, departman)} departmanına yeniden yönlendirildi.',
        )
        db.session.add(gecmis)

    db.session.commit()
    logger.info(f'Talep {talep.talep_no} yönlendirildi: {departman}')
    return talep, None


def talep_yorum_ekle(talep_id, yorum, yapan_id=None, yapan_adi=None):
    """Talebe yorum/not ekler."""
    talep = db.session.get(Talep, talep_id)
    if not talep:
        return None

    gecmis = TalepGecmisi(
        talep_id=talep.id,
        islem_turu=TalepGecmisi.ISLEM_YORUM,
        yapan_id=yapan_id,
        yapan_adi=yapan_adi,
        aciklama=yorum,
    )
    db.session.add(gecmis)
    db.session.commit()
    return gecmis


# ──────────────────────────────────────────────
# BORÇ / TAHSİLAT İŞLEMLERİ
# ──────────────────────────────────────────────

def borc_olustur(ilgili_tip, ilgili_id, borc_turu, tutar, aciklama=None, son_odeme=None, donem=None):
    """Yeni borç kaydı oluşturur."""
    borc = Borc(
        ilgili_tip=ilgili_tip,
        ilgili_id=ilgili_id,
        borc_turu=borc_turu,
        tutar=tutar,
        aciklama=aciklama,
        son_odeme_tarihi=son_odeme,
        donem=donem,
    )
    db.session.add(borc)
    db.session.commit()
    return borc


def tahsilat_kaydet(borc_id, tutar, odeme_turu, makbuz_no=None, aciklama=None, kaydeden_id=None):
    """Borç için tahsilat (ödeme) kaydeder ve borç durumunu günceller."""
    borc = db.session.get(Borc, borc_id)
    if not borc:
        return None, 'Borç kaydı bulunamadı.'

    tahsilat = Tahsilat(
        borc_id=borc_id,
        tutar=tutar,
        odeme_turu=odeme_turu,
        makbuz_no=makbuz_no,
        aciklama=aciklama,
        kaydeden_id=kaydeden_id,
    )
    db.session.add(tahsilat)

    # Borç durumunu güncelle
    borc.odenen_tutar = float(borc.odenen_tutar) + float(tutar)
    borc.durum_guncelle()

    db.session.commit()
    return tahsilat, None


def kisi_borc_ozeti(ilgili_tip, ilgili_id):
    """Bir ortak veya firmanın borç özetini döner."""
    borclar = Borc.query.filter_by(
        ilgili_tip=ilgili_tip,
        ilgili_id=ilgili_id,
        aktif=True
    ).order_by(Borc.olusturma_tarihi.desc()).all()

    toplam_borc = sum(float(b.tutar) for b in borclar)
    toplam_odeme = sum(float(b.odenen_tutar) for b in borclar)
    toplam_kalan = toplam_borc - toplam_odeme
    geciken_borc = sum(float(b.kalan_tutar) for b in borclar if b.durum == Borc.DURUM_GECIKTI)

    return {
        'borclar': borclar,
        'toplam_borc': toplam_borc,
        'toplam_odeme': toplam_odeme,
        'toplam_kalan': toplam_kalan,
        'geciken_borc': geciken_borc,
        'borc_sayisi': len(borclar),
    }


# ──────────────────────────────────────────────
# DIŞ KULLANICI İŞLEMLERİ
# ──────────────────────────────────────────────

def dis_kullanici_olustur(kullanici_adi, sifre, ad_soyad, ortak_id=None, firma_id=None,
                           telefon=None, eposta=None):
    """Yeni dış kullanıcı oluşturur."""
    if DisKullanici.query.filter_by(kullanici_adi=kullanici_adi).first():
        return None, 'Bu kullanıcı adı zaten kullanılıyor.'

    dk = DisKullanici(
        kullanici_adi=kullanici_adi,
        ad_soyad=ad_soyad,
        ortak_id=ortak_id,
        firma_id=firma_id,
        telefon=telefon,
        eposta=eposta,
        gecici_sifre=True,
    )
    dk.sifre_belirle(sifre)
    db.session.add(dk)
    db.session.commit()
    return dk, None


def dis_panel_dashboard(dis_kullanici):
    """Dış kullanıcı panel dashboard istatistikleri."""
    # Bağlı olduğu ortak/firma üzerinden talepler
    talepler = Talep.query.filter(
        Talep.aktif == True,
        or_(
            and_(Talep.talep_eden_tip == 'dis_kullanici', Talep.talep_eden_id == dis_kullanici.id),
            and_(Talep.talep_eden_tip == 'ortak', Talep.talep_eden_id == dis_kullanici.ortak_id) if dis_kullanici.ortak_id else False,
            and_(Talep.talep_eden_tip == 'firma', Talep.talep_eden_id == dis_kullanici.firma_id) if dis_kullanici.firma_id else False,
        )
    ).order_by(Talep.olusturma_tarihi.desc()).all()

    acik_talep = len([t for t in talepler if t.durum in (Talep.DURUM_ACIK, Talep.DURUM_YONLENDIRILDI, Talep.DURUM_DEVAM)])
    tamamlanan_talep = len([t for t in talepler if t.durum in (Talep.DURUM_TAMAMLANDI, Talep.DURUM_KAPANDI)])

    # Borçlar
    borc_ozeti = {'toplam_kalan': 0, 'geciken_borc': 0, 'borclar': []}
    if dis_kullanici.ortak_id:
        borc_ozeti = kisi_borc_ozeti('ortak', dis_kullanici.ortak_id)
    elif dis_kullanici.firma_id:
        borc_ozeti = kisi_borc_ozeti('firma', dis_kullanici.firma_id)

    return {
        'talepler': talepler[:5],
        'toplam_talep': len(talepler),
        'acik_talep': acik_talep,
        'tamamlanan_talep': tamamlanan_talep,
        'borc_ozeti': borc_ozeti,
    }


# ──────────────────────────────────────────────
# RAPOR
# ──────────────────────────────────────────────

def talep_rapor(filtreler=None):
    """Talep raporları."""
    filtreler = filtreler or {}
    sorgu = Talep.query.filter_by(aktif=True)

    if filtreler.get('durum'):
        sorgu = sorgu.filter(Talep.durum == filtreler['durum'])
    if filtreler.get('kategori'):
        sorgu = sorgu.filter(Talep.kategori == filtreler['kategori'])
    if filtreler.get('oncelik'):
        sorgu = sorgu.filter(Talep.oncelik == filtreler['oncelik'])
    if filtreler.get('baslangic'):
        sorgu = sorgu.filter(func.date(Talep.olusturma_tarihi) >= filtreler['baslangic'])
    if filtreler.get('bitis'):
        sorgu = sorgu.filter(func.date(Talep.olusturma_tarihi) <= filtreler['bitis'])

    return sorgu.order_by(Talep.olusturma_tarihi.desc()).all()
