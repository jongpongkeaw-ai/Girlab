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
