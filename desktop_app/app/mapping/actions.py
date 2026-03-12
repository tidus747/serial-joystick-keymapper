from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ButtonActionState:
    active: bool = False


@dataclass(slots=True)
class AxisDigitalState:
    negative_active: bool = False
    positive_active: bool = False
