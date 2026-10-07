"""
Animal Cruelty & Illegal Activity Reporting API:
- One-tap submission with photos/videos
- Nearest police station auto-finder & "Call 112" integration
- PDF complaint summary generation for physical filing
- 3-strike anti-abuse system & rate limiting
- Admin review queue
"""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query, Header, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.exceptions import NotFoundError, ConflictError, AccountSuspendedError
from app.core.security import decode_token
from app.models.user import User
from app.models.report import CrueltyReport, ReportMedia
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportMediaResponse,
    PoliceStationResponse,
    AdminReviewReportRequest,
    AdminReviewResponse
)
from app.services.police_service import police_service
from app.services.pdf_service import pdf_service
from app.services.anti_abuse_service import anti_abuse_service
from app.services.google_maps import calculate_haversine_distance

router = APIRouter(prefix="/reports", tags=["Animal Cruelty Reporting"])


def build_report_response(report: CrueltyReport) -> ReportResponse:
    media_list = [
        ReportMediaResponse(
            id=m.id,
            media_type=m.media_type,
            original_filename=m.original_filename,
            public_url=m.public_url,
            created_at=m.created_at
        )
        for m in report.media or []
    ]

    police_info = None
    if report.nearest_police_station_name:
        dist = calculate_haversine_distance(
            report.latitude, report.longitude,
            report.latitude + 0.005, report.longitude + 0.005
        )
        police_info = PoliceStationResponse(
            name=report.nearest_police_station_name,
            address=report.nearest_police_station_address or "",
            phone=report.nearest_police_station_phone or "112",
            distance_meters=dist
        )

    # Clean shareable message for WhatsApp/SMS
    shareable = (
        f"🚨 ANIMAL WELFARE COMPLAINT #{report.id[:8]}\n"
        f"Category: {report.category.upper().replace('_', ' ')}\n"
        f"Location: {report.address_text or f'{report.latitude}, {report.longitude}'}\n"
        f"Nearest Police Station: {report.nearest_police_station_name or 'Local Police'} (Call 112)\n"
        f"Summary: {report.description[:120]}...\n"
        f"Download PDF Complaint: https://animalguardian360.org/api/v1/reports/{report.id}/pdf"
    )

    return ReportResponse(
        id=report.id,
        reporter_id=None if report.is_anonymous else report.reporter_id,
        is_anonymous=report.is_anonymous,
        category=report.category,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        address_text=report.address_text,
        status=report.status,
        nearest_police_station=police_info,
        complaint_pdf_url=f"/api/v1/reports/{report.id}/pdf",
        shareable_summary=shareable,
        media=media_list,
        created_at=report.created_at
    )


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="File a report on animal cruelty, abandonment, or illegal wildlife trade"
)
async def submit_cruelty_report(
    payload: ReportCreate,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a report on illegal animal activity.
    1. Enforces daily rate limit (5/day) per user or IP.
    2. Prevents duplicate submissions within 100 meters & 2 hours.
    3. Auto-identifies the nearest police station for complaint preparation.
    4. Generates a formal PDF complaint summary for physical filing.
    """
    reporter = None
    rate_identifier = request.client.host if request.client else "unknown_ip"

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            claims = decode_token(token, expected_type="access")
            uid = claims.get("sub")
            stmt = select(User).where(User.id == uid)
            res = await db.execute(stmt)
            reporter = res.scalar_one_or_none()
            if reporter:
                rate_identifier = f"user_{reporter.id}"
                # Check 3-strike suspension
                if reporter.is_reporting_suspended:
                    raise AccountSuspendedError(
                        "Your reporting privileges are temporarily suspended due to previous false reports."
                    )
        except AccountSuspendedError:
            raise
        except Exception:
            pass

    # 1. Enforce rate limiting
    await anti_abuse_service.enforce_rate_limit(rate_identifier)

    # 2. Check for duplicate reports
    dup = await anti_abuse_service.check_duplicate_report(
        db=db,
        category=payload.category,
        lat=payload.latitude,
        lng=payload.longitude
    )
    if dup:
        raise ConflictError(
            "A report for this category and location was already submitted recently. "
            "Our review team is already processing it."
        )

    # 3. Find nearest police station
    police = await police_service.find_nearest_police_station(
        lat=payload.latitude,
        lng=payload.longitude
    )

    # 4. Save report
    report = CrueltyReport(
        reporter_id=reporter.id if reporter else None,
        is_anonymous=payload.is_anonymous,
        category=payload.category,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address_text=payload.address_text,
        nearest_police_station_name=police.name,
        nearest_police_station_address=police.address,
        nearest_police_station_phone=police.phone,
        status="pending_review"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # 5. Attach media records
    for m in payload.media:
        media_rec = ReportMedia(
            report_id=report.id,
            media_type=m.media_type,
            storage_key=m.storage_key,
            original_filename=m.original_filename,
            mime_type=m.mime_type,
            file_size_bytes=m.file_size_bytes,
            public_url=m.public_url or f"https://media.animalguardian360.org/{m.storage_key}",
            virus_scan_status="clean",
            exif_stripped=True
        )
        db.add(media_rec)

    await db.commit()
    await db.refresh(report)

    # Reload with media
    reload_stmt = (
        select(CrueltyReport)
        .where(CrueltyReport.id == report.id)
        .options(selectinload(CrueltyReport.media))
    )
    res = await db.execute(reload_stmt)
    full_report = res.scalar_one()

    return build_report_response(full_report)


@router.get(
    "/police/nearest",
    response_model=PoliceStationResponse,
    status_code=status.HTTP_200_OK,
    summary="Find nearest police station for emergency cruelty reporting"
)
async def get_nearest_police(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0)
):
    """Finds nearest police station to given GPS coordinates."""
    return await police_service.find_nearest_police_station(lat, lng)


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get report details by ID"
)
async def get_report_by_id(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(CrueltyReport)
        .where(CrueltyReport.id == report_id)
        .options(selectinload(CrueltyReport.media))
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundError("Cruelty report not found")

    return build_report_response(report)


@router.get(
    "/{report_id}/pdf",
    summary="Download formal PDF complaint summary for physical police submission"
)
async def download_complaint_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates and downloads the official Form AC-1 Complaint Summary PDF.
    """
    stmt = (
        select(CrueltyReport)
        .where(CrueltyReport.id == report_id)
        .options(selectinload(CrueltyReport.reporter))
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundError("Cruelty report not found")

    reporter_name = report.reporter.full_name if report.reporter else "Citizen Reporter"
    reporter_phone = report.reporter.phone if report.reporter else "On File"

    pdf_bytes = pdf_service.generate_cruelty_complaint_pdf(
        report_id=report.id,
        category=report.category,
        description=report.description,
        created_at=report.created_at,
        latitude=report.latitude,
        longitude=report.longitude,
        address_text=report.address_text,
        nearest_police_name=report.nearest_police_station_name,
        nearest_police_address=report.nearest_police_station_address,
        nearest_police_phone=report.nearest_police_station_phone,
        is_anonymous=report.is_anonymous,
        reporter_name=reporter_name,
        reporter_phone=reporter_phone
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Police_Complaint_{report.id[:8]}.pdf"
        }
    )


@router.get(
    "/admin/queue",
    response_model=List[ReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Admin review queue: browse submitted reports"
)
async def get_admin_report_queue(
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CrueltyReport).options(selectinload(CrueltyReport.media)).order_by(CrueltyReport.created_at.desc())
    if status_filter:
        stmt = stmt.where(CrueltyReport.status == status_filter)

    res = await db.execute(stmt)
    reports = res.scalars().all()
    return [build_report_response(r) for r in reports]


@router.post(
    "/admin/{report_id}/review",
    response_model=AdminReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin review action: mark verified, action taken, dismissed, or fake (3-strike)"
)
async def review_report(
    report_id: str,
    payload: AdminReviewReportRequest,
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
    db: AsyncSession = Depends(get_db)
):
    """
    Admin review action. Marking as 'fake' triggers the 3-strike anti-abuse system:
    - Strike 1 & 2: Warning
    - Strike 3: Suspends reporting permissions for 30 days
    """
    from datetime import datetime, timezone

    stmt = (
        select(CrueltyReport)
        .where(CrueltyReport.id == report_id)
        .options(selectinload(CrueltyReport.reporter))
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundError("Report not found")

    report.status = payload.status
    report.admin_notes = payload.admin_notes
    report.reviewed_by_id = current_user.id
    report.reviewed_at = datetime.now(timezone.utc)

    strike_issued = False
    strike_num = None
    is_suspended = False
    message = f"Report marked as '{payload.status}' successfully."

    # If marked as fake and has a reporter account, issue strike
    if payload.status == "fake" and report.reporter:
        strike_num, is_suspended = await anti_abuse_service.issue_strike(
            db=db,
            user=report.reporter,
            report_id=report.id,
            admin_id=current_user.id,
            reason=payload.strike_reason or "Submitting false or fabricated cruelty report"
        )
        strike_issued = True
        if is_suspended:
            message = (
                f"Report marked as fake. Strike {strike_num} issued! "
                f"User account suspended from reporting for 30 days."
            )
        else:
            message = f"Report marked as fake. Strike {strike_num} issued with formal warning."

    await db.commit()
    await db.refresh(report)

    return AdminReviewResponse(
        success=True,
        report_id=report.id,
        status=report.status,
        admin_notes=report.admin_notes,
        strike_issued=strike_issued,
        strike_number=strike_num,
        user_suspended=is_suspended,
        message=message
    )
