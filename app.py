from flask import Flask, render_template, request

from bjt import FIELDS, analyze, parse_bias_input

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
