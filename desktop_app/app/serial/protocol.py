from __future__ import annotations

from app.core.models import BUTTON_NAMES, AXIS_NAMES, JoystickState


class ProtocolError(ValueError):
    pass


def parse_frame(line: str) -> JoystickState:
    text = line.strip()
    if not text:
        raise ProtocolError("Empty frame")

    parts = text.split(",")
    if len(parts) != 9 or parts[0] != "T":
        raise ProtocolError(f"Invalid frame format: {text!r}")

    try:
        button_values = [bool(int(value)) for value in parts[1:5]]
        axis_values = [int(value) for value in parts[5:9]]
    except ValueError as exc:
        raise ProtocolError(f"Failed to parse frame values: {text!r}") from exc

    return JoystickState(
        buttons={name: value for name, value in zip(BUTTON_NAMES, button_values, strict=True)},
        axes_raw={name: value for name, value in zip(AXIS_NAMES, axis_values, strict=True)},
    )
