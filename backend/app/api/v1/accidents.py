"""
Accidents API: Road Accident Animal SOS flow, one-time secure dispatch action,
hospital dashboard, and 5-minute escalation cron endpoint.
"""
import asyncio
import json
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from app.core.dependencies import get_current_user, require_roles
from app.core.security import decode_token
from app.models.user import User
from app.models.hospital import VetHospital
from app.models.accident import AccidentAlert, AlertDispatch
from app.schemas.accident import (
    AccidentSOSCreate,
    AccidentAlertResponse,
    AlertDispatchResponse,
    DispatchActionRequest,
    DispatchActionResponse,
    HospitalCaseStatusUpdate,
    AccidentLiveStatusResponse
)
from app.services.accident_service import accident_service

router = APIRouter(prefix="/accidents", tags=["Road Accident SOS"])


def build_alert_response(alert: AccidentAlert) -> AccidentAlertResponse:
    dispatches = []
    for d in alert.dispatches or []:
        h_name = d.hospital.name if d.hospital else "Assigned Hospital"
        h_phone = d.hospital.phone if d.hospital else ""
        dispatches.append(
            AlertDispatchResponse(
                id=d.id,
                hospital_id=d.hospital_id,
                hospital_name=h_name,
                hospital_phone=h_phone,
                escalation_round=d.escalation_round,
                status=d.status,
                expires_at=d.expires_at,
                dispatched_at=d.dispatched_at
            )
        )

    accepted_name = alert.accepted_hospital.name if alert.accepted_hospital else None
    accepted_phone = alert.accepted_hospital.phone if alert.accepted_hospital else None

    return AccidentAlertResponse(
        id=alert.id,
        reporter_id=alert.reporter_id,
        reporter_phone=alert.reporter_phone,
        animal_type=alert.animal_type,
        condition_description=alert.condition_description,
        photo_url=alert.photo_url,
        latitude=alert.latitude,
        longitude=alert.longitude,
        address_text=alert.address_text,
        status=alert.status,
        accepted_hospital_id=alert.accepted_hospital_id,
        accepted_hospital_name=accepted_name,
        accepted_hospital_phone=accepted_phone,
        eta_minutes=alert.eta_minutes,
        created_at=alert.created_at,
        dispatches=dispatches
    )


def build_live_status_response(alert: AccidentAlert) -> AccidentLiveStatusResponse:
    dispatches = [
        AlertDispatchResponse(
            id=d.id,
            hospital_id=d.hospital_id,
            hospital_name=d.hospital.name if d.hospital else "Assigned Hospital",
            hospital_phone=d.hospital.phone if d.hospital else "",
            escalation_round=d.escalation_round,
            status=d.status,
            expires_at=d.expires_at,
            dispatched_at=d.dispatched_at
        )
        for d in alert.dispatches or []
    ]
    max_round = max([d.escalation_round for d in alert.dispatches], default=1)
    accepted_name = alert.accepted_hospital.name if alert.accepted_hospital else None
    accepted_phone = alert.accepted_hospital.phone if alert.accepted_hospital else None

    return AccidentLiveStatusResponse(
        alert_id=alert.id,
        status=alert.status,
        animal_type=alert.animal_type,
        accepted_hospital_name=accepted_name,
        accepted_hospital_phone=accepted_phone,
        eta_minutes=alert.eta_minutes,
        escalation_round=max_round,
        dispatches_count=len(dispatches),
        dispatches=dispatches,
        accepted_at=alert.accepted_at,
        reached_at=alert.reached_at,
        closed_at=alert.closed_at,
        created_at=alert.created_at
    )


@router.post(
    "/sos",
    response_model=AccidentAlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger Road Accident Animal SOS Emergency Flow"
)
async def report_road_accident(
    payload: AccidentSOSCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an urgent road accident alert with GPS coordinates and optional photo.
    Automatically identifies the 3 nearest registered hospitals and dispatches
    one-time cryptographic action links with a 5-minute escalation countdown.
    """
    reporter_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            claims = decode_token(token, expected_type="access")
            reporter_id = claims.get("sub")
        except Exception:
            pass

    alert = await accident_service.create_sos_alert(
        db=db,
        payload=payload,
        reporter_id=reporter_id
    )

    # Reload alert with relationships for response
    stmt = (
        select(AccidentAlert)
        .where(AccidentAlert.id == alert.id)
        .options(
            selectinload(AccidentAlert.dispatches).selectinload(AlertDispatch.hospital),
            selectinload(AccidentAlert.accepted_hospital)
        )
    )
    res = await db.execute(stmt)
    full_alert = res.scalar_one()

    return build_alert_response(full_alert)


@router.get(
    "/{alert_id}",
    response_model=AccidentAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Get status and live tracking of an accident alert"
)
async def get_accident_status(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AccidentAlert)
        .where(AccidentAlert.id == alert_id)
        .options(
            selectinload(AccidentAlert.dispatches).selectinload(AlertDispatch.hospital),
            selectinload(AccidentAlert.accepted_hospital)
        )
    )
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Accident alert not found")

    return build_alert_response(alert)


@router.get(
    "/dispatch/{token}",
    status_code=status.HTTP_200_OK,
    summary="View emergency dispatch details via one-time secure link"
)
async def get_dispatch_details(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Used by the hospital on clicking the emergency email/SMS action link."""
    stmt = (
        select(AlertDispatch)
        .where(AlertDispatch.secure_token == token)
        .options(
            selectinload(AlertDispatch.alert),
            selectinload(AlertDispatch.hospital)
        )
    )
    res = await db.execute(stmt)
    dispatch = res.scalar_one_or_none()
    if not dispatch:
        raise NotFoundError("Invalid or expired emergency dispatch token")

    alert = dispatch.alert
    return {
        "dispatch_id": dispatch.id,
        "dispatch_status": dispatch.status,
        "is_expired": dispatch.is_expired,
        "expires_at": dispatch.expires_at,
        "hospital_name": dispatch.hospital.name,
        "alert": {
            "id": alert.id,
            "status": alert.status,
            "animal_type": alert.animal_type,
            "condition_description": alert.condition_description,
            "photo_url": alert.photo_url,
            "address_text": alert.address_text,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "reporter_phone": alert.reporter_phone,
            "created_at": alert.created_at
        }
    }


@router.post(
    "/dispatch/{token}/action",
    response_model=DispatchActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept or Decline emergency dispatch via one-time link"
)
async def take_dispatch_action(
    token: str,
    payload: DispatchActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Hospital action: Accept or Decline.
    The first hospital to accept atomically locks the case.
    """
    accepted, message, alert = await accident_service.process_dispatch_action(
        db=db,
        token=token,
        payload=payload
    )

    return DispatchActionResponse(
        success=True,
        message=message,
        alert_status=alert.status,
        alert_id=alert.id,
        eta_minutes=alert.eta_minutes
    )


@router.get(
    "/hospital/dashboard",
    response_model=List[AccidentAlertResponse],
    status_code=status.HTTP_200_OK,
    summary="Hospital live dashboard: view incoming and accepted accident alerts"
)
async def get_hospital_dashboard(
    current_user: Annotated[User, Depends(require_roles(["hospital", "admin"]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Allows hospital staff to view alerts dispatched to their clinic or accepted by them.
    """
    # Find hospital linked to this user
    h_stmt = select(VetHospital).where(VetHospital.user_id == current_user.id)
    h_res = await db.execute(h_stmt)
    hospital = h_res.scalar_one_or_none()

    stmt = (
        select(AccidentAlert)
        .options(
            selectinload(AccidentAlert.dispatches).selectinload(AlertDispatch.hospital),
            selectinload(AccidentAlert.accepted_hospital)
        )
        .order_by(AccidentAlert.created_at.desc())
        .limit(50)
    )

    if hospital:
        # Filter for alerts assigned to this hospital or dispatched to them
        stmt = stmt.join(AccidentAlert.dispatches).where(
            AlertDispatch.hospital_id == hospital.id
        )

    res = await db.execute(stmt)
    alerts = res.scalars().unique().all()
    return [build_alert_response(a) for a in alerts]


@router.patch(
    "/{alert_id}/status",
    response_model=AccidentAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Update case status: reached or closed"
)
async def update_accident_case_status(
    alert_id: str,
    payload: HospitalCaseStatusUpdate,
    current_user: Annotated[User, Depends(require_roles(["hospital", "admin"]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Hospital marks case progress: 'reached' (rescue team arrived) or 'closed' (treated/admitted).
    """
    from datetime import datetime, timezone

    stmt = (
        select(AccidentAlert)
        .where(AccidentAlert.id == alert_id)
        .options(
            selectinload(AccidentAlert.dispatches).selectinload(AlertDispatch.hospital),
            selectinload(AccidentAlert.accepted_hospital)
        )
    )
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Accident alert not found")

    now = datetime.now(timezone.utc)
    alert.status = payload.status
    if payload.status == "reached":
        alert.reached_at = now
    elif payload.status == "closed":
        alert.closed_at = now

    await db.commit()
    await db.refresh(alert)
    return build_alert_response(alert)


@router.get(
    "/{alert_id}/live-status",
    response_model=AccidentLiveStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get real-time live triage status of a Road Accident SOS alert"
)
async def get_accident_live_status(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns real-time rescue status, accepted hospital details, and ambulance ETA countdown.
    """
    stmt = (
        select(AccidentAlert)
        .where(AccidentAlert.id == alert_id)
        .options(
            selectinload(AccidentAlert.dispatches).selectinload(AlertDispatch.hospital),
            selectinload(AccidentAlert.accepted_hospital)
        )
    )
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Accident alert not found")
    return build_live_status_response(alert)


@router.get(
    "/{alert_id}/stream",
    summary="Stream real-time SOS rescue updates via Server-Sent Events (SSE)"
)
async def stream_accident_live_status(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Streams live SSE events to citizen reporter browser with real-time ETA countdown.
    """
    async def event_generator():
        for _ in range(15):  # Stream active updates
            stmt = (
                select(AccidentAlert)
                .where(AccidentAlert.id == alert_id)
                .options(
                    selectinload(AccidentAlert.dispatches).selectinload(AlertDispatch.hospital),
                    selectinload(AccidentAlert.accepted_hospital)
                )
            )
            res = await db.execute(stmt)
            alert = res.scalar_one_or_none()
            if not alert:
                yield f"data: {json.dumps({'error': 'not_found'})}\n\n"
                break

            live_data = build_live_status_response(alert)
            yield f"data: {live_data.model_dump_json()}\n\n"

            if alert.status in ("reached", "closed"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post(
    "/cron/escalate",
    status_code=status.HTTP_200_OK,
    summary="Cron trigger to escalate alerts unanswered after 5 minutes"
)
async def trigger_escalation_worker(db: AsyncSession = Depends(get_db)):
    """
    Callable by external cron or Celery beat to advance escalation rounds for unanswered SOS cases.
    """
    escalated = await accident_service.escalate_unaccepted_alerts(db)
    return {"success": True, "escalated_alerts": escalated}
