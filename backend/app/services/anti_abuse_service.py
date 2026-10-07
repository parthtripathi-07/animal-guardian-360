"""
Anti-Abuse Service: 3-Strike Rule enforcement, sliding window rate limiting (5 reports/day),
and spatio-temporal duplicate detection (100m, 2 hours).
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RateLimitExceededError, ConflictError
from app.core.redis import cache_service
from app.models.user import User, Strike
from app.models.report import CrueltyReport
from app.services.google_maps import calculate_haversine_distance

logger = logging.getLogger(__name__)


class AntiAbuseService:
    RATE_LIMIT_MAX = 5  # 5 reports per day
    RATE_LIMIT_WINDOW_SECONDS = 86400  # 24 hours
    DUPLICATE_MAX_DISTANCE_METERS = 100.0  # 100 meters
    DUPLICATE_WINDOW_HOURS = 2  # 2 hours

    @classmethod
    async def enforce_rate_limit(cls, identifier: str) -> None:
        """
        Enforces maximum 5 reports per 24 hours per user ID or client IP.
        """
        rate_key = f"rate_limit:report:{identifier}"
        allowed, remaining = await cache_service.check_rate_limit(
            rate_key,
            max_requests=cls.RATE_LIMIT_MAX,
            window_seconds=cls.RATE_LIMIT_WINDOW_SECONDS
        )
        if not allowed:
            raise RateLimitExceededError(
                "You have reached the daily reporting limit of 5 reports per 24 hours. "
                "Please call 112 for urgent emergencies."
            )

    @classmethod
    async def check_duplicate_report(
        cls,
        db: AsyncSession,
        category: str,
        lat: float,
        lng: float
    ) -> Optional[CrueltyReport]:
        """
        Detects if another report of the same category was submitted within 100 meters
        in the past 2 hours to avoid overwhelming enforcement agencies.
        """
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=cls.DUPLICATE_WINDOW_HOURS)

        stmt = select(CrueltyReport).where(
            CrueltyReport.category == category,
            CrueltyReport.created_at >= two_hours_ago
        )
        res = await db.execute(stmt)
        recent_reports = res.scalars().all()

        for rep in recent_reports:
            dist = calculate_haversine_distance(lat, lng, rep.latitude, rep.longitude)
            if dist <= cls.DUPLICATE_MAX_DISTANCE_METERS:
                return rep

        return None

    @classmethod
    async def issue_strike(
        cls,
        db: AsyncSession,
        user: User,
        report_id: str,
        admin_id: str,
        reason: str
    ) -> Tuple[int, bool]:
        """
        Issues a formal strike against a user for submitting a fraudulent report.
        - Strike 1 & 2: Warning.
        - Strike 3: 30-day suspension of reporting privileges.
        Returns: (strike_number: int, is_suspended: bool)
        """
        user.strike_count += 1
        strike_number = user.strike_count

        strike = Strike(
            user_id=user.id,
            report_id=report_id,
            issued_by_id=admin_id,
            strike_number=strike_number,
            reason=reason,
            created_at=datetime.now(timezone.utc)
        )
        db.add(strike)

        is_suspended = False
        if strike_number >= 3:
            # Suspend user reporting for 30 days
            user.reporting_suspended_until = datetime.now(timezone.utc) + timedelta(days=30)
            is_suspended = True
            logger.warning(
                "User %s has reached Strike 3! Reporting privileges suspended for 30 days.",
                user.id
            )
        else:
            logger.info(
                "Strike %d issued to user %s. Warning recorded: %s",
                strike_number, user.id, reason
            )

        await db.commit()
        await db.refresh(user)
        return strike_number, is_suspended


anti_abuse_service = AntiAbuseService()
