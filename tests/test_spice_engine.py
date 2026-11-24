import subprocess
from dataclasses import replace

import pytest

import spice_engine
from spice_engine import (
    SIMULATION_MODES,
    build_netlist,
    find_executable,
    parse_ac,
    parse_dc,
    parse_sim_input,
    parse_tran,
    run_simulation,
)

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


DC_LOG = (
    "Node                                  Voltage\n"
    "----                                  -------\n"
    "out                              0.000000e+00\n"
    "src                              0.000000e+00\n"
    "emitter                          1.175805e+00\n"
    "collector                        9.438841e+00\n"
    "base                             1.954004e+00\n"
    "vcc                              1.200000e+01\n"
)
AC_LOG = (
    "Index   frequency       vdb(out)        vp(out)         \n"
    "--------------------------------------------------------------------------------\n"
    "0\t1.000000e+01\t4.726377e+00\t-2.90856e+00\t\n"
    "1\t1.059254e+01\t4.739313e+00\t-2.92148e+00\t\n"
)
TRAN_LOG = (
    "Index   time            v(src)          v(out)          \n"
    "--------------------------------------------------------------------------------\n"
    "0\t0.000000e+00\t0.000000e+00\t0.000000e+00\t\n"
    "1\t1.000000e-08\t6.283185e-07\t-6.58170e-05\t\n"
)


def test_parse_dc_returns_volts_and_derived_ic():
    result = parse_dc(DC_LOG, vcc=12.0, rc=2200.0)
    assert result["vb_v"] == pytest.approx(1.954004)
    assert result["ve_v"] == pytest.approx(1.175805)
    assert result["vc_v"] == pytest.approx(9.438841)
    assert result["vce_v"] == pytest.approx(9.438841 - 1.175805)
    assert result["ic_a"] == pytest.approx((12.0 - 9.438841) / 2200.0)


PAGED_AC_LOG = (
    "Index   frequency       vdb(out)        vp(out)         \n"
    "--------------------------------------------------------------------------------\n"
    "0\t1.000000e+01\t4.726377e+00\t-2.90856e+00\t\n"
    "1\t1.059254e+01\t4.739313e+00\t-2.92148e+00\t\n"
    "\n"
    "\n"
    "Index   frequency       vdb(out)        vp(out)         \n"
    "--------------------------------------------------------------------------------\n"
    "2\t1.122018e+01\t4.750860e+00\t-2.93370e+00\t\n"
    "3\t1.188502e+01\t4.761164e+00\t-2.94525e+00\t\n"
)


def test_parse_ac_columns_and_gain():
    result = parse_ac(AC_LOG)
    assert result["frequency_hz"][0] == pytest.approx(10.0)
    assert result["gain_db"][0] == pytest.approx(4.726377)
    assert result["gain_v_per_v"][0] == pytest.approx(10 ** (4.726377 / 20))
    assert result["phase_deg"][0] == pytest.approx(-2.90856)


def test_table_skips_repeated_ngspice_page_headers():
    result = parse_ac(PAGED_AC_LOG)
    assert len(result["frequency_hz"]) == 4
    assert result["frequency_hz"][-1] == pytest.approx(11.88502)


def test_parse_tran_columns():
    result = parse_tran(TRAN_LOG)
    assert result["time_s"][0] == 0.0
    assert result["vin_v"][1] == pytest.approx(6.283185e-7)
    assert result["vout_v"][1] == pytest.approx(-6.58170e-5)


def test_cutoff_not_determined():
    result = parse_ac(AC_LOG)
    assert result["cutoff_hz"] == "not determined in sweep range"


def test_missing_engine_reports_error():
    data, _ = parse_sim_input(BASE)
    result = run_simulation(data, "dc", executable="definitely-not-ngspice.exe")
    assert result.status == "error"
    assert result.data == {}
    assert result.error


def test_timeout_is_error(monkeypatch):
    def boom(*args, **kwargs):
        raise subprocess.TimeoutExpired("ngspice", 1)

    monkeypatch.setattr(spice_engine.subprocess, "run", boom)
    data, _ = parse_sim_input(BASE)
    result = run_simulation(data, "dc", executable="fake", timeout=1)
    assert result.status == "error"
    assert result.data == {}


def test_empty_log_is_error(monkeypatch):
    def no_output(*args, **kwargs):
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(spice_engine.subprocess, "run", no_output)
    data, _ = parse_sim_input(BASE)
    result = run_simulation(data, "dc", executable="fake")
    assert result.status == "error"
    assert result.data == {}


@pytest.mark.skipif(find_executable() is None, reason="ngspice not on PATH")
def test_real_run_reacts_to_re_and_source():
    base, _ = parse_sim_input(BASE)
    first = run_simulation(base, "dc")
    second = run_simulation(replace(base, re=2000.0), "dc")
    assert first.status == second.status == "success"
    assert first.data["ic_a"] != second.data["ic_a"]
    third = run_simulation(replace(base, amplitude_v=0.02), "tran")
    assert third.status == "success"
    assert third.data["vin_peak_v"] == pytest.approx(0.02, rel=0.05)
