"""
Admin Panel Tests: Operations KPIs, Hospital Verification, Strike Revocation, and Audit Trail.
"""
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, Strike
from app.models.hospital import VetHospital
from app.models.accident import AccidentAlert
from app.models.report import CrueltyReport
from app.models.pet import Pet, LostFoundPost
from app.models.donation import Donation
from app.models.audit import AuditLog


@pytest.mark.asyncio
async def test_admin_stats_unauthorized(client: AsyncClient, user_token: str):
    """Standard user is blocked from viewing admin operations metrics (403 Forbidden)."""
    res = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_stats_authorized(
    client: AsyncClient,
    admin_token: str,
    test_db_session: AsyncSession
):
    """Admin receives unified KPI summary across all operational subsystems."""
    # Seed mock hospital
    hosp = VetHospital(
        name="Indira Nagar Vet Clinic",
        phone="+919876543210",
        address="100 Feet Rd, Bengaluru",
        latitude=12.9716,
        longitude=77.5946,
        is_verified=False,
        is_active=True
    )
    # Seed mock report
    rep = CrueltyReport(
        category="cruelty",
        description="Dog chained in rain without shelter",
        latitude=12.9716,
        longitude=77.5946,
        status="submitted"
    )
    # Seed mock donation
    don = Donation(
        amount_inr=5000.0,
        donor_name="Suresh K",
        donor_email="suresh@test.org",
        razorpay_order_id="order_admin_test",
        payment_status="captured"
    )
    test_db_session.add_all([hosp, rep, don])
    await test_db_session.commit()

    res = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_hospitals"] >= 1
    assert data["pending_hospitals"] >= 1
    assert data["total_cruelty_reports"] >= 1
    assert data["pending_reports"] >= 1
    assert data["total_donations_raised_inr"] >= 5000.0


@pytest.mark.asyncio
async def test_admin_verify_hospital(
    client: AsyncClient,
    admin_token: str,
    test_db_session: AsyncSession
):
    """Admin can verify a veterinary hospital and an audit log entry is recorded."""
    hosp = VetHospital(
        name="Animal Life Hospital",
        phone="+919876543211",
        address="Sector 14, Gurugram, Haryana",
        latitude=28.4595,
        longitude=77.0266,
        is_verified=False,
        is_active=True
    )
    test_db_session.add(hosp)
    await test_db_session.commit()
    await test_db_session.refresh(hosp)

    # Verify hospital
    verify_res = await client.patch(
        f"/api/v1/admin/hospitals/{hosp.id}/verify",
        json={"is_verified": True, "notes": "Physical clinic inspection completed by field officer"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified"] is True

    # Check DB state
    await test_db_session.refresh(hosp)
    assert hosp.is_verified is True

    # Check Audit Log created
    audit_stmt = select(AuditLog).where(AuditLog.entity_id == hosp.id)
    audit_res = await test_db_session.execute(audit_stmt)
    log = audit_res.scalar_one_or_none()
    assert log is not None
    assert log.action == "HOSPITAL_VERIFIED"
    assert "field officer" in log.details.get("notes", "")


@pytest.mark.asyncio
async def test_admin_list_strikes_and_revoke(
    client: AsyncClient,
    admin_token: str,
    regular_user: User,
    test_db_session: AsyncSession
):
    """Admin lists strikes, revokes a strike, and lifts reporting suspension."""
    # Put user in suspended state with 3 strikes
    now = datetime.now(timezone.utc)
    regular_user.strike_count = 3
    regular_user.reporting_suspended_until = now + timedelta(days=30)
    test_db_session.add(regular_user)

    strike1 = Strike(user_id=regular_user.id, strike_number=1, reason="Fake test report 1")
    strike2 = Strike(user_id=regular_user.id, strike_number=2, reason="Fake test report 2")
    strike3 = Strike(user_id=regular_user.id, strike_number=3, reason="Repeated spam report 3")
    test_db_session.add_all([strike1, strike2, strike3])
    await test_db_session.commit()
    await test_db_session.refresh(strike3)

    # 1. Admin lists strikes
    list_res = await client.get("/api/v1/admin/strikes", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_res.status_code == 200
    strikes = list_res.json()
    assert len(strikes) >= 3

    # 2. Admin revokes strike 3
    del_res = await client.delete(f"/api/v1/admin/strikes/{strike3.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 200

    # 3. Check user state: strike_count reduced to 2 and suspension cleared!
    await test_db_session.refresh(regular_user)
    assert regular_user.strike_count == 2
    assert regular_user.reporting_suspended_until is None

    # 4. Check audit log
    audit_stmt = select(AuditLog).where(AuditLog.entity_id == strike3.id)
    audit_res = await test_db_session.execute(audit_stmt)
    audit_log = audit_res.scalar_one_or_none()
    assert audit_log is not None
    assert audit_log.action == "STRIKE_REVOKED"


@pytest.mark.asyncio
async def test_admin_list_audit_logs(
    client: AsyncClient,
    admin_token: str,
    admin_user: User,
    test_db_session: AsyncSession
):
    """Admin can list platform audit trail logs chronologically."""
    log1 = AuditLog(
        actor_id=admin_user.id,
        action="REPORT_APPROVED",
        entity_name="cruelty_reports",
        entity_id="rep_test_123",
        details={"case_notes": "Police station notified"}
    )
    test_db_session.add(log1)
    await test_db_session.commit()

    res = await client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1
    assert any(l["action"] == "REPORT_APPROVED" for l in logs)
