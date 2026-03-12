from __future__ import annotations

from dataclasses import dataclass

from app.core.models import AxisCalibration


@dataclass(slots=True)
class DigitalAxisOutput:
    negative: bool
    positive: bool
    normalized: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_axis(raw: int, calibration: AxisCalibration) -> float:
    center = calibration.raw_center

    if raw >= center:
        span = max(1, calibration.raw_max - center)
        normalized = (raw - center) / span
    else:
        span = max(1, center - calibration.raw_min)
        normalized = -((center - raw) / span)

    normalized = clamp(normalized, -1.0, 1.0)

    if calibration.invert:
        normalized = -normalized

    if abs(normalized) < calibration.deadzone:
        return 0.0

    sign = -1.0 if normalized < 0 else 1.0
    magnitude = (abs(normalized) - calibration.deadzone) / max(1e-6, 1.0 - calibration.deadzone)
    magnitude = clamp(magnitude, 0.0, 1.0)
    magnitude = magnitude ** max(0.1, calibration.expo)
    magnitude *= max(0.0, calibration.sensitivity)
    return clamp(sign * magnitude, -1.0, 1.0)


def compute_digital_axis(raw: int, calibration: AxisCalibration, previous_negative: bool, previous_positive: bool) -> DigitalAxisOutput:
    normalized = normalize_axis(raw, calibration)

    neg_on = -abs(calibration.negative_threshold)
    neg_off = neg_on + abs(calibration.hysteresis)
    pos_on = abs(calibration.positive_threshold)
    pos_off = pos_on - abs(calibration.hysteresis)

    negative = previous_negative
    positive = previous_positive

    if previous_negative:
        if normalized > neg_off:
            negative = False
    else:
        if normalized <= neg_on:
            negative = True

    if previous_positive:
        if normalized < pos_off:
            positive = False
    else:
        if normalized >= pos_on:
            positive = True

    if negative and positive:
        if abs(normalized - neg_on) > abs(normalized - pos_on):
            negative = False
        else:
            positive = False

    return DigitalAxisOutput(negative=negative, positive=positive, normalized=normalized)
