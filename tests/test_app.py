import pytest

from app import app

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
