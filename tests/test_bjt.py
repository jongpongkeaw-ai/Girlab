import math

import pytest

from bjt import BiasInput, FIELDS, VCE_SAT, analyze, parse_bias_input

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


def make_input(**overrides):
    raw = dict(REFERENCE, **{key: str(value) for key, value in overrides.items()})
    data, errors = parse_bias_input(raw)
    assert errors == {}
    return data


def test_thevenin_reference_operating_point():
    result = analyze(make_input())
    assert result.region == "active"
    assert result.ib_a == pytest.approx(8.824502e-6, rel=1e-6)
    assert result.ic_a == pytest.approx(1.323675e-3, rel=1e-6)
    assert result.ie_a == pytest.approx(1.332500e-3, rel=1e-6)
    assert result.vb_v == pytest.approx(2.032500, rel=1e-6)
    assert result.vc_v == pytest.approx(9.087914, rel=1e-6)
    assert result.ve_v == pytest.approx(1.332500, rel=1e-6)
    assert result.vce_v == pytest.approx(7.755414, rel=1e-6)
    assert result.pc_w == pytest.approx(10.26565e-3, rel=1e-6)
    assert result.warnings == ()


def test_cutoff_when_base_current_is_not_positive():
    result = analyze(make_input(r2=1000))
    assert result.region == "cutoff"
    assert any("cutoff" in warning.lower() for warning in result.warnings)


def test_saturation_when_vce_at_or_below_vce_sat():
    result = analyze(make_input(rc=10000))
    assert result.region == "saturation"
    assert result.vce_v <= VCE_SAT
    assert any("saturation" in warning.lower() for warning in result.warnings)


def test_warns_when_divider_current_is_small():
    result = analyze(make_input(r1=470000, r2=100000))
    assert result.region == "active"
    assert any("beta" in warning.lower() for warning in result.warnings)


def test_near_cutoff_boundary_does_not_crash():
    result = analyze(make_input(vbe=2.105))
    assert result.region in {"active", "cutoff"}
    assert math.isfinite(result.ib_a)

