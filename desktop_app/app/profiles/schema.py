from __future__ import annotations

from dataclasses import asdict

from app.core.models import AppConfig, AxisCalibration, AxisMapping, ButtonMapping


def config_to_dict(config: AppConfig) -> dict:
    return asdict(config)


def config_from_dict(data: dict) -> AppConfig:
    config = AppConfig(
        serial_port=data.get("serial_port", ""),
        baudrate=int(data.get("baudrate", 230400)),
        start_minimized=bool(data.get("start_minimized", False)),
        mapping_enabled=bool(data.get("mapping_enabled", False)),
        profile_name=str(data.get("profile_name", "default")),
    )

    buttons = data.get("buttons", {})
    for name, mapping_data in buttons.items():
        if name not in config.buttons:
            continue
        config.buttons[name] = ButtonMapping(
            mode=mapping_data.get("mode", "none"),
            behavior=mapping_data.get("behavior", "press"),
            key=mapping_data.get("key", "space"),
            mouse_button=mapping_data.get("mouse_button", "left"),
        )

    axes = data.get("axes", {})
    for name, mapping_data in axes.items():
        if name not in config.axes:
            continue
        calibration_data = mapping_data.get("calibration", {})
        calibration = AxisCalibration(
            raw_min=int(calibration_data.get("raw_min", 0)),
            raw_center=int(calibration_data.get("raw_center", 512)),
            raw_max=int(calibration_data.get("raw_max", 1023)),
            deadzone=float(calibration_data.get("deadzone", 0.06)),
            invert=bool(calibration_data.get("invert", False)),
            sensitivity=float(calibration_data.get("sensitivity", 1.0)),
            expo=float(calibration_data.get("expo", 1.4)),
            negative_threshold=float(calibration_data.get("negative_threshold", 0.35)),
            positive_threshold=float(calibration_data.get("positive_threshold", 0.35)),
            hysteresis=float(calibration_data.get("hysteresis", 0.08)),
        )
        config.axes[name] = AxisMapping(
            mode=mapping_data.get("mode", "none"),
            negative_key=mapping_data.get("negative_key", "a"),
            positive_key=mapping_data.get("positive_key", "d"),
            target=mapping_data.get("target", "mouse_x"),
            calibration=calibration,
        )

    return config
