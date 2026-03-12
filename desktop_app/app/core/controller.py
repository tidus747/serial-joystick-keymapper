from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app.mapping.actions import AxisDigitalState
from app.mapping.axis_processing import compute_digital_axis, normalize_axis
from app.mapping.keyboard_mouse import KeyboardMouseInjector
from app.profiles.profile_manager import ProfileManager
from app.serial.serial_reader import SerialReaderThread

from .models import AXIS_NAMES, BUTTON_NAMES, AppConfig, AxisMapping, ButtonMapping, JoystickState
from .state_store import StateStore


class ApplicationController(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)
    connection_changed = Signal(bool)
    config_changed = Signal(object)
    joystick_state_changed = Signal(object)

    def __init__(self, profiles_dir: Path) -> None:
        super().__init__()
        self.store = StateStore()
        self.profile_manager = ProfileManager(profiles_dir)
        self.injector = KeyboardMouseInjector()
        self.serial_thread: SerialReaderThread | None = None
        self._connected = False
        self._last_button_states = {name: False for name in BUTTON_NAMES}
        self._axis_digital_states = {name: AxisDigitalState() for name in AXIS_NAMES}

        self.store.config_changed.connect(self.config_changed.emit)
        self.store.joystick_state_changed.connect(self._handle_joystick_state)
        self.store.joystick_state_changed.connect(self.joystick_state_changed.emit)

    @property
    def config(self) -> AppConfig:
        return self.store.config

    @property
    def joystick_state(self) -> JoystickState:
        return self.store.joystick_state

    @property
    def connected(self) -> bool:
        return self._connected

    def connect_serial(self, port: str, baudrate: int) -> None:
        self.disconnect_serial()
        if not port:
            self.error_occurred.emit("No serial port selected")
            return
        self.serial_thread = SerialReaderThread(port, baudrate)
        self.serial_thread.state_received.connect(self.store.set_joystick_state)
        self.serial_thread.status_changed.connect(self.status_changed.emit)
        self.serial_thread.error_occurred.connect(self.error_occurred.emit)
        self.serial_thread.connection_changed.connect(self._on_connection_changed)
        self.serial_thread.start()

    def disconnect_serial(self) -> None:
        if self.serial_thread is not None:
            self.serial_thread.stop()
            self.serial_thread = None
        self._on_connection_changed(False)

    def _on_connection_changed(self, connected: bool) -> None:
        self._connected = connected
        self.connection_changed.emit(connected)
        if not connected:
            self.injector.release_all()

    def set_mapping_enabled(self, enabled: bool) -> None:
        config = self.config
        config.mapping_enabled = enabled
        self.store.set_config(config)
        if not enabled:
            self.injector.release_all()

    def panic_stop(self) -> None:
        self.injector.release_all()
        self.set_mapping_enabled(False)
        self.status_changed.emit("Panic stop executed: mappings disabled and held inputs released")

    def update_serial_settings(self, port: str, baudrate: int) -> None:
        config = self.config
        config.serial_port = port
        config.baudrate = baudrate
        self.store.set_config(config)

    def update_button_mapping(self, name: str, mapping: ButtonMapping) -> None:
        config = self.config
        config.buttons[name] = mapping
        self.store.set_config(config)

    def update_axis_mapping(self, name: str, mapping: AxisMapping) -> None:
        config = self.config
        config.axes[name] = mapping
        self.store.set_config(config)

    def save_profile(self, name: str) -> Path:
        path = self.profile_manager.save(name, self.config)
        self.status_changed.emit(f"Saved profile to {path.name}")
        return path

    def load_profile(self, name: str) -> None:
        config = self.profile_manager.load(name)
        self.store.set_config(config)
        self.status_changed.emit(f"Loaded profile {name}")

    def list_profiles(self) -> list[str]:
        return self.profile_manager.list_profiles()

    def _handle_joystick_state(self, state: JoystickState) -> None:
        if not self.config.mapping_enabled:
            self._last_button_states = dict(state.buttons)
            return

        self._process_buttons(state)
        self._process_axes(state)
        self._last_button_states = dict(state.buttons)

    def _process_buttons(self, state: JoystickState) -> None:
        for name in BUTTON_NAMES:
            pressed = state.buttons[name]
            was_pressed = self._last_button_states[name]
            mapping = self.config.buttons[name]

            if mapping.mode == "none":
                continue

            if mapping.behavior == "press":
                if pressed and not was_pressed:
                    self._fire_press(mapping)
            elif mapping.behavior == "hold":
                self._update_hold(mapping, pressed)

    def _process_axes(self, state: JoystickState) -> None:
        mouse_dx = 0.0
        mouse_dy = 0.0

        for name in AXIS_NAMES:
            axis_mapping = self.config.axes[name]
            raw = state.axes_raw[name]

            if axis_mapping.mode == "none":
                self._release_axis_keys(name, axis_mapping)
                continue

            if axis_mapping.mode == "digital_axis":
                digital_state = self._axis_digital_states[name]
                result = compute_digital_axis(
                    raw,
                    axis_mapping.calibration,
                    digital_state.negative_active,
                    digital_state.positive_active,
                )
                self._apply_digital_axis(name, axis_mapping, result.negative, result.positive)
            elif axis_mapping.mode == "mouse_axis":
                self._release_axis_keys(name, axis_mapping)
                normalized = normalize_axis(raw, axis_mapping.calibration)
                delta = normalized * 12.0
                if axis_mapping.target == "mouse_x":
                    mouse_dx += delta
                else:
                    mouse_dy += delta

        self.injector.move_mouse(int(round(mouse_dx)), int(round(mouse_dy)))

    def _fire_press(self, mapping: ButtonMapping) -> None:
        if mapping.mode == "keyboard":
            self.injector.tap_key(mapping.key)
        elif mapping.mode == "mouse_button":
            self.injector.click_mouse(mapping.mouse_button)

    def _update_hold(self, mapping: ButtonMapping, pressed: bool) -> None:
        if mapping.mode == "keyboard":
            if pressed:
                self.injector.hold_key(mapping.key)
            else:
                self.injector.release_key(mapping.key)
        elif mapping.mode == "mouse_button":
            if pressed:
                self.injector.hold_mouse_button(mapping.mouse_button)
            else:
                self.injector.release_mouse_button(mapping.mouse_button)

    def _apply_digital_axis(self, axis_name: str, mapping: AxisMapping, negative_active: bool, positive_active: bool) -> None:
        state = self._axis_digital_states[axis_name]
        state.negative_active = negative_active
        state.positive_active = positive_active

        if negative_active:
            self.injector.hold_key(mapping.negative_key)
        else:
            self.injector.release_key(mapping.negative_key)

        if positive_active:
            self.injector.hold_key(mapping.positive_key)
        else:
            self.injector.release_key(mapping.positive_key)

    def _release_axis_keys(self, axis_name: str, mapping: AxisMapping) -> None:
        state = self._axis_digital_states[axis_name]
        if state.negative_active:
            self.injector.release_key(mapping.negative_key)
        if state.positive_active:
            self.injector.release_key(mapping.positive_key)
        state.negative_active = False
        state.positive_active = False
