"""
GET /dashboard

Purpose: power the dashboard page — latest score, score history for the
progress chart, and recent challenges. Requires auth (not optional, unlike
/calculate-carbon) since this is inherently account-scoped data with
nothing meaningful to show a guest.

A single aggregating endpoint rather than three separate calls
(latest score / history / challenges) so the frontend can render the whole
dashboard from one request instead of waterfalling three, which matters
more here than for the calculator since this is a page people land on
directly, not a result of an action they just took.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.challenge import Challenge
from app.models.user import User
from app.schemas.dashboard import ChallengeSummary, DashboardResponse, LatestAssessment, ScorePoint

router = APIRouter(tags=["dashboard"])

HISTORY_LIMIT = 20
CHALLENGES_LIMIT = 10


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    history_result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .limit(HISTORY_LIMIT)
    )
    assessments = list(history_result.scalars().all())

    latest = None
    if assessments:
        most_recent = assessments[0]
        latest = LatestAssessment(
            overall_score=most_recent.overall_score,
            category=most_recent.category,
            transport_score=most_recent.transport_score,
            food_score=most_recent.food_score,
            energy_score=most_recent.energy_score,
            lifestyle_score=most_recent.lifestyle_score,
            created_at=most_recent.created_at,
        )

    # Chart wants oldest-first, DB query fetched newest-first.
    history = [
        ScorePoint(date=a.created_at, score=a.overall_score) for a in reversed(assessments)
    ]

    challenges_result = await db.execute(
        select(Challenge)
        .where(Challenge.user_id == current_user.id)
        .order_by(Challenge.created_at.desc())
        .limit(CHALLENGES_LIMIT)
    )
    challenges = [
        ChallengeSummary(
            id=c.id,
            title=c.title,
            category=c.category,
            completed=c.completed,
            created_at=c.created_at,
        )
        for c in challenges_result.scalars().all()
    ]

    return DashboardResponse(latest=latest, history=history, challenges=challenges)
