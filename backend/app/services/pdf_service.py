"""
PDF Generation Service using ReportLab.
Produces official animal cruelty complaint summaries formatted for physical police filing.
"""
import io
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


class PDFService:
    @staticmethod
    def generate_cruelty_complaint_pdf(
        report_id: str,
        category: str,
        description: str,
        created_at: datetime,
        latitude: float,
        longitude: float,
        address_text: Optional[str],
        nearest_police_name: Optional[str],
        nearest_police_address: Optional[str],
        nearest_police_phone: Optional[str],
        is_anonymous: bool = False,
        reporter_name: Optional[str] = None,
        reporter_phone: Optional[str] = None
    ) -> bytes:
        """
        Generates a clean, professional PDF complaint summary for submission to local police authorities.
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
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#991B1B')
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1F2937')
        )
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor('#4B5563')
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#111827'),
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1F2937')
        )
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#111827')
        )

        elements = []

        # Header Title
        elements.append(Paragraph("ANIMAL GUARDIAN 360° — CITIZEN COMPLAINT SUMMARY", title_style))
        elements.append(Paragraph("FOR SUBMISSION TO LOCAL POLICE STATION / STATION HOUSE OFFICER (SHO)", subtitle_style))
        elements.append(Spacer(1, 10))

        # Important Notice Box
        notice_text = (
            "<b>IMPORTANT LEGAL NOTICE:</b> This summary is prepared by a citizen via Animal Guardian 360° "
            "to assist police personnel in registering a formal complaint/FIR. This document does <b>NOT</b> "
            "constitute an automatically filed FIR with the police department. Direct submission or physical verification is required."
        )
        elements.append(
            Table(
                [[Paragraph(notice_text, disclaimer_style)]],
                colWidths=[540],
                style=TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF2F2')),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F87171')),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ])
            )
        )
        elements.append(Spacer(1, 12))

        # Basic Info Table
        dt_str = created_at.strftime("%d-%b-%Y, %I:%M %p UTC")
        info_data = [
            [Paragraph("Report Reference ID:", bold_style), Paragraph(report_id, body_style)],
            [Paragraph("Date & Time of Record:", bold_style), Paragraph(dt_str, body_style)],
            [Paragraph("Offence Category:", bold_style), Paragraph(category.upper().replace('_', ' '), bold_style)],
            [Paragraph("Relevant Legal Provisions:", bold_style), Paragraph(
                "Section 11, Prevention of Cruelty to Animals Act, 1960;<br/>"
                "Sections 325 & 326, Bharatiya Nyaya Sanhita (BNS) 2023 / IPC 428/429;<br/>"
                "Wildlife Protection Act, 1972 (if trade/wildlife involved)",
                body_style
            )],
        ]
        info_table = Table(info_data, colWidths=[160, 380])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

        # Nearest Police Station Section
        elements.append(Paragraph("1. DESIGNATED LOCAL POLICE JURISDICTION", section_heading))
        police_data = [
            [Paragraph("Station Name:", bold_style), Paragraph(nearest_police_name or "Local Police Station", body_style)],
            [Paragraph("Station Address:", bold_style), Paragraph(nearest_police_address or "Near incident GPS coordinates", body_style)],
            [Paragraph("Emergency Helpline:", bold_style), Paragraph("112 / " + (nearest_police_phone or "112"), bold_style)],
        ]
        p_table = Table(police_data, colWidths=[160, 380])
        p_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(p_table)
        elements.append(Spacer(1, 12))

        # Incident Location
        elements.append(Paragraph("2. INCIDENT LOCATION & GPS COORDINATES", section_heading))
        loc_data = [
            [Paragraph("GPS Coordinates:", bold_style), Paragraph(f"{latitude:.6f}° N, {longitude:.6f}° E", body_style)],
            [Paragraph("Street / Landmark:", bold_style), Paragraph(address_text or "GPS coordinates recorded directly from device", body_style)],
            [Paragraph("Google Maps Link:", bold_style), Paragraph(f"https://www.google.com/maps?q={latitude},{longitude}", body_style)],
        ]
        loc_table = Table(loc_data, colWidths=[160, 380])
        loc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(loc_table)
        elements.append(Spacer(1, 12))

        # Description of Cruelty
        elements.append(Paragraph("3. CITIZEN WITNESS ACCOUNT & DESCRIPTION", section_heading))
        desc_table = Table([[Paragraph(description, body_style)]], colWidths=[540])
        desc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(desc_table)
        elements.append(Spacer(1, 12))

        # Reporter Details
        elements.append(Paragraph("4. COMPLAINANT / INFORMANT DETAILS", section_heading))
        rep_status = "ANONYMOUS (Identity withheld under whistleblower protection)" if is_anonymous else (reporter_name or "Registered User")
        rep_phone = "PROTECTED" if is_anonymous else (reporter_phone or "On File")
        rep_data = [
            [Paragraph("Complainant Name:", bold_style), Paragraph(rep_status, body_style)],
            [Paragraph("Contact Number:", bold_style), Paragraph(rep_phone, body_style)],
        ]
        rep_table = Table(rep_data, colWidths=[160, 380])
        rep_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(rep_table)
        elements.append(Spacer(1, 20))

        # Footer Signature Blocks
        sig_data = [
            [
                Paragraph("<b>Complainant Signature:</b><br/><br/>_______________________", body_style),
                Paragraph("<b>Police Station Receiving Stamp / DD No:</b><br/><br/>_______________________", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


pdf_service = PDFService()
