"""FDYS — PDF Rapor Üretme Servisi (Kurumsal Sürüm)"""

import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# Font kaydı: Windows Arial varsa kullan, yoksa Helvetica'ya düş (Linux/macOS uyumu)
_FONT_FAMILY = 'Helvetica'
_FONT_FAMILY_BOLD = 'Helvetica-Bold'

_WINDOWS_FONT_DIR = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
_arial_path = os.path.join(_WINDOWS_FONT_DIR, 'arial.ttf')

if os.path.exists(_arial_path):
    try:
        pdfmetrics.registerFont(TTFont('Arial', os.path.join(_WINDOWS_FONT_DIR, 'arial.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-Bold', os.path.join(_WINDOWS_FONT_DIR, 'arialbd.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-Italic', os.path.join(_WINDOWS_FONT_DIR, 'ariali.ttf')))
        pdfmetrics.registerFont(TTFont('Arial-BoldItalic', os.path.join(_WINDOWS_FONT_DIR, 'arialbi.ttf')))
        pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold',
                                       italic='Arial-Italic', boldItalic='Arial-BoldItalic')
        _FONT_FAMILY = 'Arial'
        _FONT_FAMILY_BOLD = 'Arial-Bold'
    except Exception:
        pass  # Font kayıt hatası — Helvetica ile devam et

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontName=_FONT_FAMILY_BOLD,
            fontSize=18,
            alignment=1, # Center
            spaceAfter=20,
            textColor=colors.HexColor("#1e3a8a") # Koyu mavi kurumsal renk
        )
        self.subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=self.styles['Heading2'],
            fontName=_FONT_FAMILY_BOLD,
            fontSize=14,
            alignment=0,
            spaceAfter=10,
            textColor=colors.HexColor("#334155")
        )
        self.normal_style = ParagraphStyle(
            'NormalStyle',
            parent=self.styles['Normal'],
            fontName=_FONT_FAMILY,
            fontSize=10,
            spaceAfter=5
        )

    def _header_footer(self, canvas, doc, title="FabrikaOS Raporu"):
        canvas.saveState()
        # Header
        canvas.setFont(_FONT_FAMILY_BOLD, 10)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 10, "FDYS - Fabrika Dijital Yönetim Sistemi")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin + 10, title)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin + 5, doc.width + doc.leftMargin, doc.height + doc.topMargin + 5)
        
        # Footer
        canvas.setFont(_FONT_FAMILY, 9)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 15, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        page_num = canvas.getPageNumber()
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 15, f"Sayfa {page_num}")
        canvas.line(doc.leftMargin, doc.bottomMargin - 5, doc.width + doc.leftMargin, doc.bottomMargin - 5)
        canvas.restoreState()

    def _create_doc(self, buffer, title):
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2.5*cm, bottomMargin=2*cm
        )
        # Using a closure to pass title to the header/footer
        def on_page(canvas, doc):
            self._header_footer(canvas, doc, title)
        
        return doc, on_page

    def _get_base_table_style(self):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), _FONT_FAMILY_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), _FONT_FAMILY),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])
        ])

    def uretim_raporu(self, makine, uretim_verileri):
        """Makine bazlı üretim performans raporu (PDF)."""
        buffer = BytesIO()
        doc, on_page = self._create_doc(buffer, "Üretim Performans Raporu")
        elements = []

        elements.append(Paragraph("Üretim Performans Raporu", self.title_style))
        elements.append(Paragraph(f"<b>Makine:</b> {makine.ad} ({makine.kod})", self.normal_style))
        elements.append(Spacer(1, 20))

        data = [['Tarih', 'Vardiya', 'Üretim', 'Hata', 'OEE %']]
        for u in uretim_verileri:
            data.append([
                u.tarih.strftime('%d.%m.%Y'),
                u.vardiya.capitalize(),
                str(u.gercek_uretim),
                str(u.hatali_uretim),
                f"%{u.oee_yuzde}" if u.oee_yuzde else "-"
            ])

        t = Table(data, colWidths=[3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm])
        t.setStyle(self._get_base_table_style())
        elements.append(t)

        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        return buffer

    def kalite_raporu(self, hata_kayitlari, ay, yil):
        """ISO 9001 uyumlu aylık kalite raporu."""
        buffer = BytesIO()
        doc, on_page = self._create_doc(buffer, "ISO 9001 Kalite Raporu")
        elements = []

        elements.append(Paragraph(f"ISO 9001 Aylık Kalite Raporu ({ay}/{yil})", self.title_style))
        elements.append(Spacer(1, 10))

        data = [['Tarih', 'Makine', 'Kategori', 'Hata Türü', 'Adet', 'Fire (%)']]
        toplam_hata = 0
        toplam_fire = 0
        for h in hata_kayitlari:
            fire = float(h.fire_orani or 0)
            data.append([
                h.tarih.strftime('%d.%m.%Y'),
                h.makine.kod if h.makine else "-",
                h.hata_kategorisi,
                h.hata_turu[:20],
                str(h.adet),
                f"{fire:.1f}"
            ])
            toplam_hata += h.adet
            toplam_fire += fire

        # Özet Tablosu
        elements.append(Paragraph("Özet Kalite Verileri", self.subtitle_style))
        ozet_data = [
            ['Toplam Hatalı Ürün', 'Ort. Fire Oranı (%)', 'İncelenen Kayıt Sayısı'],
            [str(toplam_hata), f"{toplam_fire / max(len(hata_kayitlari), 1):.1f}", str(len(hata_kayitlari))]
        ]
        t_ozet = Table(ozet_data, colWidths=[5*cm, 5*cm, 5*cm])
        t_ozet.setStyle(self._get_base_table_style())
        elements.append(t_ozet)
        elements.append(Spacer(1, 20))

        # Detay Tablosu
        elements.append(Paragraph("Hata Detayları", self.subtitle_style))
        t = Table(data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 4*cm, 2*cm, 2.5*cm])
        t.setStyle(self._get_base_table_style())
        elements.append(t)

        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        return buffer

    def isg_raporu(self, isg_olaylari, yil):
        """ISO 45001 uyumlu yıllık İSG raporu."""
        buffer = BytesIO()
        doc, on_page = self._create_doc(buffer, "ISO 45001 Yıllık İSG Raporu")
        elements = []

        elements.append(Paragraph(f"ISO 45001 Yıllık İSG Raporu ({yil})", self.title_style))
        elements.append(Spacer(1, 10))

        data = [['Tarih', 'Olay Türü', 'Kategori', 'Şiddet', 'Kayıp Gün', 'Durum']]
        for o in isg_olaylari:
            olay_turu = 'Ramak Kala' if o.ramak_kala else 'İş Kazası'
            data.append([
                o.tarih.strftime('%d.%m.%Y'),
                olay_turu,
                o.yaralanma_tipi,
                o.siddet,
                str(o.kayip_gun),
                o.durum
            ])

        t = Table(data, colWidths=[2.5*cm, 3*cm, 3.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        t.setStyle(self._get_base_table_style())
        elements.append(t)

        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        return buffer

    def enerji_raporu(self, enerji_tuketimleri, ay, yil):
        """ISO 50001 uyumlu enerji yönetim raporu."""
        buffer = BytesIO()
        doc, on_page = self._create_doc(buffer, "ISO 50001 Enerji Yönetim Raporu")
        elements = []

        elements.append(Paragraph(f"ISO 50001 Enerji Yönetim Raporu ({ay}/{yil})", self.title_style))
        elements.append(Spacer(1, 10))

        data = [['Makine', 'Enerji Türü', 'Tüketim', 'Birim', 'Maliyet (TL)']]
        toplam_maliyet = 0
        for e in enerji_tuketimleri:
            maliyet = float(e.toplam_maliyet or 0)
            data.append([
                e.makine.kod if e.makine else "-",
                e.enerji_turu,
                str(e.miktar),
                e.birim,
                f"{maliyet:,.2f}"
            ])
            toplam_maliyet += maliyet

        elements.append(Paragraph(f"<b>Toplam Enerji Maliyeti:</b> {toplam_maliyet:,.2f} TL", self.normal_style))
        elements.append(Spacer(1, 15))

        t = Table(data, colWidths=[3.5*cm, 3.5*cm, 3*cm, 2.5*cm, 3.5*cm])
        t.setStyle(self._get_base_table_style())
        elements.append(t)

        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        return buffer

    def sgk_bildirim_formu(self, olay):
        """İş kazası SGK bildirimi formatında PDF (basitleştirilmiş şablon)."""
        buffer = BytesIO()
        doc, on_page = self._create_doc(buffer, "SGK İş Kazası Bildirim Formu")
        elements = []

        elements.append(Paragraph("SOSYAL GÜVENLİK KURUMU BAŞKANLIĞI", self.title_style))
        elements.append(Paragraph("İŞ KAZASI VE MESLEK HASTALIĞI BİLDİRİM FORMU", self.subtitle_style))
        elements.append(Spacer(1, 20))

        # Form tablosu
        olay_turu = 'Ramak Kala' if olay.ramak_kala else 'İş Kazası'
        form_data = [
            ["Olay Tarihi", olay.tarih.strftime('%d.%m.%Y %H:%M') if olay.tarih else "-"],
            ["Bildirim Tarihi", datetime.now().strftime('%d.%m.%Y %H:%M')],
            ["Kayıt No", f"ISG-{olay.id}"],
            ["Olay Türü", olay_turu],
            ["Olay Kategorisi", olay.yaralanma_tipi],
            ["Şiddet Derecesi", olay.siddet],
            ["Olayın Gerçekleştiği Bölüm", olay.yer or "-"],
            ["Olayın Açıklaması", olay.aciklama or "-"]
        ]

        t = Table(form_data, colWidths=[6*cm, 10*cm])
        style = self._get_base_table_style()
        # Remove bold from value column
        style.add('FONTNAME', (1, 0), (1, -1), 'Arial')
        style.add('ALIGN', (0, 0), (0, -1), 'LEFT')
        style.add('ALIGN', (1, 0), (1, -1), 'LEFT')
        t.setStyle(style)
        
        elements.append(t)
        elements.append(Spacer(1, 40))
        
        # İmza alanı
        imza_data = [
            ["İşveren / Vekili", "İş Güvenliği Uzmanı"],
            ["İmza:", "İmza:"]
        ]
        t_imza = Table(imza_data, colWidths=[8*cm, 8*cm])
        t_imza.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 40),
        ]))
        elements.append(t_imza)

        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        return buffer
