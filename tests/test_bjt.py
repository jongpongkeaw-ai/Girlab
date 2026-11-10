import math

import pytest

from bjt import BiasInput, FIELDS, parse_bias_input

REFERENCE = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


def test_parse_valid_input_returns_bias_input():
    data, errors = parse_bias_input(REFERENCE)
    assert errors == {}
    assert data == BiasInput(12.0, 47000.0, 10000.0, 2200.0, 1000.0, 150.0, 0.7)


@pytest.mark.parametrize("field,value", [
    ("vcc", ""), ("r1", "abc"), ("rc", "-1"), ("re", "nan"),
    ("beta", "0"), ("vbe", "12"),
])
def test_invalid_fields_are_reported(field, value):
    data, errors = parse_bias_input(dict(REFERENCE, **{field: value}))
    assert data is None
    assert field in errors


@pytest.mark.parametrize("field", ["r1", "r2", "rc", "re"])
def test_zero_resistance_is_rejected(field):
    data, errors = parse_bias_input(dict(REFERENCE, **{field: "0"}))
    assert data is None
    assert "greater than zero" in errors[field]


def test_accepts_whitespace_and_scientific_notation():
    data, errors = parse_bias_input(dict(REFERENCE, r1=" 4.7e4 ", beta="1.5e2"))
    assert errors == {}
    assert data.r1 == pytest.approx(47000.0)
    assert data.beta == pytest.approx(150.0)


def test_missing_fields_are_required():
    data, errors = parse_bias_input({})
    assert data is None
    assert set(errors) == set(FIELDS)
    assert all("Required" in message for message in errors.values())


def test_non_finite_input_is_rejected():
    data, errors = parse_bias_input(dict(REFERENCE, vcc="inf"))
    assert data is None
    assert "finite" in errors["vcc"]
