import pytest

from app import app
from spice_engine import find_executable

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


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_simulator_has_mode_selector_and_units(client):
    body = client.get("/simulator").get_data(as_text=True)
    assert client.get("/simulator").status_code == 200
    assert 'name="mode"' in body
    assert "ngspice" in body
    assert "Hz" in body
    assert 'name="amplitude_v"' in body


def test_invalid_re_has_error_and_no_plot(client):
    body = client.post("/simulator", data=dict(BASE, mode="dc", re="0")).get_data(as_text=True)
    assert "Must be greater than zero" in body
    assert "simulation-plot" not in body
    assert "Error" in body


def test_lab3_routes_still_work(client):
    assert client.get("/?mode=fixed").status_code == 200
    assert client.get("/?mode=emitter").status_code == 200
    assert client.get("/?mode=divider").status_code == 200


def test_missing_engine_clears_plots(client, monkeypatch):
    monkeypatch.setenv("NGSPICE_EXECUTABLE", "definitely-not-ngspice.exe")
    body = client.post("/simulator", data=dict(BASE, mode="ac")).get_data(as_text=True)
    assert "Error · engine" in body
    assert "ngspice executable not found" in body
    assert "simulation-plot" not in body
    assert "Success · real ngspice run" not in body


@pytest.mark.skipif(find_executable() is None, reason="ngspice not on PATH")
def test_real_runs_render_dc_numbers_and_plots(client):
    dc_body = client.post("/simulator", data=dict(BASE, mode="dc")).get_data(as_text=True)
    assert "Success · real ngspice run" in dc_body
    assert "DC operating point" in dc_body
    assert "Analytical DC reference" in dc_body

    ac_body = client.post("/simulator", data=dict(BASE, mode="ac")).get_data(as_text=True)
    assert "simulation-plot" in ac_body
    assert "Frequency (Hz, log scale)" in ac_body

    tran_body = client.post("/simulator", data=dict(BASE, mode="tran")).get_data(as_text=True)
    assert "simulation-plot" in tran_body
    assert "Time (ms)" in tran_body
    assert "Vin peak" in tran_body
