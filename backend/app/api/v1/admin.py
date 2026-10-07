"""
Admin Panel API: Oversight, system KPI metrics, hospital verification,
anti-abuse strike management, and immutable audit trails.
"""
from datetime import datetime, timezone
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.user import User, Strike
from app.models.hospital import VetHospital
from app.models.accident import AccidentAlert
from app.models.report import CrueltyReport
from app.models.pet import LostFoundPost
from app.models.donation import Donation, FundAllocation
from app.models.audit import AuditLog
from app.schemas.admin import (
    AdminStatsResponse,
    HospitalVerifyRequest,
    HospitalAdminResponse,
    StrikeAdminResponse,
    AuditLogResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin Oversight & Management"])


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated platform-wide operational KPIs"
)
async def get_admin_stats(
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    """Returns platform stats across users, rescues, hospitals, cruelty reports, and funds."""
    # 1. Users
    u_res = await db.execute(select(func.count(User.id)))
    total_users = u_res.scalar() or 0

    # 2. Hospitals
    h_total = await db.execute(select(func.count(VetHospital.id)))
    total_hospitals = h_total.scalar() or 0
    h_pending = await db.execute(select(func.count(VetHospital.id)).where(VetHospital.is_verified == False))
    pending_hospitals = h_pending.scalar() or 0

    # 3. Accident Alerts
    a_total = await db.execute(select(func.count(AccidentAlert.id)))
    total_accidents = a_total.scalar() or 0
    a_active = await db.execute(
        select(func.count(AccidentAlert.id)).where(AccidentAlert.status.in_(["pending", "alerted", "accepted", "reached"]))
    )
    active_accidents = a_active.scalar() or 0

    # 4. Cruelty Reports
    r_total = await db.execute(select(func.count(CrueltyReport.id)))
    total_cruelty = r_total.scalar() or 0
    r_pending = await db.execute(select(func.count(CrueltyReport.id)).where(CrueltyReport.status == "submitted"))
    pending_reports = r_pending.scalar() or 0

    # 5. Pets
    p_total = await db.execute(select(func.count(LostFoundPost.id)))
    total_pets = p_total.scalar() or 0
    p_reunited = await db.execute(select(func.count(LostFoundPost.id)).where(LostFoundPost.status == "reunited"))
    reunited_pets = p_reunited.scalar() or 0


    # 6. Donations & Allocations
    d_res = await db.execute(
        select(func.coalesce(func.sum(Donation.amount_inr), 0.0)).where(Donation.payment_status == "captured")
    )
    total_donations = d_res.scalar() or 0.0

    alloc_res = await db.execute(select(func.coalesce(func.sum(FundAllocation.amount_inr), 0.0)))
    total_allocated = alloc_res.scalar() or 0.0

    # 7. Active Strikes
    s_res = await db.execute(select(func.count(Strike.id)))
    active_strikes = s_res.scalar() or 0

    return AdminStatsResponse(
        total_users=total_users,
        total_hospitals=total_hospitals,
        pending_hospitals=pending_hospitals,
        total_accidents=total_accidents,
        active_accidents=active_accidents,
        total_cruelty_reports=total_cruelty,
        pending_reports=pending_reports,
        total_lost_found_posts=total_pets,
        reunited_pets=reunited_pets,
        total_donations_raised_inr=float(total_donations),
        total_funds_allocated_inr=float(total_allocated),
        active_strikes_count=active_strikes
    )


@router.get(
    "/hospitals",
    response_model=List[HospitalAdminResponse],
    status_code=status.HTTP_200_OK,
    summary="List hospitals for administration and verification"
)
async def list_admin_hospitals(
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    verified: Optional[bool] = Query(None, description="Filter by verification state"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VetHospital).order_by(VetHospital.created_at.desc())
    if verified is not None:
        stmt = stmt.where(VetHospital.is_verified == verified)
    res = await db.execute(stmt)
    return [HospitalAdminResponse.model_validate(h) for h in res.scalars().all()]


@router.patch(
    "/hospitals/{hospital_id}/verify",
    response_model=HospitalAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify or unverify a registered veterinary hospital"
)
async def verify_hospital(
    hospital_id: str,
    payload: HospitalVerifyRequest,
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VetHospital).where(VetHospital.id == hospital_id)
    res = await db.execute(stmt)
    hosp = res.scalar_one_or_none()
    if not hosp:
        raise NotFoundError("Hospital not found")

    hosp.is_verified = payload.is_verified

    # Audit Log
    audit = AuditLog(
        actor_id=current_user.id,
        action="HOSPITAL_VERIFIED" if payload.is_verified else "HOSPITAL_UNVERIFIED",
        entity_name="vet_hospitals",
        entity_id=hosp.id,
        details={"hospital_name": hosp.name, "notes": payload.notes}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(hosp)
    return HospitalAdminResponse.model_validate(hosp)


@router.get(
    "/strikes",
    response_model=List[StrikeAdminResponse],
    status_code=status.HTTP_200_OK,
    summary="List community strikes issued against abusive users"
)
async def list_strikes(
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Strike).options(selectinload(Strike.user)).order_by(Strike.created_at.desc())
    res = await db.execute(stmt)
    strikes = res.scalars().all()
    results = []
    for s in strikes:
        results.append(
            StrikeAdminResponse(
                id=s.id,
                user_id=s.user_id,
                user_phone=s.user.phone if s.user else None,
                user_email=s.user.email if s.user else None,
                strike_number=s.strike_number,
                reason=s.reason,
                created_at=s.created_at
            )
        )
    return results


@router.delete(
    "/strikes/{strike_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke a strike and lift suspension if criteria met"
)
async def revoke_strike(
    strike_id: str,
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Strike).where(Strike.id == strike_id)
    res = await db.execute(stmt)
    strike = res.scalar_one_or_none()
    if not strike:
        raise NotFoundError("Strike record not found")

    user_id = strike.user_id

    # Retrieve user
    u_stmt = select(User).where(User.id == user_id)
    u_res = await db.execute(u_stmt)
    user = u_res.scalar_one_or_none()

    if user:
        user.strike_count = max(0, user.strike_count - 1)
        if user.strike_count < 3:
            user.reporting_suspended_until = None

    await db.delete(strike)

    # Audit Log
    audit = AuditLog(
        actor_id=current_user.id,
        action="STRIKE_REVOKED",
        entity_name="strikes",
        entity_id=strike_id,
        details={"user_id": user_id, "new_strike_count": user.strike_count if user else 0}
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": "Strike revoked successfully"}


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="List administrative actions audit trail"
)
async def list_audit_logs(
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    results = []
    for l in logs:
        results.append(
            AuditLogResponse(
                id=l.id,
                actor_id=l.actor_id,
                actor_email=l.actor.email if l.actor else None,
                action=l.action,
                entity_name=l.entity_name,
                entity_id=l.entity_id,
                details=l.details,
                created_at=l.created_at
            )
        )
    return results
