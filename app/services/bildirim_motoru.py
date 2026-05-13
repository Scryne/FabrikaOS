"""
FDYS — Merkezi Bildirim ve Uyarı Motoru (Faz 3 — Tam Implementasyon)

Tüm modüllerden gelen verileri izler ve belirlenen koşullar
sağlandığında ilgili rollere anlık uyarı gönderir.

12 tetikleyici kural tanımlanmıştır.
"""

from app.extensions import db
from app.models.bildirim import Bildirim


class BildirimMotoru:
    """Merkezi bildirim servisi."""

    # Tetikleyici kurallar
    KURALLAR = {
        'stok_dusuk': {'seviye': 'uyari', 'rol': 'yonetici'},
        'ariza_bildirimi': {'seviye': 'kritik', 'rol': ['teknisyen', 'yonetici']},
        'oee_dusuk': {'seviye': 'uyari', 'rol': 'yonetici'},
        'bakim_yaklasıyor': {'seviye': 'bilgi', 'rol': 'teknisyen'},
        'hata_orani_yuksek': {'seviye': 'uyari', 'rol': 'yonetici'},
        'egitim_suresi_doldu': {'seviye': 'uyari', 'rol': 'yonetici'},
        'izin_bekliyor': {'seviye': 'bilgi', 'rol': 'yonetici'},
        'enerji_hedef': {'seviye': 'bilgi', 'rol': 'yonetici'},
        'is_kazasi': {'seviye': 'kritik', 'rol': 'yonetici'},
        'mudahale_gecikmesi': {'seviye': 'uyari', 'rol': 'yonetici'},
        'uretim_dusuk': {'seviye': 'uyari', 'rol': 'yonetici'},
        'hesap_kilidi': {'seviye': 'guvenlik', 'rol': 'yonetici'},
    }

    def bildirim_olustur(self, kullanici_id, baslik, mesaj, seviye='bilgi', modul=None, url=None):
        """Yeni bildirim oluşturur, veritabanına kaydeder ve SocketIO ile anında iter."""
        bildirim = Bildirim(
            kullanici_id=kullanici_id,
            baslik=baslik,
            mesaj=mesaj,
            seviye=seviye,
            modul=modul,
            url=url
        )
        db.session.add(bildirim)
        db.session.commit()

        # SocketIO ile anlık gönderim
        try:
            from app.extensions import socketio
            socketio.emit('yeni_bildirim', {
                'id': bildirim.id,
                'baslik': bildirim.baslik,
                'mesaj': bildirim.mesaj,
                'seviye': bildirim.seviye,
                'url': bildirim.url,
                'tarih': bildirim.olusturma_tarihi.strftime('%d.%m.%Y %H:%M')
            }, room=f'user_{kullanici_id}')
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"SocketIO bildirim gönderim hatası: {e}")

        # Kritik bildirimlerde otomatik e-posta gönderimi
        if seviye == 'kritik':
            try:
                from app.services.eposta_servisi import eposta_servisi
                eposta_servisi.kritik_uyari_gonder(baslik, mesaj, modul or 'sistem')
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"E-posta bildirim hatası: {e}")

        return bildirim

    def _hedef_kullanicilari_bul(self, roller):
        """Belirtilen rollerdeki aktif kullanıcıları bulur."""
        from app.models.kullanici import Kullanici
        if isinstance(roller, str):
            roller = [roller]
        return Kullanici.query.filter(
            Kullanici.rol.in_(roller),
            Kullanici.aktif == True
        ).all()

    def stok_kontrol(self, malzeme):
        """Stok seviyesi minimum eşiğin altına düştüğünde uyarı gönderir."""
        if malzeme.mevcut_miktar <= malzeme.minimum_stok:
            kural = self.KURALLAR['stok_dusuk']
            hedefler = self._hedef_kullanicilari_bul(kural['rol'])
            for k in hedefler:
                self.bildirim_olustur(
                    kullanici_id=k.id,
                    baslik="Kritik Stok Uyarısı",
                    mesaj=f"{malzeme.ad} — Mevcut: {malzeme.mevcut_miktar} {malzeme.birim} (Min: {malzeme.minimum_stok})",
                    seviye=kural['seviye'],
                    modul="stok",
                    url="/stok/"
                )

    def oee_kontrol(self, makine, oee_degeri):
        """OEE hedefin %10 altına düştüğünde uyarı gönderir."""
        hedef = float(makine.hedef_oee)
        if float(oee_degeri) < hedef * 0.9:
            kural = self.KURALLAR['oee_dusuk']
            hedefler = self._hedef_kullanicilari_bul(kural['rol'])
            for k in hedefler:
                self.bildirim_olustur(
                    kullanici_id=k.id,
                    baslik="OEE Düşük Uyarısı",
                    mesaj=f"{makine.ad} — OEE: %{oee_degeri} (Hedef: %{hedef})",
                    seviye=kural['seviye'],
                    modul="makine",
                    url=f"/makine/detay/{makine.id}"
                )

    def ariza_bildirim(self, ariza_kaydi):
        """Yeni arıza bildiriminde teknisyen ve yöneticiye bildirim gönderir."""
        kural = self.KURALLAR['ariza_bildirimi']
        seviye = 'kritik' if ariza_kaydi.oncelik in ('kritik', 'yuksek') else kural['seviye']
        hedefler = self._hedef_kullanicilari_bul(kural['rol'])
        for k in hedefler:
            self.bildirim_olustur(
                kullanici_id=k.id,
                baslik="Yeni Arıza Bildirimi",
                mesaj=f"{ariza_kaydi.makine.ad} — {ariza_kaydi.ariza_turu} ({ariza_kaydi.oncelik})",
                seviye=seviye,
                modul="makine",
                url=f"/makine/detay/{ariza_kaydi.makine_id}"
            )

    def bakim_yaklasiyor_kontrol(self):
        """Bakım tarihi yaklaşan makineler için bildirim gönderir."""
        from app.models.makine import Makine
        from datetime import timedelta, datetime, timezone

        makineler = Makine.query.filter_by(aktif=True).all()
        kural = self.KURALLAR['bakim_yaklasıyor']
        hedefler = self._hedef_kullanicilari_bul(kural['rol'])

        for m in makineler:
            sonraki = m.sonraki_bakim_tarihi
            if sonraki:
                kalan_gun = (sonraki - datetime.now(timezone.utc).date()).days
                if 0 < kalan_gun <= 7:
                    for k in hedefler:
                        self.bildirim_olustur(
                            kullanici_id=k.id,
                            baslik="Bakım Hatırlatması",
                            mesaj=f"{m.ad} — Periyodik bakım {kalan_gun} gün sonra.",
                            seviye=kural['seviye'],
                            modul="makine",
                            url=f"/makine/detay/{m.id}"
                        )

    def is_kazasi_bildirim(self, kaza):
        """İş kazası bildiriminde yöneticilere acil uyarı gönderir."""
        kural = self.KURALLAR['is_kazasi']
        hedefler = self._hedef_kullanicilari_bul(kural['rol'])
        for k in hedefler:
            self.bildirim_olustur(
                kullanici_id=k.id,
                baslik="ACİL: İş Kazası Bildirimi!",
                mesaj=f"{kaza.calisan.ad_soyad} — {kaza.yer} bölgesinde {kaza.siddet} seviye olay.",
                seviye=kural['seviye'],
                modul="isg",
                url="/isg/"
            )

    def egitim_suresi_kontrol(self):
        """Süresi dolan İSG eğitimleri için bildirim gönderir."""
        from app.models.isg import IsgEgitimi
        from datetime import datetime, timezone

        kural = self.KURALLAR['egitim_suresi_doldu']
        hedefler = self._hedef_kullanicilari_bul(kural['rol'])

        suresi_dolanlar = IsgEgitimi.query.filter(
            IsgEgitimi.gecerlilik_bitis < datetime.now(timezone.utc).date(),
            IsgEgitimi.durum == 'gecerli'
        ).all()

        if suresi_dolanlar:
            for k in hedefler:
                self.bildirim_olustur(
                    kullanici_id=k.id,
                    baslik="İSG Eğitim Süresi Doldu",
                    mesaj=f"{len(suresi_dolanlar)} adet İSG eğitiminin süresi dolmuştur. Eğitim yenilenmelidir.",
                    seviye=kural['seviye'],
                    modul="isg",
                    url="/isg/egitimler"
                )


bildirim_motoru = BildirimMotoru()
