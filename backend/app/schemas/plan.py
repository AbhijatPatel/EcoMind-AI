from pydantic import BaseModel


class SustainabilityPlanResponse(BaseModel):
    based_on_score: int
    based_on_category: str
    focus_areas: list[str]
    daily: list[str]
    weekly: list[str]
    monthly: list[str]
