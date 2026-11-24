import pytest

from spice_engine import SIMULATION_MODES, build_netlist, parse_sim_input

BASE = {
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "rl": "10000",
    "cin": "10e-6",
    "cout": "10e-6",
    "amplitude_v": "0.01",
    "frequency_hz": "1000",
    "beta": "100",
    "vbe": "0.70",
}


def test_parses_reference_fixture():
    data, errors = parse_sim_input(BASE)
    assert errors == {}
    assert data.vcc == 12.0
    assert data.r1 == 100_000.0
    assert data.amplitude_v == 0.01


def test_rejects_bad_frequency():
    data, errors = parse_sim_input(dict(BASE, frequency_hz="0"))
    assert data is None
    assert "frequency_hz" in errors


def test_rejects_nonpositive_amplitude():
    data, errors = parse_sim_input(dict(BASE, amplitude_v="-1"))
    assert data is None
    assert "amplitude_v" in errors


def test_rejects_unknown_mode_netlist():
    data, _ = parse_sim_input(BASE)
    with pytest.raises(ValueError):
        build_netlist(data, "bogus")


def test_modes_are_dc_ac_tran():
    assert SIMULATION_MODES == ("dc", "ac", "tran")
