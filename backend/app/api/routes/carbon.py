"""
POST /calculate-carbon

Purpose: calculate environmental impact score from lifestyle inputs.

Works for guests (no auth token) so the landing page's "no account required
to see your first score" promise actually holds — a guest gets the score
computed and returned but not saved. A logged-in user (valid bearer token)
gets the same computation, persisted to their assessment history so it can
feed /generate-plan, /challenge, and the future progress dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.carbon import CarbonAssessmentRequest, CarbonAssessmentResponse
from app.services.carbon_engine import CarbonInputs, compute_carbon_score

router = APIRouter(tags=["carbon"])
logger = get_logger(__name__)


@router.post("/calculate-carbon", response_model=CarbonAssessmentResponse, status_code=201)
async def calculate_carbon(
    payload: CarbonAssessmentRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> CarbonAssessmentResponse:
    result = compute_carbon_score(
        CarbonInputs(
            vehicle_type=payload.vehicle_type,
            distance_km_per_day=payload.distance_km_per_day,
            diet_type=payload.diet_type,
            meat_meals_per_week=payload.meat_meals_per_week,
            electricity_kwh_per_month=payload.electricity_kwh_per_month,
            ac_hours_per_day=payload.ac_hours_per_day,
            shopping_trips_per_month=payload.shopping_trips_per_month,
            recycles=payload.recycles,
        )
    )

    if current_user is None:
        logger.info("Guest carbon assessment: score=%d category=%s", result.overall_score, result.category.value)
        return CarbonAssessmentResponse(
            saved=False,
            overall_score=result.overall_score,
            category=result.category,
            transport_score=result.transport_score,
            food_score=result.food_score,
            energy_score=result.energy_score,
            lifestyle_score=result.lifestyle_score,
        )

    assessment = Assessment(
        user_id=current_user.id,
        inputs=payload.model_dump(mode="json"),
        overall_score=result.overall_score,
        category=result.category.value,
        transport_score=result.transport_score,
        food_score=result.food_score,
        energy_score=result.energy_score,
        lifestyle_score=result.lifestyle_score,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    logger.info(
        "Carbon assessment %s for user %s: score=%d category=%s",
        assessment.id,
        current_user.id,
        result.overall_score,
        result.category.value,
    )

    return CarbonAssessmentResponse(
        id=assessment.id,
        saved=True,
        overall_score=assessment.overall_score,
        category=result.category,
        transport_score=assessment.transport_score,
        food_score=assessment.food_score,
        energy_score=assessment.energy_score,
        lifestyle_score=assessment.lifestyle_score,
        created_at=assessment.created_at,
    )
