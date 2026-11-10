import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_static_demo_page_contains_calculator():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="input-panel"' in html
    assert 'id="circuit-panel"' in html
    assert 'id="results-panel"' in html
    for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
        assert f'name="{field}"' in html
    assert "Week 2 Goal" in html
    assert "https://github.com/jongpongkeaw-ai/Girlab" in html
    assert "demo.js" in html


def test_static_demo_js_matches_reference():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for the static demo parity check")
    result = subprocess.run(
        [node, "tests/static_demo_check.cjs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    data = json.loads(result.stdout)

    assert data["region"] == "active"
    assert data["ib"] == pytest.approx(8.824502e-6, rel=1e-6)
    assert data["ic"] == pytest.approx(1.323675e-3, rel=1e-6)
    assert data["ie"] == pytest.approx(1.332500e-3, rel=1e-6)
    assert data["vb"] == pytest.approx(2.032500, rel=1e-6)
    assert data["vc"] == pytest.approx(9.087914, rel=1e-6)
    assert data["ve"] == pytest.approx(1.332500, rel=1e-6)
    assert data["vce"] == pytest.approx(7.755414, rel=1e-6)
    assert data["pc"] == pytest.approx(10.26565e-3, rel=1e-6)
    assert data["formatted"] == {
        "vb": "2.032 V",
        "ve": "1.332 V",
        "vc": "9.088 V",
        "vce": "7.755 V",
        "ib": "8.82 µA",
        "ic": "1.324 mA",
        "ie": "1.332 mA",
        "pc": "10.27 mW",
    }
    assert data["nano"] == "1.41 nA"
    assert data["cutoff"]["region"] == "cutoff"
    assert "Cutoff region" in data["cutoff"]["message"]
    assert data["saturation"]["region"] == "saturation"
    assert "Saturation region" in data["saturation"]["message"]
