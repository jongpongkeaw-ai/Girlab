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


MODES = ("divider", "fixed", "emitter")

MODE_FIELDS: dict[str, tuple[str, ...]] = {
    "divider": FIELDS,
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}


@dataclass(frozen=True)
class FixedBiasInput:
    vcc: float
    rb: float
    rc: float
    beta: float
    vbe: float


@dataclass(frozen=True)
class EmitterBiasInput:
    vcc: float
    rb: float
    rc: float
    re: float
    beta: float
    vbe: float


def _parse_mode_values(
    raw: Mapping[str, str], fields: tuple[str, ...]
) -> tuple[dict[str, float], dict[str, str]]:
    """ตรวจตัวเลขพื้นฐานของโหมดที่เลือก ใช้ข้อความ error ชุดเดียวกับ Divider"""
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for field in fields:
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

    for field in fields:
        if field in values and values[field] <= 0:
            errors[field] = "Must be greater than zero"

    if values.get("vcc", 0) > 0 and "vbe" in values:
        if values["vbe"] >= values["vcc"]:
            errors["vbe"] = "Must be less than VCC"

    return values, errors


def parse_mode_input(
    mode: str, raw: Mapping[str, str]
) -> tuple[BiasInput | FixedBiasInput | EmitterBiasInput | None, dict[str, str]]:
    """แปลงอินพุตตามโหมด; Divider ใช้ตัวตรวจเดิมทั้งหมด"""
    if mode not in MODE_FIELDS:
        return None, {"mode": "Unknown bias mode"}
    if mode == "divider":
        return parse_bias_input(raw)

    values, errors = _parse_mode_values(raw, MODE_FIELDS[mode])
    if errors:
        return None, errors
    if mode == "fixed":
        return FixedBiasInput(**values), {}
    return EmitterBiasInput(**values), {}


def _result_dict(
    mode: str,
    ib: float,
    ic: float,
    ie: float,
    vb: float,
    vc: float,
    ve: float,
    vce: float,
    pc: float,
    region: str,
    warnings: list[str],
) -> dict[str, object]:
    """คีย์และหน่วยชุดเดียวกันทุกโหมด: กระแสเป็น A, แรงดันเป็น V, กำลังเป็น W"""
    return {
        "mode": mode,
        "ib_a": ib,
        "ic_a": ic,
        "ie_a": ie,
        "vb_v": vb,
        "vc_v": vc,
        "ve_v": ve,
        "vce_v": vce,
        "pc_w": pc,
        "region": region,
        "warnings": warnings,
    }


def _classify(ib: float, vce: float) -> tuple[str, list[str]]:
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
    return region, warnings


def analyze_fixed(data: FixedBiasInput) -> dict[str, object]:
    """Fixed bias: IB = (VCC - VBE) / RB"""
    ib = (data.vcc - data.vbe) / data.rb
    ic = data.beta * ib
    ie = (1 + data.beta) * ib
    vb = data.vbe
    ve = 0.0
    vc = data.vcc - ic * data.rc
    vce = vc - ve
    pc = vce * ic
    region, warnings = _classify(ib, vce)
    return _result_dict("fixed", ib, ic, ie, vb, vc, ve, vce, pc, region, warnings)


def analyze_emitter(data: EmitterBiasInput) -> dict[str, object]:
    """Emitter bias แหล่งจ่ายเดียว: IB = (VCC - VBE) / (RB + (1 + beta) * RE)"""
    ib = (data.vcc - data.vbe) / (data.rb + (1 + data.beta) * data.re)
    ic = data.beta * ib
    ie = (1 + data.beta) * ib
    ve = ie * data.re
    vc = data.vcc - ic * data.rc
    vce = vc - ve
    vb = data.vbe + ve
    pc = vce * ic
    region, warnings = _classify(ib, vce)
    return _result_dict("emitter", ib, ic, ie, vb, vc, ve, vce, pc, region, warnings)


def analyze_mode(
    mode: str, data: BiasInput | FixedBiasInput | EmitterBiasInput
) -> dict[str, object]:
    """เลือกฟังก์ชันตามโหมดและคืน dict คีย์/หน่วยเดียวกันทุกโหมด"""
    if mode == "divider":
        result = analyze(data)  # type: ignore[arg-type]
        return _result_dict(
            "divider",
            result.ib_a,
            result.ic_a,
            result.ie_a,
            result.vb_v,
            result.vc_v,
            result.ve_v,
            result.vce_v,
            result.pc_w,
            result.region,
            list(result.warnings),
        )
    if mode == "fixed":
        return analyze_fixed(data)  # type: ignore[arg-type]
    if mode == "emitter":
        return analyze_emitter(data)  # type: ignore[arg-type]
    raise ValueError(f"Unknown bias mode: {mode}")
