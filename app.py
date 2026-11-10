from flask import Flask, render_template, request

from bjt import FIELDS, parse_bias_input

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


@app.get("/")
def index():
    return render_template("index.html", values=DEFAULTS, errors={}, result=None)


@app.post("/")
def calculate():
    values = {field: request.form.get(field, "") for field in FIELDS}
    data, errors = parse_bias_input(values)
    if errors:
        return render_template("index.html", values=values, errors=errors, result=None)
    return render_template("index.html", values=values, errors={}, result=None)
