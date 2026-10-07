"""
Feature 4 Tests: Donations via UPI, Razorpay Orders, HMAC Signature Verification,
80G Tax Exemption Receipts, Idempotent Webhooks, and Public Transparency Ledger.
"""
import io
import json
from datetime import date
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.donation import Campaign, Donation, FundAllocation
from app.models.user import User



@pytest.mark.asyncio
async def test_create_donation_order_valid(client: AsyncClient):
    """Anonymous donor can create a valid donation order with PAN for 80G tax receipt."""
    payload = {
        "amount_inr": 2500.0,
        "donor_name": "Rohan Deshmukh",
        "donor_email": "rohan@example.org",
        "donor_phone": "+919876543210",
        "donor_pan": "ABCDE1234F",
        "donor_address": "Flat 302, Green Meadows, Pune, Maharashtra 411001"
    }
    response = await client.post("/api/v1/donations/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "order_id" in data
    assert data["order_id"].startswith("order_")
    assert data["amount_inr"] == 2500.0
    assert data["amount_paise"] == 250000
    assert data["currency"] == "INR"
    assert "donation_id" in data


@pytest.mark.asyncio
async def test_create_donation_order_invalid_pan_format(client: AsyncClient):
    """Invalid PAN format is rejected with validation error (422)."""
    payload = {
        "amount_inr": 1000.0,
        "donor_name": "Invalid Pan Donor",
        "donor_email": "donor@example.org",
        "donor_pan": "INVALIDPAN123"  # Not 5 letters, 4 digits, 1 letter
    }
    response = await client.post("/api/v1/donations/orders", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_payment_signature_success(client: AsyncClient, test_db_session: AsyncSession):
    """Payment signature verification updates status to 'captured' and marks 80G issued."""
    # 1. Create order
    order_res = await client.post(
        "/api/v1/donations/orders",
        json={
            "amount_inr": 5000.0,
            "donor_name": "Ananya Sen",
            "donor_email": "ananya@example.org",
            "donor_pan": "BNZPS9988K",
            "donor_address": "Park Street, Kolkata"
        }
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["order_id"]

    # 2. Verify with valid signature
    verify_res = await client.post(
        "/api/v1/donations/verify",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_test998877",
            "razorpay_signature": "mock_valid_signature"
        }
    )
    assert verify_res.status_code == 200
    donation_data = verify_res.json()
    assert donation_data["payment_status"] == "captured"
    assert donation_data["tax_exemption_80g_issued"] is True
    assert donation_data["receipt_number"].startswith("AG360-")
    assert f"/api/v1/donations/{donation_data['id']}/receipt" in donation_data["receipt_pdf_url"]


@pytest.mark.asyncio
async def test_verify_payment_signature_invalid(client: AsyncClient):
    """Tampered or invalid signature returns 400 Bad Request."""
    # Create order
    order_res = await client.post(
        "/api/v1/donations/orders",
        json={
            "amount_inr": 500.0,
            "donor_name": "Donor X",
            "donor_email": "donorx@example.org"
        }
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["order_id"]

    # Verify with fraudulent signature
    verify_res = await client.post(
        "/api/v1/donations/verify",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake123",
            "razorpay_signature": "invalid_forged_hash"
        }
    )
    assert verify_res.status_code == 400
    assert "signature" in verify_res.json()["message"].lower()


@pytest.mark.asyncio
async def test_verify_payment_idempotency(client: AsyncClient, test_db_session: AsyncSession):
    """Re-verifying an already captured donation returns the existing record idempotently."""
    # Create campaign
    campaign = Campaign(
        title="Winter Street Dog Care",
        slug="winter-street-dog-care",
        description="Blankets and anti-rabies vaccination drives",
        target_amount_inr=100000.0,
        raised_amount_inr=0.0,
        is_active=True
    )
    test_db_session.add(campaign)
    await test_db_session.commit()
    await test_db_session.refresh(campaign)

    # Create order linked to campaign
    order_res = await client.post(
        "/api/v1/donations/orders",
        json={
            "amount_inr": 2000.0,
            "campaign_id": campaign.id,
            "donor_name": "Priya Patel",
            "donor_email": "priya@example.com"
        }
    )
    order_id = order_res.json()["order_id"]

    # First verification
    res1 = await client.post(
        "/api/v1/donations/verify",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_priya_1",
            "razorpay_signature": "mock_valid_signature"
        }
    )
    assert res1.status_code == 200
    assert res1.json()["payment_status"] == "captured"

    # Verify campaign raised amount is 2000
    await test_db_session.refresh(campaign)
    assert campaign.raised_amount_inr == 2000.0

    # Second verification (idempotent replay)
    res2 = await client.post(
        "/api/v1/donations/verify",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_priya_1",
            "razorpay_signature": "mock_valid_signature"
        }
    )
    assert res2.status_code == 200

    # Campaign must not be credited twice!
    await test_db_session.refresh(campaign)
    assert campaign.raised_amount_inr == 2000.0


@pytest.mark.asyncio
async def test_razorpay_webhook_payment_captured(client: AsyncClient, test_db_session: AsyncSession):
    """Webhook triggers background reconciliation and status update."""
    order_res = await client.post(
        "/api/v1/donations/orders",
        json={
            "amount_inr": 1500.0,
            "donor_name": "Webhook Donor",
            "donor_email": "webhook_donor@example.org"
        }
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["order_id"]

    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_webhook_999",
                    "order_id": order_id,
                    "method": "upi",
                    "amount": 150000
                }
            }
        }
    }

    res = await client.post(
        "/api/v1/donations/webhook",
        content=json.dumps(webhook_payload),
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 200

    # Check donation was updated to captured in DB
    stmt = select(Donation).where(Donation.razorpay_order_id == order_id)
    db_res = await test_db_session.execute(stmt)
    donation = db_res.scalar_one()
    assert donation.payment_status == "captured"
    assert donation.razorpay_payment_id == "pay_webhook_999"


@pytest.mark.asyncio
async def test_download_80g_receipt_pdf(client: AsyncClient, test_db_session: AsyncSession):
    """Section 80G tax receipt endpoint generates valid PDF binary with header."""
    donation = Donation(
        amount_inr=5000.0,
        currency="INR",
        donor_name="Dr. Vikram Sarabhai",
        donor_email="vikram@isro.org",
        donor_pan="ABCDE5555K",
        donor_address="ISRO HQ, Bengaluru, Karnataka",
        razorpay_order_id="order_test_80g",
        razorpay_payment_id="pay_test_80g",
        payment_status="captured",
        payment_method="UPI",
        tax_exemption_80g_issued=True,
        receipt_number="AG360-202627-889900"
    )
    test_db_session.add(donation)
    await test_db_session.commit()
    await test_db_session.refresh(donation)

    res = await client.get(f"/api/v1/donations/{donation.id}/receipt")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    # Verify PDF magic bytes '%PDF-'
    assert res.content[:4] == b"%PDF"
    assert len(res.content) > 1000  # Substantial PDF document


@pytest.mark.asyncio
async def test_transparency_summary(client: AsyncClient, test_db_session: AsyncSession, admin_user: User):
    """Transparency summary aggregates funds raised, allocated, categories, and active campaigns."""
    # Seed captured donations
    d1 = Donation(
        amount_inr=10000.0,
        payment_status="captured",
        razorpay_order_id="ord1",
        donor_name="Donor 1",
        donor_email="donor1@test.org"
    )
    d2 = Donation(
        amount_inr=5000.0,
        payment_status="captured",
        razorpay_order_id="ord2",
        donor_name="Donor 2",
        donor_email="donor2@test.org"
    )
    d_pending = Donation(
        amount_inr=3000.0,
        payment_status="created",
        razorpay_order_id="ord3",
        donor_name="Donor 3",
        donor_email="donor3@test.org"
    )
    test_db_session.add_all([d1, d2, d_pending])


    # Seed fund allocations
    a1 = FundAllocation(
        category="rescue_ops",
        title="Ambulance fuel & emergency medical kits",
        amount_inr=6000.0,
        allocation_date=date(2026, 10, 1),
        verified_by_id=admin_user.id
    )
    a2 = FundAllocation(
        category="food_feeding",
        title="100 bags of dog kibble for stray feeding",
        amount_inr=4000.0,
        allocation_date=date(2026, 10, 3),
        verified_by_id=admin_user.id
    )
    test_db_session.add_all([a1, a2])

    # Seed campaign
    camp = Campaign(
        title="Monsoon Trauma Care",
        slug="monsoon-trauma-care",
        description="Emergency shelter during monsoon floods",
        target_amount_inr=50000.0,
        raised_amount_inr=15000.0,
        is_active=True
    )
    test_db_session.add(camp)
    await test_db_session.commit()


    res = await client.get("/api/v1/donations/transparency")
    assert res.status_code == 200
    data = res.json()
    assert data["total_raised_inr"] == 15000.0  # 10000 + 5000 (pending excluded)
    assert data["total_allocated_inr"] == 10000.0  # 6000 + 4000
    assert data["donations_count"] == 2
    assert data["category_breakdown"]["rescue_ops"] == 6000.0
    assert data["category_breakdown"]["food_feeding"] == 4000.0
    assert len(data["recent_allocations"]) == 2
    assert len(data["active_campaigns"]) == 1
    assert data["active_campaigns"][0]["progress_percent"] == 30.0


@pytest.mark.asyncio
async def test_admin_fund_allocation_authorized_and_unauthorized(
    client: AsyncClient,
    admin_token: str,
    user_token: str
):
    """Admin can record audited expenditure; standard user is rejected with 403."""
    payload = {
        "category": "medical_supplies",
        "title": "Anti-rabies vaccines batch 2026-Q4",
        "description": "500 vials of Rabisin for community vaccination drives",
        "amount_inr": 12500.0,
        "allocation_date": "2026-10-05",
        "receipt_url": "https://storage.animalguardian360.org/receipts/vaccines_oct2026.pdf"
    }

    # Standard user attempt -> 403 Forbidden
    res_unauth = await client.post(
        "/api/v1/donations/allocations",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res_unauth.status_code == 403

    # Admin attempt -> 201 Created
    res_auth = await client.post(
        "/api/v1/donations/allocations",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_auth.status_code == 201
    created = res_auth.json()
    assert created["title"] == payload["title"]
    assert created["amount_inr"] == 12500.0
    assert created["receipt_url"] == payload["receipt_url"]


@pytest.mark.asyncio
async def test_campaign_creation_and_listing(
    client: AsyncClient,
    admin_token: str
):
    """Admin creates a fundraising campaign, which is publicly listable."""
    create_payload = {
        "title": "Puppy Critical Care Incubator Fund",
        "description": "Procuring 2 specialized neonatal oxygen incubators",
        "target_amount_inr": 80000.0,
        "cover_image_url": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b"
    }
    create_res = await client.post(
        "/api/v1/donations/campaigns",
        json=create_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 201
    camp_data = create_res.json()
    assert camp_data["title"] == create_payload["title"]
    assert camp_data["target_amount_inr"] == 80000.0
    assert camp_data["raised_amount_inr"] == 0.0
    assert camp_data["progress_percent"] == 0.0

    # Public list campaigns
    list_res = await client.get("/api/v1/donations/campaigns")
    assert list_res.status_code == 200
    campaigns = list_res.json()
    assert len(campaigns) >= 1
    assert any(c["title"] == create_payload["title"] for c in campaigns)
