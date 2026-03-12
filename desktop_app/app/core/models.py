from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AXIS_NAMES = ["stick1_x", "stick1_y", "stick2_x", "stick2_y"]
BUTTON_NAMES = ["btn1", "btn2", "btn3", "btn4"]
MouseButtonName = Literal["left", "right", "middle"]
ButtonMode = Literal["none", "keyboard", "mouse_button"]
ButtonBehavior = Literal["press", "hold"]
AxisMode = Literal["none", "digital_axis", "mouse_axis"]
MouseTarget = Literal["mouse_x", "mouse_y"]


@dataclass(slots=True)
class JoystickState:
    buttons: dict[str, bool] = field(default_factory=lambda: {name: False for name in BUTTON_NAMES})
    axes_raw: dict[str, int] = field(default_factory=lambda: {name: 512 for name in AXIS_NAMES})


@dataclass(slots=True)
class AxisCalibration:
    raw_min: int = 0
    raw_center: int = 512
    raw_max: int = 1023
    deadzone: float = 0.06
    invert: bool = False
    sensitivity: float = 1.0
    expo: float = 1.4
    negative_threshold: float = 0.35
    positive_threshold: float = 0.35
    hysteresis: float = 0.08


@dataclass(slots=True)
class ButtonMapping:
    mode: ButtonMode = "none"
    behavior: ButtonBehavior = "press"
    key: str = "space"
    mouse_button: MouseButtonName = "left"


@dataclass(slots=True)
class AxisMapping:
    mode: AxisMode = "none"
    negative_key: str = "a"
    positive_key: str = "d"
    target: MouseTarget = "mouse_x"
    calibration: AxisCalibration = field(default_factory=AxisCalibration)


@dataclass(slots=True)
class AppConfig:
    serial_port: str = ""
    baudrate: int = 230400
    start_minimized: bool = False
    mapping_enabled: bool = False
    profile_name: str = "default"
    buttons: dict[str, ButtonMapping] = field(
        default_factory=lambda: {name: ButtonMapping() for name in BUTTON_NAMES}
    )
    axes: dict[str, AxisMapping] = field(
        default_factory=lambda: {name: AxisMapping() for name in AXIS_NAMES}
    )
