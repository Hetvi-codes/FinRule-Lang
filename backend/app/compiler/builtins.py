import math
from typing import List, Any


def fn_growth(base: float, rate: float, period: float) -> float:
    return float(base * math.pow(1.0 + rate, period))


def fn_compound(principal: float, rate: float, periods: float) -> float:
    return float(principal * math.pow(1.0 + rate, periods))


def fn_pmt(rate: float, nper: float, pv: float, fv: float = 0.0) -> float:
    if rate == 0:
        return float(-(pv + fv) / nper) if nper != 0 else 0.0
    factor = math.pow(1.0 + rate, nper)
    return float((rate * (pv * factor + fv)) / (factor - 1.0))


def fn_fv(rate: float, nper: float, pmt: float, pv: float = 0.0) -> float:
    if rate == 0:
        return float(-pv - (pmt * nper))
    factor = math.pow(1.0 + rate, nper)
    return float(-(pv * factor + pmt * (factor - 1.0) / rate))


def fn_npv(rate: float, *values: float) -> float:
    total = 0.0
    for i, val in enumerate(values):
        total += float(val) / math.pow(1.0 + rate, i + 1)
    return float(total)


def fn_round(val: float, decimals: int = 2) -> float:
    return round(float(val), int(decimals))


def fn_min(*values: float) -> float:
    return float(min(values))


def fn_max(*values: float) -> float:
    return float(max(values))


def fn_abs(val: float) -> float:
    return float(abs(val))


FINANCIAL_BUILTINS = {
    "growth": fn_growth,
    "compound": fn_compound,
    "pmt": fn_pmt,
    "fv": fn_fv,
    "npv": fn_npv,
    "round": fn_round,
    "min": fn_min,
    "max": fn_max,
    "abs": fn_abs,
}
