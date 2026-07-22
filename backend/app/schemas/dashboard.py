from datetime import datetime

from pydantic import BaseModel


class ScorePoint(BaseModel):
    date: datetime
    score: int


class LatestAssessment(BaseModel):
    overall_score: int
    category: str
    transport_score: int
    food_score: int
    energy_score: int
    lifestyle_score: int
    created_at: datetime


class ChallengeSummary(BaseModel):
    id: str
    title: str
    category: str
    completed: bool
    created_at: datetime


class DashboardResponse(BaseModel):
    latest: LatestAssessment | None
    history: list[ScorePoint]
    challenges: list[ChallengeSummary]
