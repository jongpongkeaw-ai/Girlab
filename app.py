from flask import Flask, render_template, request

from bjt import FIELDS, analyze, parse_bias_input

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


def format_current(amperes: float) -> str:
    magnitude = abs(amperes)
    if magnitude < 1e-3:
        return f"{amperes * 1e6:.2f} µA"
    if magnitude < 1:
        return f"{amperes * 1e3:.3f} mA"
    return f"{amperes:.3f} A"


def format_voltage(volts: float) -> str:
    return f"{volts:.3f} V"


def format_power(watts: float) -> str:
    if abs(watts) < 1:
        return f"{watts * 1e3:.2f} mW"
    return f"{watts:.3f} W"


app.jinja_env.filters.update(
    current=format_current, voltage=format_voltage, power=format_power
)


@app.get("/")
def index():
    return render_template("index.html", values=DEFAULTS, errors={}, result=None)


@app.post("/")
def calculate():
    values = {field: request.form.get(field, "") for field in FIELDS}
    data, errors = parse_bias_input(values)
    if errors:
        return render_template("index.html", values=values, errors=errors, result=None)
    return render_template("index.html", values=values, errors={}, result=analyze(data))
