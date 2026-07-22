"""
POST /challenge, GET /challenges, PATCH /challenges/{id}/complete

Purpose: create weekly eco challenges, list a user's challenge history,
and let them mark one complete.

POST /challenge does NOT require a prior carbon assessment — challenges
are meant to be a low-friction entry point (a new user should be able to
get a challenge on day one). If an assessment exists, the challenge
targets the user's weakest category; if not, it falls back to a fixed
default category so the app still behaves predictably.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import EcoMindError, NotFoundError
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.challenge import Challenge
from app.models.user import User
from app.schemas.challenge import ChallengeRequest, ChallengeResponse
from app.services.challenge_generator import CATEGORY_LABELS, VALID_CATEGORIES, generate_challenge

router = APIRouter(tags=["challenge"])
logger = get_logger(__name__)

_DEFAULT_CATEGORY_WITHOUT_ASSESSMENT = "lifestyle"
_LIST_LIMIT = 100


def _to_response(challenge: Challenge) -> ChallengeResponse:
    return ChallengeResponse(
        id=challenge.id,
        category=challenge.category,
        category_label=CATEGORY_LABELS[challenge.category],
        title=challenge.title,
        description=challenge.description,
        duration_days=challenge.duration_days,
        completed=challenge.completed,
        created_at=challenge.created_at,
    )


async def _weakest_category_or_default(user_id: str, db: AsyncSession) -> str:
    result = await db.execute(
        select(Assessment).where(Assessment.user_id == user_id).order_by(Assessment.created_at.desc()).limit(1)
    )
    assessment = result.scalar_one_or_none()
    if assessment is None:
        return _DEFAULT_CATEGORY_WITHOUT_ASSESSMENT

    sub_scores = {
        "transport": assessment.transport_score,
        "food": assessment.food_score,
        "energy": assessment.energy_score,
        "lifestyle": assessment.lifestyle_score,
    }
    return min(sub_scores, key=sub_scores.get)


@router.post("/challenge", response_model=ChallengeResponse, status_code=201)
async def create_challenge(
    payload: ChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChallengeResponse:
    if payload.category is not None and payload.category not in VALID_CATEGORIES:
        raise EcoMindError(
            f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}.", status_code=422
        )

    category = payload.category or await _weakest_category_or_default(current_user.id, db)

    count_result = await db.execute(
        select(func.count())
        .select_from(Challenge)
        .where(Challenge.user_id == current_user.id, Challenge.category == category)
    )
    challenges_received_in_category = count_result.scalar_one()

    generated = generate_challenge(category, challenges_received_in_category)

    challenge = Challenge(
        user_id=current_user.id,
        category=category,
        title=generated.title,
        description=generated.description,
        duration_days=generated.duration_days,
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)

    logger.info("Created challenge %s (%s) for user %s", challenge.id, category, current_user.id)

    return _to_response(challenge)


@router.get("/challenges", response_model=list[ChallengeResponse])
async def list_challenges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChallengeResponse]:
    result = await db.execute(
        select(Challenge)
        .where(Challenge.user_id == current_user.id)
        .order_by(Challenge.created_at.desc())
        .limit(_LIST_LIMIT)
    )
    return [_to_response(c) for c in result.scalars().all()]


@router.patch("/challenges/{challenge_id}/complete", response_model=ChallengeResponse)
async def complete_challenge(
    challenge_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChallengeResponse:
    result = await db.execute(
        select(Challenge).where(Challenge.id == challenge_id, Challenge.user_id == current_user.id)
    )
    challenge = result.scalar_one_or_none()
    # Same 404 whether the challenge doesn't exist or belongs to someone
    # else — never reveal that a given ID belongs to another user's data.
    if challenge is None:
        raise NotFoundError("Challenge not found.")

    challenge.completed = True
    await db.commit()
    await db.refresh(challenge)

    logger.info("Challenge %s marked complete by user %s", challenge.id, current_user.id)

    return _to_response(challenge)
