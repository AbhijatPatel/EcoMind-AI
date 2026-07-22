"""
POST /generate-plan

Purpose: generate a personalized daily/weekly/monthly sustainability
roadmap. Requires that the user has already run /calculate-carbon at
least once — the plan is meaningless without knowing which categories
actually need attention, so this fails clearly rather than falling back
to a generic plan that ignores the user's real situation.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.plan import SustainabilityPlanResponse
from app.services.plan_generator import SubScores, generate_plan

router = APIRouter(tags=["plan"])
logger = get_logger(__name__)


@router.post("/generate-plan", response_model=SustainabilityPlanResponse)
async def create_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SustainabilityPlanResponse:
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .limit(1)
    )
    assessment = result.scalar_one_or_none()
    if assessment is None:
        raise NotFoundError(
            "No carbon assessment found yet. Run /calculate-carbon first so your plan can "
            "target your actual lifestyle instead of guessing."
        )

    plan = generate_plan(
        SubScores(
            transport_score=assessment.transport_score,
            food_score=assessment.food_score,
            energy_score=assessment.energy_score,
            lifestyle_score=assessment.lifestyle_score,
        )
    )

    logger.info(
        "Generated plan for user %s targeting %s (based on assessment %s)",
        current_user.id,
        plan.focus_areas,
        assessment.id,
    )

    return SustainabilityPlanResponse(
        based_on_score=assessment.overall_score,
        based_on_category=assessment.category,
        focus_areas=plan.focus_areas,
        daily=plan.daily,
        weekly=plan.weekly,
        monthly=plan.monthly,
    )
