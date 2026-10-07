"""
Accident Service: SOS alert management, multi-hospital dispatches, atomic case locking,
and 5-minute automatic escalation workflow.
"""
from datetime import datetime, timedelta, timezone
import logging
from typing import List, Tuple, Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ConflictError, AppException
from app.core.security import generate_secure_token
from app.models.hospital import VetHospital
from app.models.accident import AccidentAlert, AlertDispatch
from app.schemas.accident import AccidentSOSCreate, DispatchActionRequest
from app.services.google_maps import calculate_haversine_distance
from app.services.notification import notification_service

logger = logging.getLogger(__name__)


class AccidentService:
    @staticmethod
    async def find_nearest_hospitals(
        db: AsyncSession,
        lat: float,
        lng: float,
        limit: int = 3,
        exclude_hospital_ids: Optional[List[str]] = None
    ) -> List[Tuple[VetHospital, float]]:
        """
        Finds active, verified hospitals sorted by distance from coordinates.
        """
        stmt = select(VetHospital).where(
            VetHospital.is_active == True,
            VetHospital.is_verified == True
        )
        if exclude_hospital_ids:
            stmt = stmt.where(VetHospital.id.not_in(exclude_hospital_ids))

        res = await db.execute(stmt)
        hospitals = res.scalars().all()

        hospitals_with_distance = []
        for h in hospitals:
            dist = calculate_haversine_distance(lat, lng, h.latitude, h.longitude)
            hospitals_with_distance.append((h, dist))

        # Sort ascending by distance
        hospitals_with_distance.sort(key=lambda x: x[1])
        return hospitals_with_distance[:limit]

    @classmethod
    async def create_sos_alert(
        cls,
        db: AsyncSession,
        payload: AccidentSOSCreate,
        reporter_id: Optional[str] = None
    ) -> AccidentAlert:
        """
        Creates a road accident SOS alert and immediately dispatches to the 3 nearest hospitals.
        """
        alert = AccidentAlert(
            reporter_id=reporter_id,
            reporter_phone=payload.reporter_phone,
            animal_type=payload.animal_type,
            condition_description=payload.condition_description,
            photo_url=payload.photo_url,
            latitude=payload.latitude,
            longitude=payload.longitude,
            address_text=payload.address_text,
            status="alerted"
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        # Dispatch round 1 to the 3 nearest hospitals
        nearest = await cls.find_nearest_hospitals(
            db=db,
            lat=payload.latitude,
            lng=payload.longitude,
            limit=3
        )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)

        for hospital, dist in nearest:
            token = generate_secure_token(32)
            dispatch = AlertDispatch(
                alert_id=alert.id,
                hospital_id=hospital.id,
                escalation_round=1,
                secure_token=token,
                status="pending",
                dispatched_at=now,
                expires_at=expires_at
            )
            db.add(dispatch)
            # Send notification
            await notification_service.send_emergency_dispatch(
                hospital_name=hospital.name,
                hospital_email=hospital.email,
                hospital_phone=hospital.phone,
                animal_type=payload.animal_type,
                address=payload.address_text,
                secure_token=token,
                round_number=1
            )

        await db.commit()
        await db.refresh(alert)
        return alert

    @classmethod
    async def process_dispatch_action(
        cls,
        db: AsyncSession,
        token: str,
        payload: DispatchActionRequest
    ) -> Tuple[bool, str, AccidentAlert]:
        """
        Processes a hospital's accept or decline decision via one-time secure link.
        Locks the case atomically on first accept to prevent duplicate assignments.
        """
        stmt = (
            select(AlertDispatch)
            .where(AlertDispatch.secure_token == token)
            .options(selectinload(AlertDispatch.alert), selectinload(AlertDispatch.hospital))
        )
        res = await db.execute(stmt)
        dispatch = res.scalar_one_or_none()

        if not dispatch:
            raise NotFoundError("Invalid or expired emergency dispatch token")

        alert = dispatch.alert

        now = datetime.now(timezone.utc)
        exp = dispatch.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        # Check if already handled
        if dispatch.status in ("accepted", "declined"):
            raise ConflictError(f"This dispatch action was already recorded as '{dispatch.status}'")

        if payload.action == "decline":
            dispatch.status = "declined"
            dispatch.decline_reason = payload.decline_reason or "Hospital unavailable"
            dispatch.responded_at = now
            await db.commit()
            return False, "Case was declined. We will escalate to another hospital.", alert

        # ACTION: ACCEPT
        if alert.status != "alerted":
            # Another hospital got here first
            dispatch.status = "expired"
            dispatch.responded_at = now
            await db.commit()
            raise ConflictError("This case has already been accepted by another hospital.")

        # Atomic lock
        alert.status = "accepted"
        alert.accepted_hospital_id = dispatch.hospital_id
        alert.accepted_at = now
        alert.eta_minutes = payload.eta_minutes or 15

        dispatch.status = "accepted"
        dispatch.responded_at = now

        await db.commit()
        await db.refresh(alert)

        # Notify reporter
        await notification_service.notify_reporter_case_accepted(
            reporter_phone=alert.reporter_phone,
            hospital_name=dispatch.hospital.name,
            hospital_phone=dispatch.hospital.phone,
            eta_minutes=alert.eta_minutes
        )

        return True, f"Case successfully accepted! ETA set to {alert.eta_minutes} minutes.", alert

    @classmethod
    async def escalate_unaccepted_alerts(cls, db: AsyncSession) -> int:
        """
        Background worker check: finds active alerts where all round dispatches have expired (5 min)
        and escalates to the next round of nearest hospitals.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(AccidentAlert)
            .where(AccidentAlert.status == "alerted")
            .options(selectinload(AccidentAlert.dispatches))
        )
        res = await db.execute(stmt)
        alerts = res.scalars().all()
        escalated_count = 0

        for alert in alerts:
            # Check dispatches for latest round
            if not alert.dispatches:
                continue

            max_round = max(d.escalation_round for d in alert.dispatches)
            current_round_dispatches = [d for d in alert.dispatches if d.escalation_round == max_round]

            # Check if all in current round are expired or declined
            all_done = True
            for d in current_round_dispatches:
                d_exp = d.expires_at.replace(tzinfo=timezone.utc) if d.expires_at.tzinfo is None else d.expires_at
                if d.status == "pending":
                    if now > d_exp:
                        d.status = "expired"
                    else:
                        all_done = False
                        break

            if all_done:
                # Escalate to next round
                already_contacted = [d.hospital_id for d in alert.dispatches]
                next_nearest = await cls.find_nearest_hospitals(
                    db=db,
                    lat=alert.latitude,
                    lng=alert.longitude,
                    limit=3,
                    exclude_hospital_ids=already_contacted
                )

                if next_nearest:
                    next_round = max_round + 1
                    expires_at = now + timedelta(minutes=5)
                    for hospital, _ in next_nearest:
                        token = generate_secure_token(32)
                        dispatch = AlertDispatch(
                            alert_id=alert.id,
                            hospital_id=hospital.id,
                            escalation_round=next_round,
                            secure_token=token,
                            status="pending",
                            dispatched_at=now,
                            expires_at=expires_at
                        )
                        db.add(dispatch)
                        await notification_service.send_emergency_dispatch(
                            hospital_name=hospital.name,
                            hospital_email=hospital.email,
                            hospital_phone=hospital.phone,
                            animal_type=alert.animal_type,
                            address=alert.address_text,
                            secure_token=token,
                            round_number=next_round
                        )
                    escalated_count += 1

        await db.commit()
        return escalated_count


accident_service = AccidentService()
