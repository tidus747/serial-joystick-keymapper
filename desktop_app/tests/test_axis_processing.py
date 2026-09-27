import pytest

from app.core.models import AxisCalibration
from app.mapping.axis_processing import compute_digital_axis, normalize_axis


def test_normalize_axis_center_is_zero():
    calibration = AxisCalibration(raw_min=0, raw_center=512, raw_max=1023)

    assert normalize_axis(512, calibration) == 0.0


def test_normalize_axis_reaches_limits():
    calibration = AxisCalibration(
        raw_min=0,
        raw_center=512,
        raw_max=1023,
        deadzone=0.0,
        expo=1.0,
    )

    assert normalize_axis(0, calibration) == pytest.approx(-1.0)
    assert normalize_axis(1023, calibration) == pytest.approx(1.0)


def test_normalize_axis_inversion():
    calibration = AxisCalibration(
        raw_min=0,
        raw_center=512,
        raw_max=1023,
        deadzone=0.0,
        expo=1.0,
        invert=True,
    )

    assert normalize_axis(1023, calibration) == pytest.approx(-1.0)


def test_digital_axis_uses_hysteresis():
    calibration = AxisCalibration(
        raw_min=0,
        raw_center=500,
        raw_max=1000,
        deadzone=0.0,
        expo=1.0,
        positive_threshold=0.4,
        hysteresis=0.1,
    )

    active = compute_digital_axis(
        raw=750,
        calibration=calibration,
        previous_negative=False,
        previous_positive=False,
    )
    assert active.positive is True

    still_active = compute_digital_axis(
        raw=675,
        calibration=calibration,
        previous_negative=False,
        previous_positive=True,
    )
    assert still_active.positive is True

    released = compute_digital_axis(
        raw=625,
        calibration=calibration,
        previous_negative=False,
        previous_positive=True,
    )
    assert released.positive is False
