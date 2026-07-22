"""
Request/response schemas for POST /calculate-carbon.

Field-level validation (ge/le bounds) rejects nonsensical input — e.g. a
negative commute distance — before it ever reaches the scoring engine,
rather than relying on the engine to clamp bad data silently.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.carbon_engine import DietType, ImpactCategory, VehicleType


class CarbonAssessmentRequest(BaseModel):
    vehicle_type: VehicleType
    distance_km_per_day: float = Field(ge=0, le=500)
    diet_type: DietType
    meat_meals_per_week: int = Field(ge=0, le=21)
    electricity_kwh_per_month: float = Field(ge=0, le=5000)
    ac_hours_per_day: float = Field(ge=0, le=24)
    shopping_trips_per_month: int = Field(ge=0, le=60)
    recycles: bool


class CarbonAssessmentResponse(BaseModel):
    id: str | None = None
    saved: bool
    overall_score: int
    category: ImpactCategory
    transport_score: int
    food_score: int
    energy_score: int
    lifestyle_score: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
