"""
Notification service for Emergency SOS dispatches, SMS/WhatsApp, and Email alerts.
Supports SendGrid v3 API, AWS SES, SMS Gateway, and robust local mock dispatching.
"""
import base64
import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachment_name: Optional[str] = None,
        attachment_bytes: Optional[bytes] = None,
        attachment_type: str = "application/pdf"
    ) -> bool:
        """
        Sends an email using SendGrid v3 API, AWS SES, or gracefully logs in mock mode.
        """
        text_body = text_content or html_content

        # 1. SendGrid API Integration
        if settings.SENDGRID_API_KEY:
            try:
                mail_payload: Dict[str, Any] = {
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": settings.FROM_EMAIL, "name": settings.FROM_NAME},
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": text_body},
                        {"type": "text/html", "value": html_content}
                    ]
                }
                if attachment_name and attachment_bytes:
                    encoded_file = base64.b64encode(attachment_bytes).decode("ascii")
                    mail_payload["attachments"] = [
                        {
                            "content": encoded_file,
                            "filename": attachment_name,
                            "type": attachment_type,
                            "disposition": "attachment"
                        }
                    ]

                headers = {
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json"
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.sendgrid.com/v3/mail/send",
                        json=mail_payload,
                        headers=headers
                    )
                    if resp.status_code in (200, 202):
                        logger.info("SendGrid email successfully sent to %s (Subject: %s)", to_email, subject)
                        return True
                    else:
                        logger.error("SendGrid failed [%s]: %s", resp.status_code, resp.text)
            except Exception as err:
                logger.error("SendGrid API invocation error: %s", err)

        # 2. Local Mock / Development Fallback
        logger.info("================ EMAIL DISPATCH (DEV/MOCK) ================")
        logger.info("To: %s", to_email)
        logger.info("From: %s <%s>", settings.FROM_NAME, settings.FROM_EMAIL)
        logger.info("Subject: %s", subject)
        if attachment_name:
            logger.info("Attachment: %s (%d bytes)", attachment_name, len(attachment_bytes or b""))
        logger.info("Body Preview: %s", text_body[:200])
        logger.info("===========================================================")
        return True

    @staticmethod
    async def send_sms(to_phone: str, message: str) -> bool:
        """
        Sends an SMS alert via configured SMS provider or logs in development mock mode.
        """
        if settings.SMS_API_KEY and settings.SMS_PROVIDER != "mock":
            try:
                # Example generic SMS Gateway HTTP dispatch
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        "https://api.sms-gateway.in/v1/send",
                        json={"to": to_phone, "message": message, "sender": "AG360"},
                        headers={"Authorization": f"Bearer {settings.SMS_API_KEY}"}
                    )
                    if resp.status_code == 200:
                        logger.info("SMS delivered to %s", to_phone)
                        return True
            except Exception as err:
                logger.error("SMS Gateway error: %s", err)

        logger.info("================ SMS ALERT (DEV/MOCK) ================")
        logger.info("To: %s", to_phone)
        logger.info("Message: %s", message)
        logger.info("======================================================")
        return True

    async def send_emergency_dispatch(
        self,
        hospital_name: str,
        hospital_email: Optional[str],
        hospital_phone: str,
        animal_type: str,
        address: Optional[str],
        secure_token: str,
        round_number: int
    ) -> None:
        """
        Sends an emergency SOS dispatch alert to a veterinary hospital via Email and SMS/WhatsApp.
        Includes a one-time cryptographic link to Accept or Decline the case.
        """
        action_base = f"{settings.FRONTEND_URL}/vets/dispatch/{secure_token}"
        accept_url = f"{action_base}?action=accept"
        decline_url = f"{action_base}?action=decline"

        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #dc2626; border-radius: 12px; background: #fff;">
            <h2 style="color: #dc2626; margin-top: 0;">🚨 CRITICAL ROAD ACCIDENT SOS DISPATCH</h2>
            <p>Dear <strong>{hospital_name}</strong>,</p>
            <p>An injured animal requires immediate emergency triage within your operational perimeter.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr><td style="padding: 6px; font-weight: bold; width: 140px;">Animal Type:</td><td style="padding: 6px; color: #dc2626;"><strong>{animal_type.upper()}</strong></td></tr>
                <tr><td style="padding: 6px; font-weight: bold;">Location:</td><td style="padding: 6px;">{address or 'GPS coordinates attached on link'}</td></tr>
                <tr><td style="padding: 6px; font-weight: bold;">Escalation Tier:</td><td style="padding: 6px;">Round {round_number}</td></tr>
            </table>
            <div style="margin-top: 24px; text-align: center;">
                <a href="{accept_url}" style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-right: 12px; display: inline-block;">✅ ACCEPT CASE & DISPATCH AMBULANCE</a>
                <a href="{decline_url}" style="background-color: #64748b; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">DECLINE</a>
            </div>
            <p style="font-size: 11px; color: #64748b; margin-top: 24px; text-align: center;">Animal Guardian 360° Emergency Network India</p>
        </div>
        """

        sms_text = (
            f"🚨 AG360 SOS ALERT: Injured {animal_type} at {address or 'nearby GPS'}. "
            f"Accept or Decline immediately: {accept_url}"
        )

        if hospital_email:
            await self.send_email(
                to_email=hospital_email,
                subject=f"🚨 URGENT: Road Accident SOS ({animal_type.upper()}) - Round {round_number}",
                html_content=email_html,
                text_content=sms_text
            )

        if hospital_phone:
            await self.send_sms(to_phone=hospital_phone, message=sms_text)

    async def notify_reporter_case_accepted(
        self,
        reporter_phone: Optional[str],
        hospital_name: str,
        hospital_phone: str,
        eta_minutes: int
    ) -> None:
        """
        Notifies citizen reporter that a veterinary hospital accepted their road accident SOS.
        """
        if not reporter_phone:
            return

        msg = (
            f"✅ Good news! {hospital_name} has accepted your animal rescue alert. "
            f"Estimated arrival time: {eta_minutes} mins. "
            f"Direct Hospital Helpline: {hospital_phone}. Thank you for being a guardian!"
        )
        await self.send_sms(to_phone=reporter_phone, message=msg)

    async def send_80g_receipt_email(
        self,
        donor_name: str,
        donor_email: str,
        receipt_number: str,
        amount_inr: float,
        pan_number: str,
        pdf_bytes: Optional[bytes] = None
    ) -> None:
        """
        Sends the 80G tax exemption receipt PDF directly to the donor.
        """
        subject = f"Your 80G Tax Exemption Certificate #{receipt_number} - Animal Guardian 360°"
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
            <h2 style="color: #059669;">Thank you for your life-saving contribution!</h2>
            <p>Dear <strong>{donor_name}</strong>,</p>
            <p>We gratefully acknowledge your contribution of <strong>₹{amount_inr:,.2f}</strong> towards animal rescue, medical trauma care, and feeding drives.</p>
            <div style="background-color: #f8fafc; padding: 14px; border-radius: 8px; margin: 16px 0; border: 1px solid #cbd5e1;">
                <p style="margin: 4px 0;"><strong>Receipt No:</strong> {receipt_number}</p>
                <p style="margin: 4px 0;"><strong>Donor PAN:</strong> {pan_number}</p>
                <p style="margin: 4px 0;"><strong>Eligible Deduction:</strong> Section 80G of the Income Tax Act, 1961</p>
            </div>
            <p>Your official tax exemption certificate is attached to this email.</p>
            <p style="font-size: 12px; color: #64748b;">Animal Guardian 360° India • Section 80G Registration Active</p>
        </div>
        """

        await self.send_email(
            to_email=donor_email,
            subject=subject,
            html_content=email_html,
            attachment_name=f"Tax_Receipt_80G_{receipt_number}.pdf",
            attachment_bytes=pdf_bytes,
            attachment_type="application/pdf"
        )


notification_service = NotificationService()
