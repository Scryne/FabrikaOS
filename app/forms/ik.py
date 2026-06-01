"""
FDYS — İK (İnsan Kaynakları) Formları
Faz 1 — Tam Genişletme

Savunma/Tutanak, Fazla Mesai, Sertifika, Maaş Skalası,
Zimmet ve Giriş/Çıkış Evrak formlarını içerir.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, SelectField, SubmitField, DecimalField,
    TextAreaField, TimeField, IntegerField, BooleanField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import datetime, timezone


class SavunmaTutanakForm(FlaskForm):
    """Savunma, tutanak, uyarı, ihtar, disiplin kurulu formu."""
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    tur = SelectField('Tür', choices=[
        ('savunma', 'Savunma'),
        ('tutanak', 'Tutanak'),
        ('uyari', 'Uyarı'),
        ('ihtar', 'İhtar'),
        ('disiplin_kurulu', 'Disiplin Kurulu'),
    ], validators=[DataRequired()])
    konu = StringField('Konu', validators=[DataRequired(), Length(min=3, max=200)])
    icerik = TextAreaField('İçerik', validators=[DataRequired(), Length(min=10)])
    karar = TextAreaField('Karar', validators=[Optional()])
    karar_tarihi = DateField('Karar Tarihi', format='%Y-%m-%d', validators=[Optional()])
    durum = SelectField('Durum', choices=[
        ('acik', 'Açık'),
        ('kapatildi', 'Kapatıldı'),
        ('itiraz_edildi', 'İtiraz Edildi'),
    ], default='acik')
    tanik_ad_soyad = StringField('Tanık Ad Soyad', validators=[Optional(), Length(max=100)])
    tanik_sicil_no = StringField('Tanık Sicil No', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Kaydet')


class FazlaMesaiForm(FlaskForm):
    """Fazla mesai giriş/düzenleme formu."""
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    tarih = DateField('Tarih', format='%Y-%m-%d', validators=[DataRequired()],
                      default=lambda: datetime.now(timezone.utc))
    baslangic_saati = TimeField('Başlangıç Saati', format='%H:%M', validators=[DataRequired()])
    bitis_saati = TimeField('Bitiş Saati', format='%H:%M', validators=[DataRequired()])
    mesai_turu = SelectField('Mesai Türü', choices=[
        ('hafta_ici', 'Hafta İçi (1.5x)'),
        ('hafta_sonu', 'Hafta Sonu (2.0x)'),
        ('resmi_tatil', 'Resmi Tatil (2.0x)'),
    ], validators=[DataRequired()])
    neden = TextAreaField('Neden', validators=[Optional()])
    submit = SubmitField('Kaydet')


class SertifikaForm(FlaskForm):
    """Sertifika ekleme/düzenleme formu."""
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    sertifika_adi = StringField('Sertifika Adı', validators=[DataRequired(), Length(min=3, max=200)])
    veren_kurum = StringField('Veren Kurum', validators=[DataRequired(), Length(min=2, max=150)])
    sertifika_no = StringField('Sertifika No', validators=[Optional(), Length(max=100)])
    kategori = SelectField('Kategori', choices=[
        ('mesleki', 'Mesleki Yeterlilik'),
        ('teknik', 'Teknik Eğitim'),
        ('isg', 'İSG'),
        ('dil', 'Yabancı Dil'),
        ('bilgi_teknolojileri', 'Bilgi Teknolojileri'),
        ('diger', 'Diğer'),
    ], validators=[DataRequired()])
    verilis_tarihi = DateField('Veriliş Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    gecerlilik_bitis = DateField('Geçerlilik Bitiş', format='%Y-%m-%d', validators=[Optional()])
    hatirlatma_gun = IntegerField('Hatırlatma (gün)', default=30,
                                  validators=[Optional(), NumberRange(min=1, max=365)])
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')


class MaasSkalasıForm(FlaskForm):
    """Maaş skalası kayıt formu."""
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    donem_baslangic = DateField('Dönem Başlangıç', format='%Y-%m-%d', validators=[DataRequired()])
    donem_bitis = DateField('Dönem Bitiş', format='%Y-%m-%d', validators=[Optional()])
    brut_maas = DecimalField('Brüt Maaş (₺)', places=2, validators=[DataRequired(), NumberRange(min=0)])
    net_maas = DecimalField('Net Maaş (₺)', places=2, validators=[Optional(), NumberRange(min=0)])
    ek_odeme = DecimalField('Ek Ödeme (₺)', places=2, default=0, validators=[Optional(), NumberRange(min=0)])
    ek_odeme_aciklama = StringField('Ek Ödeme Açıklama', validators=[Optional(), Length(max=200)])
    artis_orani = DecimalField('Artış Oranı (%)', places=2, validators=[Optional()])
    derece = IntegerField('Derece', validators=[Optional(), NumberRange(min=1, max=15)])
    kademe = IntegerField('Kademe', validators=[Optional(), NumberRange(min=1, max=10)])
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')


class ZimmetForm(FlaskForm):
    """Zimmet kayıt formu."""
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    demirbas_adi = StringField('Demirbaş Adı', validators=[DataRequired(), Length(min=2, max=200)])
    demirbas_kodu = StringField('Demirbaş Kodu', validators=[Optional(), Length(max=50)])
    seri_no = StringField('Seri No', validators=[Optional(), Length(max=100)])
    kategori = SelectField('Kategori', choices=[
        ('bilisim', 'Bilişim'),
        ('otopark', 'Otopark'),
        ('anahtar', 'Anahtar / Kart'),
        ('kiyafet', 'Kıyafet / KKD'),
        ('alet', 'Alet / Ekipman'),
        ('diger', 'Diğer'),
    ], validators=[DataRequired()])
    teslim_tarihi = DateField('Teslim Tarihi', format='%Y-%m-%d', validators=[DataRequired()],
                               default=lambda: datetime.now(timezone.utc))
    deger = DecimalField('Tahmini Değer (₺)', places=2, validators=[Optional(), NumberRange(min=0)])
    notlar = TextAreaField('Notlar', validators=[Optional()])
    teslim_alan_imza = BooleanField('İmza Alındı', default=False)
    submit = SubmitField('Kaydet')


class GirisCikisEvrakForm(FlaskForm):
    """İşe giriş/çıkış evrak kayıt formu."""
    calisan_id = SelectField('Çalışan', coerce=int, validators=[DataRequired()])
    evrak_turu = SelectField('Evrak Türü', choices=[
        ('ise_giris', 'İşe Giriş'),
        ('isten_cikis', 'İşten Çıkış'),
    ], validators=[DataRequired()])
    evrak_adi = StringField('Evrak Adı', validators=[DataRequired(), Length(min=3, max=200)])
    durum = SelectField('Durum', choices=[
        ('bekliyor', 'Bekliyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('eksik', 'Eksik'),
    ], default='bekliyor')
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')
