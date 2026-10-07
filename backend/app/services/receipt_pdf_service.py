"""
Section 80G Income Tax Exemption Donation Receipt PDF Generator using ReportLab.
"""
import io
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT


def number_to_words(n: int) -> str:
    """Helper converting integer amount into words in Indian numbering convention."""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    if n == 0:
        return "Zero"

    def convert_below_thousand(num: int) -> str:
        res = ""
        if num >= 100:
            res += units[num // 100] + " Hundred "
            num %= 100
        if num >= 20:
            res += tens[num // 10] + " "
            num %= 10
        elif num >= 10:
            res += teens[num - 10] + " "
            num = 0
        if num > 0:
            res += units[num] + " "
        return res.strip()

    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000

    parts = []
    if crore:
        parts.append(convert_below_thousand(crore) + " Crore")
    if lakh:
        parts.append(convert_below_thousand(lakh) + " Lakh")
    if thousand:
        parts.append(convert_below_thousand(thousand) + " Thousand")
    if n:
        parts.append(convert_below_thousand(n))

    return " ".join(parts).strip() + " Rupees Only"


class ReceiptPDFService:
    @staticmethod
    def generate_80g_receipt_pdf(
        receipt_number: str,
        donor_name: str,
        donor_pan: Optional[str],
        donor_email: str,
        donor_address: Optional[str],
        amount_inr: float,
        payment_id: str,
        payment_method: str,
        campaign_title: Optional[str],
        donation_date: datetime
    ) -> bytes:
        """
        Builds a compliant Section 80G tax exemption donation receipt.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#047857')
        )
        subtitle_style = ParagraphStyle(
            'HeaderSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#374151')
        )
        badge_style = ParagraphStyle(
            'Badge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#065F46')
        )
        bold_text = ParagraphStyle('BText', fontName='Helvetica-Bold', fontSize=9, leading=13, textColor=colors.HexColor('#111827'))
        body_text = ParagraphStyle('NText', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#374151'))
        legal_text = ParagraphStyle('LText', fontName='Helvetica', fontSize=7.5, leading=10.5, alignment=TA_JUSTIFY, textColor=colors.HexColor('#4B5563'))

        elements = []

        # Organization Header
        elements.append(Paragraph("ANIMAL GUARDIAN 360 FOUNDATION", title_style))
        elements.append(Paragraph(
            "Registered Public Charitable Trust | NITI Aayog NGO Darpan Reg. No: DL/2024/0398214<br/>"
            "National Secretariat: Institutional Area, New Delhi - 110003 | Email: accounts@animalguardian360.org",
            subtitle_style
        ))
        elements.append(Spacer(1, 8))

        # Receipt Title Box
        elements.append(
            Table(
                [[Paragraph("DONATION RECEIPT (UNDER SECTION 80G OF INCOME TAX ACT, 1961)", badge_style)]],
                colWidths=[540],
                style=TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#10B981')),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ])
            )
        )
        elements.append(Spacer(1, 10))

        # Metadata Row
        date_str = donation_date.strftime("%d-%B-%Y")
        meta_data = [
            [Paragraph(f"<b>Receipt No:</b> {receipt_number}", bold_text), Paragraph(f"<b>Date:</b> {date_str}", bold_text)],
            [Paragraph("<b>80G Order No:</b> CIT(E)/DELHI/80G/2024-25/08492", bold_text), Paragraph("<b>Financial Year:</b> 2026-2027", bold_text)],
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 12))

        # Donor Information Table
        donor_rows = [
            [Paragraph("Donor Name:", bold_text), Paragraph(donor_name, bold_text)],
            [Paragraph("Permanent Account Number (PAN):", bold_text), Paragraph(donor_pan or "NOT PROVIDED (General Receipt)", bold_text)],
            [Paragraph("Email Address:", bold_text), Paragraph(donor_email, body_text)],
            [Paragraph("Postal Address:", bold_text), Paragraph(donor_address or "Recorded via Digital Payment Profile", body_text)],
        ]
        donor_table = Table(donor_rows, colWidths=[180, 360])
        donor_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(donor_table)
        elements.append(Spacer(1, 12))

        # Payment & Amount Table
        words_str = number_to_words(int(amount_inr))
        payment_rows = [
            [Paragraph("Donation Amount in Figures:", bold_text), Paragraph(f"<b>₹ {amount_inr:,.2f} INR</b>", bold_text)],
            [Paragraph("Donation Amount in Words:", bold_text), Paragraph(words_str, bold_text)],
            [Paragraph("Mode of Payment / Method:", bold_text), Paragraph(f"Razorpay / {payment_method.upper()}", body_text)],
            [Paragraph("Transaction Reference / ID:", bold_text), Paragraph(payment_id, body_text)],
            [Paragraph("Allocated Purpose:", bold_text), Paragraph(campaign_title or "General Animal Welfare, Rescue & Care Fund", body_text)],
        ]
        payment_table = Table(payment_rows, colWidths=[180, 360])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 12))

        # Legal Exemption Box
        legal_text_content = (
            "<b>STATUTORY TAX EXEMPTION DECLARATION:</b><br/>"
            "This certifies that donations to Animal Guardian 360 Foundation qualify for 50% income tax deduction under "
            "Section 80G(5)(vi) of the Income Tax Act, 1961. Unique Document Identification Number (UDIN) will be filed "
            "in the annual Statement of Donations (Form 10BD) with the Income Tax Department. "
            "Donors with valid PAN will automatically have this contribution reflected in their Annual Information Statement (AIS) / Form 26AS."
        )
        elements.append(
            Table(
                [[Paragraph(legal_text_content, legal_text)]],
                colWidths=[540],
                style=TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#9CA3AF')),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ])
            )
        )
        elements.append(Spacer(1, 25))

        # Authorized Signatory Block
        sig_data = [
            [
                Paragraph("<i>This is a computer-generated receipt valid under IT Rules.</i>", legal_text),
                Paragraph("<b>For Animal Guardian 360 Foundation</b><br/><br/><i>Authorized Signatory & Treasurer</i>", bold_text)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[320, 220])
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


receipt_pdf_service = ReceiptPDFService()
