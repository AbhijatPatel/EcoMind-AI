"""
Weekly eco-challenge generator.

Same pattern as carbon_engine and plan_generator: pure Python, no LLM call,
no randomness. Challenge *selection* is deterministic given (category,
how many challenges this user has already received in that category) —
this is what lets repeated calls rotate through a category's pool instead
of either always returning the same challenge or picking one unpredictably.
"""

from dataclasses import dataclass

_CHALLENGE_POOL: dict[str, list[dict]] = {
    "transport": [
        {
            "title": "7-Day Car-Light Challenge",
            "description": "Replace at least one car trip per day with walking, biking, or public transport.",
            "duration_days": 7,
        },
        {
            "title": "One-Week Carpool Challenge",
            "description": "Share a ride for at least 3 trips this week instead of driving alone.",
            "duration_days": 7,
        },
    ],
    "food": [
        {
            "title": "7-Day Plant-Forward Challenge",
            "description": "Make at least one meal per day fully plant-based for a week.",
            "duration_days": 7,
        },
        {
            "title": "Meatless Weekdays Challenge",
            "description": "Go meat-free every weekday this week (weekends are up to you).",
            "duration_days": 7,
        },
    ],
    "energy": [
        {
            "title": "7-Day Standby Power Challenge",
            "description": "Fully switch off (not just standby) all non-essential devices every night for a week.",
            "duration_days": 7,
        },
        {
            "title": "One-Week Thermostat Challenge",
            "description": "Adjust your thermostat by 2 degrees in the energy-saving direction for a full week.",
            "duration_days": 7,
        },
    ],
    "lifestyle": [
        {
            "title": "7-Day Plastic Reduction Challenge",
            "description": "Avoid single-use plastic for a full week — bring your own bags, bottles, and containers.",
            "duration_days": 7,
        },
        {
            "title": "One-Week No-Impulse-Buy Challenge",
            "description": "Go a full week without any non-essential purchases, planned or impulse.",
            "duration_days": 7,
        },
    ],
}

CATEGORY_LABELS = {
    "transport": "Transportation",
    "food": "Food",
    "energy": "Energy",
    "lifestyle": "Shopping & waste",
}
_CATEGORY_LABELS = CATEGORY_LABELS  # internal alias, kept for existing references below

VALID_CATEGORIES = set(_CHALLENGE_POOL.keys())


@dataclass(frozen=True)
class GeneratedChallenge:
    title: str
    description: str
    duration_days: int
    category_label: str


def generate_challenge(category: str, challenges_received_in_category: int) -> GeneratedChallenge:
    """
    category: one of transport/food/energy/lifestyle.
    challenges_received_in_category: how many challenges this user has
        already been given in this category (used to rotate through the
        pool deterministically rather than repeating challenge #1 forever).
    """
    if category not in _CHALLENGE_POOL:
        raise ValueError(f"Unknown challenge category: {category!r}")

    pool = _CHALLENGE_POOL[category]
    index = challenges_received_in_category % len(pool)
    chosen = pool[index]

    return GeneratedChallenge(
        title=chosen["title"],
        description=chosen["description"],
        duration_days=chosen["duration_days"],
        category_label=_CATEGORY_LABELS[category],
    )
