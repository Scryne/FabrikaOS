"""
FDYS — İSG Risk Puanlama Algoritması
Faz 4 — Kurumsal Seviye (5x5 Matris)

Risk Puanı = Olasılık × Şiddet
1-6   : Düşük (Kabul Edilebilir)
8-12  : Orta (Dikkate Değer)
15-20 : Yüksek (Önemli)
25    : Kritik (Kabul Edilemez)
"""


class ISGRiskPuani:
    """İSG risk değerlendirme motoru (5x5 Matris)."""

    def hesapla(self, olasilik, siddet):
        """Risk puanı ve seviyesini hesaplar."""
        puan = olasilik * siddet
        
        if puan <= 6:
            seviye = 'dusuk'
            renk = 'success'
        elif puan <= 12:
            seviye = 'orta'
            renk = 'warning'
        elif puan <= 20:
            seviye = 'yuksek'
            renk = 'danger'
        else:
            seviye = 'kritik'
            renk = 'dark'
            
        return {'puan': puan, 'seviye': seviye, 'renk': renk}

    def bolum_risk_ozeti(self, risk_degerlendirmeler):
        """Bir bölümün toplam risk profilini çıkarır."""
        if not risk_degerlendirmeler:
            return {'toplam': 0, 'kritik': 0, 'yuksek': 0, 'orta': 0, 'dusuk': 0, 'ortalama_puan': 0}

        kritik = sum(1 for r in risk_degerlendirmeler if r.risk_seviyesi == 'kritik')
        yuksek = sum(1 for r in risk_degerlendirmeler if r.risk_seviyesi == 'yuksek')
        orta = sum(1 for r in risk_degerlendirmeler if r.risk_seviyesi == 'orta')
        dusuk = sum(1 for r in risk_degerlendirmeler if r.risk_seviyesi == 'dusuk')
        toplam = len(risk_degerlendirmeler)
        ortalama = sum(r.risk_puani for r in risk_degerlendirmeler if r.risk_puani) / toplam

        return {
            'toplam': toplam,
            'kritik': kritik,
            'yuksek': yuksek,
            'orta': orta,
            'dusuk': dusuk,
            'ortalama_puan': round(ortalama, 1)
        }


isg_risk_puani = ISGRiskPuani()
