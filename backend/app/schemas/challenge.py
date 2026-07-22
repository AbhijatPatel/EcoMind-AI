from datetime import datetime

from pydantic import BaseModel


class ChallengeRequest(BaseModel):
    # Optional: let the user explicitly pick a category. If omitted, the
    # route infers it from the user's latest carbon assessment (weakest
    # category), falling back to a fixed default if no assessment exists yet.
    category: str | None = None


class ChallengeResponse(BaseModel):
    id: str
    category: str
    category_label: str
    title: str
    description: str
    duration_days: int
    completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
