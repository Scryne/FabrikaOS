"""
FDYS — Kalite, İSG ve Enerji Modülü Form Tanımları
Faz 4 — Kurumsal Seviye
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, DecimalField, DateField,
                     SelectField, SubmitField, TextAreaField, BooleanField)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import datetime, timezone


# ─── Kalite Kontrol Formları ──────────────────────────────────────────

class HataKaydiForm(FlaskForm):
    makine_id = SelectField('Makine', coerce=int, validators=[Optional()])
    calisan_id = SelectField('Operatör', coerce=int, validators=[Optional()])
    urun_adi = StringField('Ürün Adı / Parça No', validators=[DataRequired(), Length(max=150)])
    parti_no = StringField('Parti / Lot No', validators=[Optional(), Length(max=50)])
    hat = StringField('Üretim Hattı', validators=[Optional(), Length(max=50)])
    tarih = DateField('Hata Tarihi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    
    hata_turu = StringField('Hata Türü / Açıklaması', validators=[DataRequired(), Length(max=100)])
    hata_kategorisi = SelectField('Hata Kategorisi', choices=[
        ('olcusel', 'Ölçüsel Hata'),
        ('yuzey', 'Yüzey Kusuru'),
        ('malzeme', 'Malzeme Hatası'),
        ('montaj', 'Montaj Hatası'),
        ('fonksiyon', 'Fonksiyonel Hata'),
        ('diger', 'Diğer')
    ], validators=[DataRequired()])
    
    hata_kaynagi = SelectField('Olası Hata Kaynağı', choices=[
        ('', '— Belirsiz —'),
        ('iscilik', 'İşçilik / Operatör'),
        ('makine', 'Makine / Ekipman'),
        ('malzeme', 'Hammadde / Malzeme'),
        ('metot', 'Üretim Metodu / Süreç')
    ], validators=[Optional()])
    
    adet = IntegerField('Hatalı Ürün Adedi', validators=[DataRequired(), NumberRange(min=1)])
    fire_orani = DecimalField('Fire Oranı (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    vardiya = SelectField('Vardiya', choices=[
        ('', '— Seçiniz —'),
        ('08_16', '08:00 - 16:00'),
        ('16_24', '16:00 - 24:00'),
        ('24_08', '00:00 - 08:00')
    ], validators=[Optional()])
    
    aksiyon_karari = SelectField('Aksiyon Kararı', choices=[
        ('', '— Bekliyor —'),
        ('hurda', 'Hurdaya Ayrılacak'),
        ('tamir', 'Tamir Edilecek / Yeniden İşlem'),
        ('sartli_kabul', 'Şartlı Kabul')
    ], validators=[Optional()])
    
    aciklama = TextAreaField('Detaylı Açıklama / Ölçüm Değerleri', validators=[Optional()])
    submit = SubmitField('Hata Kaydını Oluştur')


class DuzelticiFaaliyetForm(FlaskForm):
    capa_no = StringField('CAPA / 8D No', validators=[Optional(), Length(max=50)])
    ekip_lideri_id = SelectField('Ekip Lideri', coerce=int, validators=[Optional()])
    
    kok_neden = TextAreaField('Kök Neden Analizi (5 Neden / Ishikawa)', validators=[DataRequired()])
    neden_kategorisi = SelectField('Kök Neden Kategorisi', choices=[
        ('', '— Seçiniz —'),
        ('insan', 'İnsan (Eğitim, Dikkat, Motivasyon)'),
        ('makine', 'Makine (Ayar, Bakım, Aşınma)'),
        ('malzeme', 'Malzeme (Spesifikasyon dışı, hatalı)'),
        ('metot', 'Metot (Yanlış talimat, eksik standart)'),
        ('cevre', 'Çevre (Sıcaklık, Nem, Işıklandırma)')
    ], validators=[Optional()])
    
    gecici_onlem = TextAreaField('Acil / Geçici Önlem (Containment Action)', validators=[Optional()])
    faaliyet = TextAreaField('Kalıcı Düzeltici / Önleyici Faaliyet', validators=[DataRequired()])
    
    sorumlu_id = SelectField('Faaliyet Sorumlusu', coerce=int, validators=[DataRequired()])
    hedef_tarih = DateField('Hedef Tamamlama Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('CAPA Sürecini Başlat')


# ─── Enerji Takip Formları ───────────────────────────────────────────

class EnerjiTuketimForm(FlaskForm):
    makine_id = SelectField('İlgili Makine / Hat', coerce=int, validators=[Optional()])
    departman = StringField('Departman / Tesis Alanı', validators=[Optional(), Length(max=100)])
    
    enerji_turu = SelectField('Enerji Türü', choices=[
        ('elektrik', 'Elektrik (kWh)'),
        ('dogalgaz', 'Doğalgaz (m³)'),
        ('su', 'Su (m³)'),
        ('buhar', 'Buhar (Ton)'),
        ('basincli_hava', 'Basınçlı Hava (m³)')
    ], validators=[DataRequired()])
    
    donem_baslangic = DateField('Dönem Başlangıcı', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    donem_bitis = DateField('Dönem Bitişi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    
    miktar = DecimalField('Tüketim Miktarı', validators=[DataRequired(), NumberRange(min=0.01)])
    birim_fiyat = DecimalField('Birim Fiyat (₺)', validators=[Optional(), NumberRange(min=0)])
    hedef_miktar = DecimalField('Aylık Hedef Miktar', validators=[Optional(), NumberRange(min=0)])
    
    fatura_no = StringField('Fatura / Sayaç Okuma No', validators=[Optional(), Length(max=50)])
    notlar = TextAreaField('Ek Açıklamalar', validators=[Optional()])
    
    submit = SubmitField('Enerji Verisini Kaydet')


# ─── İSG Formları ────────────────────────────────────────────────────

class IsKazasiForm(FlaskForm):
    olay_no = StringField('Olay Kayıt No', validators=[Optional(), Length(max=50)])
    calisan_id = SelectField('Etkilenen Çalışan', coerce=int, validators=[DataRequired()])
    
    tarih = DateField('Olay Tarihi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    vardiya = SelectField('Vardiya', choices=[
        ('', '— Seçiniz —'), ('08_16', '08:00 - 16:00'), ('16_24', '16:00 - 24:00'), ('24_08', '00:00 - 08:00')
    ], validators=[Optional()])
    
    olay_turu = SelectField('Olay Sınıflandırması', choices=[
        ('is_kazasi', 'İş Kazası'),
        ('ramak_kala', 'Ramak Kala Olayı'),
        ('meslek_hastaligi', 'Meslek Hastalığı Şüphesi')
    ], validators=[DataRequired()])
    
    yer = StringField('Olayın Gerçekleştiği Yer', validators=[DataRequired(), Length(max=100)])
    yaralanma_tipi = StringField('Yaralanma Tipi (Örn: Kesik, Kırık, Yanık)', validators=[DataRequired(), Length(max=100)])
    uzuv = StringField('Etkilenen Uzuv / Vücut Bölümü', validators=[Optional(), Length(max=100)])
    
    siddet = SelectField('Şiddet Derecesi', choices=[
        ('hafif', 'Hafif (İlk Yardım)'),
        ('orta', 'Orta (Tıbbi Müdahale)'),
        ('agir', 'Ağır (Uzuv Kaybı / Ağır Yaralanma)'),
        ('olumcul', 'Ölümcül')
    ], validators=[DataRequired()])
    
    kaza_sekli = SelectField('Kaza Şekli', choices=[
        ('', '— Seçiniz —'),
        ('dusme', 'Düşme / Kayma'),
        ('sikisma', 'Sıkışma / Ezilme'),
        ('kesilme', 'Kesilme / Delinme'),
        ('yanik', 'Yanık (Termal / Kimyasal)'),
        ('elektrik', 'Elektrik Çarpması'),
        ('malzeme_dusmesi', 'Malzeme Düşmesi'),
        ('diger', 'Diğer')
    ], validators=[Optional()])
    
    aciklama = TextAreaField('Olay Detayı ve Oluş Şekli', validators=[DataRequired()])
    kok_neden = TextAreaField('Kök Neden Analizi', validators=[Optional()])
    duzeltici_faaliyet = TextAreaField('Alınan Acil Önlemler', validators=[Optional()])
    kayip_gun = IntegerField('Kayıp İş Günü', validators=[Optional(), NumberRange(min=0)], default=0)
    
    submit = SubmitField('Olay Raporunu Kaydet')


class RiskDegerlendirmeForm(FlaskForm):
    bolum = StringField('Bölüm / Tesis Alanı', validators=[DataRequired(), Length(max=100)])
    faaliyet = StringField('Gerçekleştirilen Faaliyet', validators=[Optional(), Length(max=150)])
    
    tehlike = TextAreaField('Tehlike Tanımı', validators=[DataRequired()])
    risk = TextAreaField('Oluşabilecek Risk / Sonuç', validators=[Optional()])
    
    # 5x5 Matris
    olasilik = SelectField('Olasılık (1-5)', choices=[
        ('1', '1 — Çok Küçük (Yılda bir)'), 
        ('2', '2 — Küçük (Ayda bir)'), 
        ('3', '3 — Orta (Haftada bir)'),
        ('4', '4 — Yüksek (Günde bir)'),
        ('5', '5 — Çok Yüksek (Her an)')
    ], validators=[DataRequired()])
    
    siddet = SelectField('Şiddet (1-5)', choices=[
        ('1', '1 — Çok Hafif (İlk yardım)'), 
        ('2', '2 — Hafif (İş günü kaybı yok)'), 
        ('3', '3 — Orta (Hafif yaralanma, iş günü kaybı)'),
        ('4', '4 — Ciddi (Ağır yaralanma, uzuv kaybı)'),
        ('5', '5 — Çok Ciddi (Ölüm)')
    ], validators=[DataRequired()])
    
    mevcut_onlem = TextAreaField('Mevcut Kontrol Önlemleri', validators=[Optional()])
    ek_onlem = TextAreaField('Alınması Gereken Ek Önlemler', validators=[Optional()])
    
    sorumlu = StringField('Sorumlu Kişi / Birim', validators=[Optional(), Length(max=100)])
    hedef_tarih = DateField('Termin Tarihi', format='%Y-%m-%d', validators=[Optional()])
    
    submit = SubmitField('Risk Değerlendirmesini Kaydet')


class IsgEgitimiForm(FlaskForm):
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    
    egitim_kategorisi = SelectField('Eğitim Kategorisi', choices=[
        ('', '— Seçiniz —'),
        ('temel_isg', 'Temel İSG Eğitimi'),
        ('ilkyardim', 'İlk Yardım Eğitimi'),
        ('yangin', 'Yangın Eğitimi'),
        ('yuksekte_calisma', 'Yüksekte Çalışma'),
        ('mesleki', 'Mesleki Yeterlilik (MYK)'),
        ('hijyen', 'Hijyen Eğitimi'),
        ('diger', 'Diğer İşbaşı Eğitimleri')
    ], validators=[Optional()])
    
    egitim_adi = StringField('Eğitim Konusu', validators=[DataRequired(), Length(max=200)])
    egitim_suresi = DecimalField('Eğitim Süresi (Saat)', validators=[Optional(), NumberRange(min=0)])
    
    egitim_tarihi = DateField('Eğitim Tarihi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    gecerlilik_bitis = DateField('Geçerlilik Bitiş Tarihi', format='%Y-%m-%d', validators=[Optional()])
    
    sertifika_no = StringField('Sertifika / Belge No', validators=[Optional(), Length(max=50)])
    egitmen = StringField('Eğitmen / Eğitim Kurumu', validators=[Optional(), Length(max=100)])
    
    submit = SubmitField('Eğitim Kaydını Oluştur')


# ─── İSG Sağlık Muayenesi Formu ─────────────────────────────────────

class SaglikMuayenesiForm(FlaskForm):
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])

    muayene_turu = SelectField('Muayene Türü', choices=[
        ('ise_giris', 'İşe Giriş Muayenesi'),
        ('periyodik', 'Periyodik Muayene'),
        ('ozel', 'Özel Muayene'),
        ('ayrilma', 'İşten Ayrılış Muayenesi')
    ], validators=[DataRequired()])

    muayene_tarihi = DateField('Muayene Tarihi', format='%Y-%m-%d',
                                validators=[DataRequired()],
                                default=lambda: datetime.now(timezone.utc))
    sonraki_muayene_tarihi = DateField('Sonraki Muayene Tarihi', format='%Y-%m-%d',
                                        validators=[Optional()])

    hastane_adi = StringField('Hastane / Kurum Adı', validators=[Optional(), Length(max=200)])
    doktor_adi = StringField('Doktor Adı', validators=[Optional(), Length(max=150)])

    sonuc = SelectField('Muayene Sonucu', choices=[
        ('uygun', 'Uygun — İş için sağlık engeli yok'),
        ('sinirli_uygun', 'Sınırlı Uygun — Kısıtlamalarla çalışabilir'),
        ('uygun_degil', 'Uygun Değil — Bu pozisyonda çalışamaz')
    ], validators=[DataRequired()])

    kisitlamalar = TextAreaField('Kısıtlamalar / Özel Koşullar',
                                 validators=[Optional()],
                                 description='Sınırlı uygun ise kısıtlamaları belirtin.')

    hatirlatma_gun = IntegerField('Hatırlatma (Gün Öncesinden)',
                                   validators=[Optional(), NumberRange(min=1, max=365)],
                                   default=30)
    notlar = TextAreaField('Ek Notlar', validators=[Optional()])

    submit = SubmitField('Muayene Kaydını Kaydet')


# ─── İSG Doküman Formu ──────────────────────────────────────────────

class IsgDokumaniForm(FlaskForm):
    baslik = StringField('Doküman Başlığı', validators=[DataRequired(), Length(max=200)])

    kategori = SelectField('Kategori', choices=[
        ('tutanak', 'Tutanak'),
        ('form', 'Form'),
        ('saha_raporu', 'Saha Raporu'),
        ('talimat', 'Talimat'),
        ('prosedur', 'Prosedür'),
        ('egitim_materyali', 'Eğitim Materyali')
    ], validators=[DataRequired()])

    aciklama = TextAreaField('Açıklama / Doküman Özeti', validators=[Optional()])

    ilgili_bolum = StringField('İlgili Bölüm / Departman',
                                validators=[Optional(), Length(max=100)])

    gecerlilik_tarihi = DateField('Geçerlilik Tarihi', format='%Y-%m-%d',
                                   validators=[Optional()])

    versiyon = IntegerField('Versiyon No', validators=[Optional(), NumberRange(min=1)],
                             default=1)

    onay_durumu = SelectField('Onay Durumu', choices=[
        ('taslak', 'Taslak'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi')
    ], validators=[Optional()])

    submit = SubmitField('Dokümanı Kaydet')
