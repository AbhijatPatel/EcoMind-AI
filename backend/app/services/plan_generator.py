"""
Sustainability plan generator.

Like the carbon engine, this is pure Python with no LLM call — the plan is
built by ranking the user's four carbon sub-scores (transport, food, energy,
lifestyle) weakest-first, then pulling targeted actions from a curated pool
for the two weakest categories. This keeps the plan reproducible and
testable, and keeps "which categories need the most help" as a transparent,
auditable decision rather than something an LLM decides differently each call.

The action pools themselves are illustrative starting content — reasonable,
realistic suggestions, not the output of a research process. They're a good
candidate for expansion/refinement once there's real user feedback on which
suggestions people actually find worth doing.
"""

from dataclasses import dataclass

# Each category maps to a small pool of actions per time horizon. Kept short
# and specific per the "avoid unrealistic advice" principle — no vague
# "consume less" entries.
_ACTION_POOL: dict[str, dict[str, list[str]]] = {
    "transport": {
        "daily": ["Combine errands into a single trip today to cut short car journeys."],
        "weekly": ["Swap one car commute this week for public transport, biking, or walking."],
        "monthly": ["Map out a realistic public-transport or carpool route for your regular commute."],
    },
    "food": {
        "daily": ["Make one meal today fully plant-based instead of meat-based."],
        "weekly": ["Plan two meat-free dinners this week ahead of time so it's not a last-minute decision."],
        "monthly": ["Try a week-long plant-forward meal plan to see what realistically fits your routine."],
    },
    "energy": {
        "daily": ["Unplug or switch off devices on standby before you leave the house today."],
        "weekly": ["Shift 2-3 loads of laundry or dishwashing this week to off-peak hours."],
        "monthly": ["Get a home energy check (many utilities offer this free) to find your biggest draw."],
    },
    "lifestyle": {
        "daily": ["Skip one non-essential purchase today and note how it felt."],
        "weekly": ["Set aside recyclables properly all week and confirm your local collection rules."],
        "monthly": ["Do a one-month 'buy nothing new' challenge for a single category (e.g. clothes)."],
    },
}

_CATEGORY_LABELS = {
    "transport": "Transportation",
    "food": "Food",
    "energy": "Energy",
    "lifestyle": "Shopping & waste",
}


@dataclass(frozen=True)
class SubScores:
    transport_score: int
    food_score: int
    energy_score: int
    lifestyle_score: int


@dataclass(frozen=True)
class SustainabilityPlan:
    daily: list[str]
    weekly: list[str]
    monthly: list[str]
    focus_areas: list[str]  # human-readable labels of the categories this plan targets


def _weakest_categories(scores: SubScores, count: int = 2) -> list[str]:
    ranked = sorted(
        [
            ("transport", scores.transport_score),
            ("food", scores.food_score),
            ("energy", scores.energy_score),
            ("lifestyle", scores.lifestyle_score),
        ],
        key=lambda pair: pair[1],
    )
    return [category for category, _ in ranked[:count]]


def generate_plan(scores: SubScores) -> SustainabilityPlan:
    weakest = _weakest_categories(scores, count=2)

    daily = [_ACTION_POOL[cat]["daily"][0] for cat in weakest]
    weekly = [_ACTION_POOL[cat]["weekly"][0] for cat in weakest]
    monthly = [_ACTION_POOL[cat]["monthly"][0] for cat in weakest]

    return SustainabilityPlan(
        daily=daily,
        weekly=weekly,
        monthly=monthly,
        focus_areas=[_CATEGORY_LABELS[cat] for cat in weakest],
    )
