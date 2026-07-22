"""
Carbon footprint scoring engine.

Deliberately pure Python with no I/O, no randomness, and no LLM calls.
The same inputs always produce the same score — this is what lets the
AI layer (Phase 4) *explain* a number instead of *inventing* one, and
lets us unit-test the score directly against known inputs.

IMPORTANT — model accuracy disclaimer:
The emission factors and weights below are a simplified heuristic proxy,
not a peer-reviewed life-cycle-assessment (LCA) model. They're good enough
to rank relative lifestyle choices and drive behavioral nudges ("fewer car
km = higher score"), but should NOT be presented to users as precise
kg-CO2 accounting. Before any real launch, these constants should be
replaced or calibrated against a recognized source (e.g. EPA, DEFRA, or
IPCC emission factor tables) and reviewed by someone with domain
expertise — this is flagged here so it isn't mistaken for verified science.
"""

from dataclasses import dataclass
from enum import Enum


class VehicleType(str, Enum):
    NONE = "none"
    BIKE = "bike"
    PUBLIC_TRANSPORT = "public_transport"
    ELECTRIC_CAR = "electric_car"
    PETROL_CAR = "petrol_car"
    DIESEL_CAR = "diesel_car"


class DietType(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    FLEXITARIAN = "flexitarian"
    NON_VEGETARIAN = "non_vegetarian"


class ImpactCategory(str, Enum):
    ECO_CHAMPION = "Eco Champion"
    GREEN_LIFESTYLE = "Green Lifestyle"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    HIGH_IMPACT = "High Impact"


# kg CO2 per km — illustrative, see module disclaimer above.
_VEHICLE_EMISSION_FACTOR = {
    VehicleType.NONE: 0.0,
    VehicleType.BIKE: 0.0,
    VehicleType.PUBLIC_TRANSPORT: 0.05,
    VehicleType.ELECTRIC_CAR: 0.05,
    VehicleType.PETROL_CAR: 0.192,
    VehicleType.DIESEL_CAR: 0.171,
}

_DIET_BASE_SCORE = {
    DietType.VEGAN: 100,
    DietType.VEGETARIAN: 85,
    DietType.FLEXITARIAN: 60,
    DietType.NON_VEGETARIAN: 40,
}

# Relative weight of each category in the overall score. Transport and diet
# are weighted highest as they're typically the largest personal-footprint
# levers in common household carbon calculators.
_WEIGHTS = {
    "transport": 0.30,
    "food": 0.25,
    "energy": 0.25,
    "lifestyle": 0.20,
}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class CarbonInputs:
    vehicle_type: VehicleType
    distance_km_per_day: float
    diet_type: DietType
    meat_meals_per_week: int
    electricity_kwh_per_month: float
    ac_hours_per_day: float
    shopping_trips_per_month: int
    recycles: bool


@dataclass(frozen=True)
class CarbonResult:
    overall_score: int
    category: ImpactCategory
    transport_score: int
    food_score: int
    energy_score: int
    lifestyle_score: int


def _transport_score(vehicle_type: VehicleType, distance_km_per_day: float) -> float:
    factor = _VEHICLE_EMISSION_FACTOR[vehicle_type]
    daily_emissions_kg = factor * max(0.0, distance_km_per_day)
    # 10kg/day treated as a rough "high impact" ceiling for normalization.
    return _clamp(100 - (daily_emissions_kg / 10) * 100)


def _food_score(diet_type: DietType, meat_meals_per_week: int) -> float:
    base = _DIET_BASE_SCORE[diet_type]
    penalty = min(base, max(0, meat_meals_per_week) * 2)
    return _clamp(base - penalty)


def _energy_score(electricity_kwh_per_month: float, ac_hours_per_day: float) -> float:
    electricity_penalty = min(60.0, max(0.0, electricity_kwh_per_month) / 10)
    ac_penalty = min(40.0, max(0.0, ac_hours_per_day) * 5)
    return _clamp(100 - electricity_penalty - ac_penalty)


def _lifestyle_score(shopping_trips_per_month: int, recycles: bool) -> float:
    shopping_penalty = min(80.0, max(0, shopping_trips_per_month) * 3)
    score = 100 - shopping_penalty
    score += 10 if recycles else -10
    return _clamp(score)


def _category_for_score(score: int) -> ImpactCategory:
    if score >= 90:
        return ImpactCategory.ECO_CHAMPION
    if score >= 70:
        return ImpactCategory.GREEN_LIFESTYLE
    if score >= 40:
        return ImpactCategory.NEEDS_IMPROVEMENT
    return ImpactCategory.HIGH_IMPACT


def compute_carbon_score(inputs: CarbonInputs) -> CarbonResult:
    transport = _transport_score(inputs.vehicle_type, inputs.distance_km_per_day)
    food = _food_score(inputs.diet_type, inputs.meat_meals_per_week)
    energy = _energy_score(inputs.electricity_kwh_per_month, inputs.ac_hours_per_day)
    lifestyle = _lifestyle_score(inputs.shopping_trips_per_month, inputs.recycles)

    overall = (
        transport * _WEIGHTS["transport"]
        + food * _WEIGHTS["food"]
        + energy * _WEIGHTS["energy"]
        + lifestyle * _WEIGHTS["lifestyle"]
    )
    overall_rounded = round(overall)

    return CarbonResult(
        overall_score=overall_rounded,
        category=_category_for_score(overall_rounded),
        transport_score=round(transport),
        food_score=round(food),
        energy_score=round(energy),
        lifestyle_score=round(lifestyle),
    )
