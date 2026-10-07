"""
Donations API: Razorpay UPI Intent & QR Checkout, HMAC-SHA256 signature verification,
idempotent webhook receiver, 80G tax receipt PDF generation, and public transparency.
"""
from datetime import datetime, timezone
import json
import re
from typing import Annotated, Optional, List, Dict
from fastapi import APIRouter, Depends, Query, Header, Request, Response, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.exceptions import NotFoundError, BadRequestError, AppException
from app.core.security import decode_token
from app.models.user import User
from app.models.donation import Campaign, Donation, FundAllocation
from app.schemas.donation import (
    DonationOrderCreate,
    DonationOrderResponse,
    PaymentVerifyRequest,
    DonationResponse,
    CampaignCreate,
    CampaignResponse,
    FundAllocationCreate,
    FundAllocationResponse,
    TransparencySummaryResponse
)
from app.services.razorpay_service import razorpay_service
from app.services.receipt_pdf_service import receipt_pdf_service
from app.services.notification import notification_service

router = APIRouter(prefix="/donations", tags=["Donations & Transparency"])


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[-\s]+", "-", s)


@router.post(
    "/orders",
    response_model=DonationOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay order for UPI Intent / QR Checkout"
)
async def create_donation_order(
    payload: DonationOrderCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a donation intent and returns a Razorpay Order ID for frontend checkout.
    Supports both anonymous donors and authenticated accounts.
    """
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            claims = decode_token(token, expected_type="access")
            user_id = claims.get("sub")
        except Exception:
            pass

    # Verify campaign exists if specified
    campaign_title = None
    if payload.campaign_id:
        c_stmt = select(Campaign).where(Campaign.id == payload.campaign_id)
        c_res = await db.execute(c_stmt)
        campaign = c_res.scalar_one_or_none()
        if campaign:
            campaign_title = campaign.title

    receipt_ref = razorpay_service.generate_receipt_number()
    rzp_order = razorpay_service.create_order(
        amount_inr=payload.amount_inr,
        receipt=receipt_ref,
        notes={
            "donor_name": payload.donor_name,
            "donor_email": payload.donor_email,
            "campaign_id": payload.campaign_id or "general_welfare",
            "pan": payload.donor_pan or "none"
        }
    )

    donation = Donation(
        user_id=user_id,
        campaign_id=payload.campaign_id,
        amount_inr=payload.amount_inr,
        currency="INR",
        donor_name=payload.donor_name,
        donor_email=payload.donor_email,
        donor_phone=payload.donor_phone,
        donor_pan=payload.donor_pan,
        donor_address=payload.donor_address,
        razorpay_order_id=rzp_order["id"],
        payment_status="created",
        receipt_number=receipt_ref
    )
    db.add(donation)
    await db.commit()
    await db.refresh(donation)

    return DonationOrderResponse(
        order_id=rzp_order["id"],
        amount_inr=payload.amount_inr,
        amount_paise=int(round(payload.amount_inr * 100)),
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID or "rzp_test_public_key",
        donation_id=donation.id
    )


@router.post(
    "/verify",
    response_model=DonationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Razorpay payment signature, capture donation, and issue 80G receipt"
)
async def verify_payment(
    payload: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies the HMAC-SHA256 signature returned by Razorpay Checkout.
    Idempotent: Re-submitting the same payment ID returns the existing captured record.
    """
    is_valid = razorpay_service.verify_payment_signature(
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature
    )
    if not is_valid:
        from app.core.exceptions import AppException
        raise AppException(
            message="Payment verification failed: invalid transaction signature",
            status_code=400,
            error_code="INVALID_PAYMENT_SIGNATURE"
        )

    stmt = select(Donation).where(Donation.razorpay_order_id == payload.razorpay_order_id)
    res = await db.execute(stmt)
    donation = res.scalar_one_or_none()
    if not donation:
        raise NotFoundError("Donation order record not found")

    # Idempotent guard
    if donation.payment_status == "captured":
        return DonationResponse.model_validate(donation)

    # Mark as captured
    donation.payment_status = "captured"
    donation.razorpay_payment_id = payload.razorpay_payment_id
    donation.razorpay_signature = payload.razorpay_signature
    donation.payment_method = "upi"
    donation.tax_exemption_80g_issued = True
    donation.receipt_pdf_url = f"/api/v1/donations/{donation.id}/receipt"

    # If linked to a campaign, increment raised amount
    if donation.campaign_id:
        c_stmt = select(Campaign).where(Campaign.id == donation.campaign_id)
        c_res = await db.execute(c_stmt)
        campaign = c_res.scalar_one_or_none()
        if campaign:
            campaign.raised_amount_inr += donation.amount_inr

    await db.commit()
    await db.refresh(donation)

    # Automatically dispatch 80G Tax Exemption Receipt via Email
    if donation.donor_email:
        try:
            camp_title = "General Welfare Fund"
            if donation.campaign_id:
                c_stmt = select(Campaign).where(Campaign.id == donation.campaign_id)
                c_res = await db.execute(c_stmt)
                c_obj = c_res.scalar_one_or_none()
                if c_obj:
                    camp_title = c_obj.title

            pdf_bytes = receipt_pdf_service.generate_80g_receipt_pdf(
                receipt_number=donation.receipt_number or f"AG360-80G-{donation.id[:8].upper()}",
                donor_name=donation.donor_name,
                donor_email=donation.donor_email,
                donor_phone=donation.donor_phone,
                donor_pan=donation.donor_pan or "NOT PROVIDED",
                amount_inr=donation.amount_inr,
                payment_id=donation.razorpay_payment_id or "VERIFIED",
                order_id=donation.razorpay_order_id,
                donation_date=donation.created_at,
                campaign_title=camp_title
            )
            await notification_service.send_80g_receipt_email(
                donor_name=donation.donor_name,
                donor_email=donation.donor_email,
                receipt_number=donation.receipt_number or f"AG360-80G-{donation.id[:8].upper()}",
                amount_inr=donation.amount_inr,
                pan_number=donation.donor_pan or "NOT PROVIDED",
                pdf_bytes=pdf_bytes
            )
        except Exception:
            pass

    return DonationResponse.model_validate(donation)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Razorpay Webhook receiver for background payment notifications"
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Idempotent webhook receiver for payment.captured events.
    Verifies X-Razorpay-Signature and reconciles payment records.
    """
    body_bytes = await request.body()

    if x_razorpay_signature:
        is_valid = razorpay_service.verify_webhook_signature(
            payload_body=body_bytes,
            signature=x_razorpay_signature
        )
        if not is_valid:
            from app.core.exceptions import AppException
            raise AppException(message="Invalid webhook signature", status_code=400)

    try:
        event_data = json.loads(body_bytes.decode("utf-8"))
        event_type = event_data.get("event")

        if event_type == "payment.captured":
            payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")
            method = payment_entity.get("method", "upi")

            if order_id:
                stmt = select(Donation).where(Donation.razorpay_order_id == order_id)
                res = await db.execute(stmt)
                donation = res.scalar_one_or_none()
                if donation and donation.payment_status != "captured":
                    donation.payment_status = "captured"
                    donation.razorpay_payment_id = payment_id
                    donation.payment_method = method
                    donation.tax_exemption_80g_issued = True
                    donation.receipt_pdf_url = f"/api/v1/donations/{donation.id}/receipt"

                    if donation.campaign_id:
                        c_stmt = select(Campaign).where(Campaign.id == donation.campaign_id)
                        c_res = await db.execute(c_stmt)
                        campaign = c_res.scalar_one_or_none()
                        if campaign:
                            campaign.raised_amount_inr += donation.amount_inr

                    await db.commit()
    except Exception:
        pass

    return {"status": "ok", "message": "Webhook processed"}


@router.get(
    "/{donation_id}/receipt",
    summary="Download Section 80G Tax Exemption Donation Receipt PDF"
)
async def download_80g_receipt(
    donation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates and downloads the official Section 80G Tax Exemption Donation Receipt.
    """
    stmt = (
        select(Donation)
        .where(Donation.id == donation_id)
        .options(selectinload(Donation.campaign))
    )
    res = await db.execute(stmt)
    donation = res.scalar_one_or_none()
    if not donation:
        raise NotFoundError("Donation record not found")

    campaign_title = donation.campaign.title if donation.campaign else "General Welfare Fund"

    pdf_bytes = receipt_pdf_service.generate_80g_receipt_pdf(
        receipt_number=donation.receipt_number or "AG360-RECEIPT",
        donor_name=donation.donor_name,
        donor_pan=donation.donor_pan,
        donor_email=donation.donor_email,
        donor_address=donation.donor_address,
        amount_inr=donation.amount_inr,
        payment_id=donation.razorpay_payment_id or donation.razorpay_order_id,
        payment_method=donation.payment_method or "UPI",
        campaign_title=campaign_title,
        donation_date=donation.created_at
    )

    filename = f"80G_Receipt_{donation.receipt_number or donation.id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/transparency",
    response_model=TransparencySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public fund transparency breakdown and expense audits"
)
async def get_transparency_summary(db: AsyncSession = Depends(get_db)):
    """
    Public transparency endpoint displaying total funds raised, total allocated,
    category breakdown, recent audited expenses, and active campaigns.
    """
    # 1. Total raised
    raised_stmt = (
        select(func.coalesce(func.sum(Donation.amount_inr), 0.0), func.count(Donation.id))
        .where(Donation.payment_status == "captured")
    )
    raised_res = await db.execute(raised_stmt)
    total_raised, count_donations = raised_res.one()

    # 2. Total allocated
    alloc_stmt = select(func.coalesce(func.sum(FundAllocation.amount_inr), 0.0))
    alloc_res = await db.execute(alloc_stmt)
    total_allocated = alloc_res.scalar()

    # 3. Category breakdown
    cat_stmt = (
        select(FundAllocation.category, func.coalesce(func.sum(FundAllocation.amount_inr), 0.0))
        .group_by(FundAllocation.category)
    )
    cat_res = await db.execute(cat_stmt)
    cat_breakdown = {row[0]: float(row[1]) for row in cat_res.all()}

    # Ensure all primary categories exist in map
    for default_cat in ["rescue_ops", "shelters", "medical_supplies", "food_feeding", "infrastructure"]:
        if default_cat not in cat_breakdown:
            cat_breakdown[default_cat] = 0.0

    # 4. Recent allocations (audited expenses)
    recent_alloc_stmt = (
        select(FundAllocation)
        .order_by(FundAllocation.allocation_date.desc(), FundAllocation.created_at.desc())
        .limit(20)
    )
    recent_res = await db.execute(recent_alloc_stmt)
    recent_allocs = [FundAllocationResponse.model_validate(a) for a in recent_res.scalars().all()]

    # 5. Active campaigns
    camp_stmt = select(Campaign).where(Campaign.is_active == True).order_by(Campaign.created_at.desc())
    camp_res = await db.execute(camp_stmt)
    campaigns = []
    for c in camp_res.scalars().all():
        pct = round((c.raised_amount_inr / c.target_amount_inr) * 100, 1) if c.target_amount_inr > 0 else 0.0
        campaigns.append(
            CampaignResponse(
                id=c.id,
                title=c.title,
                slug=c.slug,
                description=c.description,
                target_amount_inr=c.target_amount_inr,
                raised_amount_inr=c.raised_amount_inr,
                progress_percent=min(100.0, pct),
                cover_image_url=c.cover_image_url,
                is_active=c.is_active,
                created_at=c.created_at
            )
        )

    return TransparencySummaryResponse(
        total_raised_inr=float(total_raised),
        total_allocated_inr=float(total_allocated),
        donations_count=int(count_donations),
        category_breakdown=cat_breakdown,
        recent_allocations=recent_allocs,
        active_campaigns=campaigns
    )


@router.post(
    "/allocations",
    response_model=FundAllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin adds an audited expenditure entry with receipt URL"
)
async def create_fund_allocation(
    payload: FundAllocationCreate,
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    """Admin entry to record an audited allocation with invoice/receipt URL."""
    alloc = FundAllocation(
        category=payload.category,
        title=payload.title,
        description=payload.description,
        amount_inr=payload.amount_inr,
        allocation_date=payload.allocation_date,
        receipt_url=payload.receipt_url,
        verified_by_id=current_user.id
    )
    db.add(alloc)
    await db.commit()
    await db.refresh(alloc)
    return FundAllocationResponse.model_validate(alloc)


@router.get(
    "/campaigns",
    response_model=List[CampaignResponse],
    status_code=status.HTTP_200_OK,
    summary="List active donation campaigns"
)
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    stmt = select(Campaign).where(Campaign.is_active == True).order_by(Campaign.created_at.desc())
    res = await db.execute(stmt)
    camps = res.scalars().all()
    results = []
    for c in camps:
        pct = round((c.raised_amount_inr / c.target_amount_inr) * 100, 1) if c.target_amount_inr > 0 else 0.0
        results.append(
            CampaignResponse(
                id=c.id,
                title=c.title,
                slug=c.slug,
                description=c.description,
                target_amount_inr=c.target_amount_inr,
                raised_amount_inr=c.raised_amount_inr,
                progress_percent=min(100.0, pct),
                cover_image_url=c.cover_image_url,
                is_active=c.is_active,
                created_at=c.created_at
            )
        )
    return results


@router.post(
    "/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin creates a new donation campaign"
)
async def create_campaign(
    payload: CampaignCreate,
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    base_slug = slugify(payload.title)
    camp = Campaign(
        title=payload.title,
        slug=f"{base_slug}-{int(datetime.now(timezone.utc).timestamp())}",
        description=payload.description,
        target_amount_inr=payload.target_amount_inr,
        raised_amount_inr=0.0,
        cover_image_url=payload.cover_image_url,
        hospital_id=payload.hospital_id,
        is_active=True
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)

    return CampaignResponse(
        id=camp.id,
        title=camp.title,
        slug=camp.slug,
        description=camp.description,
        target_amount_inr=camp.target_amount_inr,
        raised_amount_inr=0.0,
        progress_percent=0.0,
        cover_image_url=camp.cover_image_url,
        is_active=camp.is_active,
        created_at=camp.created_at
    )
