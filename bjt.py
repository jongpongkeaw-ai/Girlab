from dataclasses import dataclass
from math import isfinite
from typing import Mapping

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


@dataclass(frozen=True)
class BiasInput:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


def parse_bias_input(raw: Mapping[str, str]) -> tuple[BiasInput | None, dict[str, str]]:
    """แปลงค่าดิบเป็น BiasInput; คืน (None, errors) เมื่อมีช่องผิด"""
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for field in FIELDS:
        text = str(raw.get(field, "")).strip()
        if not text:
            errors[field] = "Required"
            continue
        try:
            value = float(text)
        except ValueError:
            errors[field] = "Must be a number"
            continue
        if not isfinite(value):
            errors[field] = "Must be a finite number"
            continue
        values[field] = value

    for field in FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = "Must be greater than zero"

    if values.get("vcc", 0) > 0 and "vbe" in values:
        if values["vbe"] >= values["vcc"]:
            errors["vbe"] = "Must be less than VCC"

    if errors:
        return None, errors
    return BiasInput(**values), {}


VCE_SAT = 0.2


@dataclass(frozen=True)
class BiasResult:
    ib_a: float
    ic_a: float
    ie_a: float
    vb_v: float
    vc_v: float
    ve_v: float
    vce_v: float
    pc_w: float
    region: str
    warnings: tuple[str, ...]


def analyze(data: BiasInput) -> BiasResult:
    """คำนวณจุดทำงาน DC ด้วยสมมูลเทเวนิน"""
    vbb = data.vcc * data.r2 / (data.r1 + data.r2)
    rb = data.r1 * data.r2 / (data.r1 + data.r2)
    ib = (vbb - data.vbe) / (rb + (1 + data.beta) * data.re)
    ic = data.beta * ib
    ie = (1 + data.beta) * ib
    ve = ie * data.re
    vc = data.vcc - ic * data.rc
    vce = vc - ve
    vb = data.vbe + ve
    pc = vce * ic

    warnings: list[str] = []
    if ib <= 0:
        region = "cutoff"
        warnings.append("Transistor is in cutoff: base current is zero or negative.")
    elif vce <= VCE_SAT:
        region = "saturation"
        warnings.append(
            "Transistor is in saturation: VCE is at or below VCE(sat); "
            "the linear model is not valid."
        )
    else:
        region = "active"

    if ib > 0 and data.vcc / (data.r1 + data.r2) < 10 * ib:
        warnings.append(
            "Divider current is less than 10x IB; the bias point depends strongly on beta."
        )

    return BiasResult(ib, ic, ie, vb, vc, ve, vce, pc, region, tuple(warnings))
