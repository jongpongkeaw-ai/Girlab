from simulator_plots import bode_svg, wave_svg

AC_DATA = {
    "frequency_hz": [10.0, 100.0, 1000.0],
    "gain_db": [4.7, 4.85, 4.6],
    "phase_deg": [-3.0, -3.1, -3.2],
    "cutoff_hz": "not determined in sweep range",
}

TRAN_DATA = {
    "time_s": [0.0, 0.00025, 0.0005],
    "vin_v": [0.0, 0.01, 0.0],
    "vout_v": [0.0, -0.017, 0.0],
    "inverted": True,
}


def test_bode_has_axis_units_and_legend_swatches():
    svg = bode_svg(AC_DATA)
    assert "Gain (dB, left axis)" in svg
    assert "Phase (deg, right axis)" in svg
    assert "Frequency (Hz, log scale)" in svg
    assert "sim-swatch-gain" in svg
    assert "sim-swatch-phase" in svg
    assert "10^1" in svg
    assert "10^2" in svg
    assert "not determined in sweep range" in svg


def test_wave_has_axis_units_and_legend_swatches():
    svg = wave_svg(TRAN_DATA)
    assert "Vin (mV, left axis)" in svg
    assert "Vout (V, right axis)" in svg
    assert "Time (ms)" in svg
    assert "sim-swatch-vin" in svg
    assert "sim-swatch-vout" in svg
    assert "Phase inversion: yes" in svg


def test_empty_arrays_render_nothing():
    assert bode_svg({"frequency_hz": [], "gain_db": [], "phase_deg": [], "cutoff_hz": "x"}) == ""
    assert wave_svg({"time_s": [], "vin_v": [], "vout_v": [], "inverted": False}) == ""
