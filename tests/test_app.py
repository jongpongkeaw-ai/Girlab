import pytest

from app import app, format_current, format_power, format_voltage

FORM = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_index_shows_form(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    for field in FORM:
        assert f'name="{field}"' in body


def test_layout_has_three_panels_and_goal_bar(client):
    body = client.get("/").get_data(as_text=True)
    for panel in ("input-panel", "circuit-panel", "results-panel"):
        assert f'id="{panel}"' in body
    assert "<svg" in body
    assert "/static/vendor/bootstrap.min.css" in body
    assert "Week 2 Goal" in body


def test_bootstrap_css_is_served_locally(client):
    response = client.get("/static/vendor/bootstrap.min.css")
    assert response.status_code == 200
    assert len(response.get_data()) > 100000


def test_post_invalid_shows_error_and_keeps_value(client):
    response = client.post("/", data=dict(FORM, r2="0"))
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "greater than zero" in body
    assert 'value="0"' in body


def test_html_in_input_is_escaped(client):
    body = client.post("/", data=dict(FORM, r1="<script>")).get_data(as_text=True)
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_formatters_pick_units():
    assert format_current(8.824502e-6) == "8.82 µA"
    assert format_current(1.323675e-3) == "1.324 mA"
    assert format_current(2.5) == "2.500 A"
    assert format_voltage(7.755414) == "7.755 V"
    assert format_power(10.2659e-3) == "10.27 mW"


def test_formatters_handle_extreme_magnitudes():
    assert format_current(1e6).endswith(" A")
    assert format_current(1e-9).endswith(" µA")
    assert format_voltage(1e6) == "1000000.000 V"


def test_post_valid_shows_operating_point(client):
    body = client.post("/", data=FORM).get_data(as_text=True)
    assert "Active region approximation OK" in body
    assert "8.82 µA" in body
    assert "1.324 mA" in body
    assert "1.332 mA" in body
    assert "2.032 V" in body
    assert "9.088 V" in body
    assert "7.755 V" in body
    assert "10.27 mW" in body


def test_saturation_status_box(client):
    body = client.post("/", data=dict(FORM, rc="10000")).get_data(as_text=True)
    assert "Saturation region" in body
    assert "linear model is not valid" in body


def test_cutoff_status_box(client):
    body = client.post("/", data=dict(FORM, r2="1000")).get_data(as_text=True)
    assert "Cutoff region" in body
    assert "base current is zero or negative" in body

