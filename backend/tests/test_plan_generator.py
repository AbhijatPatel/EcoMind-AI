from app.services.plan_generator import SubScores, generate_plan


def test_targets_the_two_weakest_categories():
    # transport=20 (weakest), lifestyle=30 (2nd weakest), food/energy strong
    scores = SubScores(transport_score=20, food_score=90, energy_score=85, lifestyle_score=30)
    plan = generate_plan(scores)

    assert plan.focus_areas == ["Transportation", "Shopping & waste"]
    assert len(plan.daily) == 2
    assert len(plan.weekly) == 2
    assert len(plan.monthly) == 2


def test_is_deterministic_across_repeated_calls():
    scores = SubScores(transport_score=40, food_score=60, energy_score=20, lifestyle_score=80)
    first = generate_plan(scores)
    second = generate_plan(scores)
    assert first == second


def test_all_categories_weakest_still_produces_valid_plan():
    scores = SubScores(transport_score=50, food_score=50, energy_score=50, lifestyle_score=50)
    plan = generate_plan(scores)
    assert len(plan.focus_areas) == 2
    assert all(isinstance(item, str) and item for item in plan.daily + plan.weekly + plan.monthly)


def test_food_weakest_produces_food_actions():
    scores = SubScores(transport_score=90, food_score=10, energy_score=90, lifestyle_score=90)
    plan = generate_plan(scores)
    assert plan.focus_areas[0] == "Food"
    assert "plant-based" in plan.daily[0] or "meat-free" in " ".join(plan.weekly)
