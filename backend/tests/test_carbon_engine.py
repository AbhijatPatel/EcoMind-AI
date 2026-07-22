"""
Unit tests for the carbon scoring engine.

No DB, no HTTP client — these test the pure function directly, which is
the whole point of keeping scoring deterministic and side-effect-free.
"""

from app.services.carbon_engine import (
    CarbonInputs,
    DietType,
    ImpactCategory,
    VehicleType,
    compute_carbon_score,
)


def _best_case_inputs() -> CarbonInputs:
    return CarbonInputs(
        vehicle_type=VehicleType.NONE,
        distance_km_per_day=0,
        diet_type=DietType.VEGAN,
        meat_meals_per_week=0,
        electricity_kwh_per_month=0,
        ac_hours_per_day=0,
        shopping_trips_per_month=0,
        recycles=True,
    )


def _worst_case_inputs() -> CarbonInputs:
    return CarbonInputs(
        vehicle_type=VehicleType.DIESEL_CAR,
        distance_km_per_day=100,
        diet_type=DietType.NON_VEGETARIAN,
        meat_meals_per_week=21,
        electricity_kwh_per_month=2000,
        ac_hours_per_day=24,
        shopping_trips_per_month=60,
        recycles=False,
    )


def test_best_case_scores_eco_champion():
    result = compute_carbon_score(_best_case_inputs())
    assert result.overall_score == 100
    assert result.category == ImpactCategory.ECO_CHAMPION


def test_worst_case_scores_high_impact():
    result = compute_carbon_score(_worst_case_inputs())
    assert result.overall_score <= 10
    assert result.category == ImpactCategory.HIGH_IMPACT


def test_score_is_deterministic_across_repeated_calls():
    inputs = CarbonInputs(
        vehicle_type=VehicleType.PETROL_CAR,
        distance_km_per_day=20,
        diet_type=DietType.FLEXITARIAN,
        meat_meals_per_week=5,
        electricity_kwh_per_month=350,
        ac_hours_per_day=3,
        shopping_trips_per_month=4,
        recycles=True,
    )
    first = compute_carbon_score(inputs)
    second = compute_carbon_score(inputs)
    assert first == second


def test_public_transport_scores_better_than_petrol_car_same_distance():
    petrol = CarbonInputs(
        vehicle_type=VehicleType.PETROL_CAR,
        distance_km_per_day=20,
        diet_type=DietType.FLEXITARIAN,
        meat_meals_per_week=5,
        electricity_kwh_per_month=300,
        ac_hours_per_day=2,
        shopping_trips_per_month=4,
        recycles=True,
    )
    public_transport = CarbonInputs(**{**petrol.__dict__, "vehicle_type": VehicleType.PUBLIC_TRANSPORT})

    petrol_result = compute_carbon_score(petrol)
    transit_result = compute_carbon_score(public_transport)

    assert transit_result.transport_score > petrol_result.transport_score
    assert transit_result.overall_score > petrol_result.overall_score


def test_category_thresholds_match_spec():
    # 90-100 Eco Champion, 70-89 Green Lifestyle, 40-69 Needs Improvement, 0-39 High Impact
    from app.services.carbon_engine import _category_for_score

    assert _category_for_score(100) == ImpactCategory.ECO_CHAMPION
    assert _category_for_score(90) == ImpactCategory.ECO_CHAMPION
    assert _category_for_score(89) == ImpactCategory.GREEN_LIFESTYLE
    assert _category_for_score(70) == ImpactCategory.GREEN_LIFESTYLE
    assert _category_for_score(69) == ImpactCategory.NEEDS_IMPROVEMENT
    assert _category_for_score(40) == ImpactCategory.NEEDS_IMPROVEMENT
    assert _category_for_score(39) == ImpactCategory.HIGH_IMPACT
    assert _category_for_score(0) == ImpactCategory.HIGH_IMPACT


def test_recycling_improves_lifestyle_score():
    base = dict(
        vehicle_type=VehicleType.NONE,
        distance_km_per_day=0,
        diet_type=DietType.VEGAN,
        meat_meals_per_week=0,
        electricity_kwh_per_month=0,
        ac_hours_per_day=0,
        shopping_trips_per_month=10,
    )
    with_recycling = compute_carbon_score(CarbonInputs(**base, recycles=True))
    without_recycling = compute_carbon_score(CarbonInputs(**base, recycles=False))

    assert with_recycling.lifestyle_score > without_recycling.lifestyle_score
