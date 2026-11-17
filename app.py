from flask import Flask, render_template, request

from bjt import MODES, analyze_mode, parse_mode_input

app = Flask(__name__)

MODE_LABELS = {
    "divider": "Voltage Divider",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

MODE_DESCRIPTIONS = {
    "divider": "Common-emitter amplifier with voltage-divider bias — DC operating point",
    "fixed": "Common-emitter amplifier with fixed bias from a single supply — DC operating point",
    "emitter": "Common-emitter amplifier with emitter bias from a single supply — DC operating point",
}

DIVIDER_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
FIXED_FIELDS = ("vcc", "rb", "rc", "beta", "vbe")
EMITTER_FIELDS = ("vcc", "rb", "rc", "re", "beta", "vbe")

FIELD_META = {
    "divider": (
        ("vcc", "VCC", "V"),
        ("r1", "R1", "Ω"),
        ("r2", "R2", "Ω"),
        ("rc", "RC", "Ω"),
        ("re", "RE", "Ω"),
        ("beta", "β", ""),
        ("vbe", "VBE", "V"),
    ),
    "fixed": (
        ("vcc", "VCC", "V"),
        ("rb", "RB", "Ω"),
        ("rc", "RC", "Ω"),
        ("beta", "β", ""),
        ("vbe", "VBE", "V"),
    ),
    "emitter": (
        ("vcc", "VCC", "V"),
        ("rb", "RB", "Ω"),
        ("rc", "RC", "Ω"),
        ("re", "RE", "Ω"),
        ("beta", "β", ""),
        ("vbe", "VBE", "V"),
    ),
}

DEFAULTS = {
    "divider": {
        "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
    "fixed": {
        "vcc": "12", "rb": "470000", "rc": "2200", "beta": "150", "vbe": "0.7",
    },
    "emitter": {
        "vcc": "12", "rb": "470000", "rc": "2200", "re": "1000",
        "beta": "150", "vbe": "0.7",
    },
}

CIRCUIT_TEMPLATES = {
    "divider": "_circuit.svg",
    "fixed": "_circuit_fixed.svg",
    "emitter": "_circuit_emitter.svg",
}

MODE_GOALS = {
    "divider": "Analyze and verify the DC operating point of a voltage-divider biased common-emitter amplifier.",
    "fixed": "Analyze and verify the DC operating point of a fixed-biased common-emitter amplifier.",
    "emitter": "Analyze and verify the DC operating point of an emitter-biased common-emitter amplifier.",
}


def _fixed(value: float, decimals: int) -> str:
    """จัดรูปแบบทศนิยมโดยไม่แสดง -0.00 จากค่าลบที่น้อยมาก"""
    text = f"{value:.{decimals}f}"
    if text.startswith("-") and float(text) == 0:
        return text[1:]
    return text


def format_current(amperes: float) -> str:
    magnitude = abs(amperes)
    if magnitude < 1e-6:
        return f"{_fixed(amperes * 1e9, 2)} nA"
    if magnitude < 1e-3:
        return f"{_fixed(amperes * 1e6, 2)} µA"
    if magnitude < 1:
        return f"{_fixed(amperes * 1e3, 3)} mA"
    return f"{_fixed(amperes, 3)} A"


def format_voltage(volts: float) -> str:
    return f"{_fixed(volts, 3)} V"


def format_power(watts: float) -> str:
    if abs(watts) < 1:
        return f"{_fixed(watts * 1e3, 2)} mW"
    return f"{_fixed(watts, 3)} W"


app.jinja_env.filters.update(
    current=format_current, voltage=format_voltage, power=format_power
)


def _mode_from(value: str | None) -> str:
    """โหมดที่ไม่รู้จักหรือไม่ส่งมาจะกลับไปใช้ Divider เพื่อความเข้ากันได้เดิม"""
    return value if value in MODES else "divider"


def _render(mode: str, values: dict[str, str], errors: dict[str, str], result):
    return render_template(
        "index.html",
        mode=mode,
        modes=MODES,
        mode_labels=MODE_LABELS,
        mode_descriptions=MODE_DESCRIPTIONS,
        field_meta=FIELD_META[mode],
        values=values,
        errors=errors,
        result=result,
        circuit=CIRCUIT_TEMPLATES[mode],
        goal=MODE_GOALS[mode],
    )


def _read_form(fields: tuple[str, ...]) -> dict[str, str]:
    """อ่านเฉพาะฟิลด์ของโหมดที่เลือก โดยคงค่าดิบไว้แสดงกลับในฟอร์ม"""
    return {field: request.form.get(field, "") for field in fields}


@app.get("/")
def index():
    mode = _mode_from(request.args.get("mode"))
    if mode == "fixed":
        return _render("fixed", DEFAULTS["fixed"], {}, None)
    elif mode == "emitter":
        return _render("emitter", DEFAULTS["emitter"], {}, None)
    return _render("divider", DEFAULTS["divider"], {}, None)


@app.post("/")
def calculate():
    mode = _mode_from(request.form.get("mode"))

    if mode == "fixed":
        values = _read_form(FIXED_FIELDS)
        data, errors = parse_mode_input("fixed", values)
    elif mode == "emitter":
        values = _read_form(EMITTER_FIELDS)
        data, errors = parse_mode_input("emitter", values)
    else:
        # Divider เป็นโหมดเริ่มต้นและคงตัวตรวจเดิมไว้ทั้งหมด
        mode = "divider"
        values = _read_form(DIVIDER_FIELDS)
        data, errors = parse_mode_input("divider", values)

    if errors:
        return _render(mode, values, errors, None)
    return _render(mode, values, {}, analyze_mode(mode, data))
