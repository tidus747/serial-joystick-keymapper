from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject, Signal

from .models import AppConfig, JoystickState


class StateStore(QObject):
    config_changed = Signal(object)
    joystick_state_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._config = AppConfig()
        self._joystick_state = JoystickState()

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def joystick_state(self) -> JoystickState:
        return self._joystick_state

    def set_config(self, config: AppConfig) -> None:
        self._config = config
        self.config_changed.emit(config)

    def update_config(self, config: AppConfig) -> None:
        self.set_config(replace(config))

    def set_joystick_state(self, state: JoystickState) -> None:
        self._joystick_state = state
        self.joystick_state_changed.emit(state)
