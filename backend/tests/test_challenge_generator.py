import pytest

from app.services.challenge_generator import generate_challenge


def test_rotates_through_pool_deterministically():
    first = generate_challenge("transport", 0)
    second = generate_challenge("transport", 1)
    third = generate_challenge("transport", 2)  # wraps back to index 0

    assert first.title != second.title
    assert first.title == third.title


def test_same_inputs_produce_same_output():
    a = generate_challenge("food", 3)
    b = generate_challenge("food", 3)
    assert a == b


def test_invalid_category_raises():
    with pytest.raises(ValueError):
        generate_challenge("spaceship", 0)


def test_category_label_is_human_readable():
    result = generate_challenge("lifestyle", 0)
    assert result.category_label == "Shopping & waste"
