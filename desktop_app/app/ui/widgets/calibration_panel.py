from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.models import AxisMapping, ButtonMapping


class ButtonConfigWidget(QWidget):
    mapping_changed = Signal(str, object)

    def __init__(self, button_name: str, title: str, parent=None) -> None:
        super().__init__(parent)
        self.button_name = button_name

        self.group = QGroupBox(title)
        form = QFormLayout(self.group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["none", "keyboard", "mouse_button"])
        self.behavior_combo = QComboBox()
        self.behavior_combo.addItems(["press", "hold"])
        self.key_edit = QLineEdit("space")
        self.mouse_combo = QComboBox()
        self.mouse_combo.addItems(["left", "right", "middle"])

        form.addRow("Mode", self.mode_combo)
        form.addRow("Behavior", self.behavior_combo)
        form.addRow("Keyboard key", self.key_edit)
        form.addRow("Mouse button", self.mouse_combo)

        layout = QVBoxLayout(self)
        layout.addWidget(self.group)

        self.mode_combo.currentTextChanged.connect(self._emit_change)
        self.behavior_combo.currentTextChanged.connect(self._emit_change)
        self.key_edit.editingFinished.connect(self._emit_change)
        self.mouse_combo.currentTextChanged.connect(self._emit_change)

    def set_mapping(self, mapping: ButtonMapping) -> None:
        blockers = [
            QSignalBlocker(self.mode_combo),
            QSignalBlocker(self.behavior_combo),
            QSignalBlocker(self.key_edit),
            QSignalBlocker(self.mouse_combo),
        ]
        self.mode_combo.setCurrentText(mapping.mode)
        self.behavior_combo.setCurrentText(mapping.behavior)
        self.key_edit.setText(mapping.key)
        self.mouse_combo.setCurrentText(mapping.mouse_button)
        del blockers

    def _emit_change(self) -> None:
        mapping = ButtonMapping(
            mode=self.mode_combo.currentText(),
            behavior=self.behavior_combo.currentText(),
            key=self.key_edit.text().strip() or "space",
            mouse_button=self.mouse_combo.currentText(),
        )
        self.mapping_changed.emit(self.button_name, mapping)


class AxisConfigWidget(QWidget):
    mapping_changed = Signal(str, object)
    capture_requested = Signal(str, str)

    def __init__(self, axis_name: str, title: str, parent=None) -> None:
        super().__init__(parent)
        self.axis_name = axis_name

        outer_layout = QVBoxLayout(self)

        mapping_group = QGroupBox(title)
        mapping_form = QFormLayout(mapping_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["none", "digital_axis", "mouse_axis"])

        self.negative_key_edit = QLineEdit("a")
        self.positive_key_edit = QLineEdit("d")
        self.target_combo = QComboBox()
        self.target_combo.addItems(["mouse_x", "mouse_y"])

        mapping_form.addRow("Mode", self.mode_combo)
        mapping_form.addRow("Negative key", self.negative_key_edit)
        mapping_form.addRow("Positive key", self.positive_key_edit)
        mapping_form.addRow("Mouse target", self.target_combo)

        calibration_group = QGroupBox("Calibration")
        calibration_form = QFormLayout(calibration_group)

        self.raw_min = QSpinBox()
        self.raw_min.setRange(0, 1023)
        self.raw_center = QSpinBox()
        self.raw_center.setRange(0, 1023)
        self.raw_max = QSpinBox()
        self.raw_max.setRange(0, 1023)

        self.deadzone = QDoubleSpinBox()
        self.deadzone.setRange(0.0, 0.50)
        self.deadzone.setDecimals(3)
        self.deadzone.setSingleStep(0.01)

        self.sensitivity = QDoubleSpinBox()
        self.sensitivity.setRange(0.0, 5.0)
        self.sensitivity.setDecimals(3)
        self.sensitivity.setSingleStep(0.05)

        self.expo = QDoubleSpinBox()
        self.expo.setRange(0.1, 5.0)
        self.expo.setDecimals(3)
        self.expo.setSingleStep(0.05)

        self.neg_threshold = QDoubleSpinBox()
        self.neg_threshold.setRange(0.0, 1.0)
        self.neg_threshold.setDecimals(3)
        self.neg_threshold.setSingleStep(0.01)

        self.pos_threshold = QDoubleSpinBox()
        self.pos_threshold.setRange(0.0, 1.0)
        self.pos_threshold.setDecimals(3)
        self.pos_threshold.setSingleStep(0.01)

        self.hysteresis = QDoubleSpinBox()
        self.hysteresis.setRange(0.0, 0.5)
        self.hysteresis.setDecimals(3)
        self.hysteresis.setSingleStep(0.01)

        self.invert = QCheckBox("Invert axis")

        capture_layout = QHBoxLayout()
        self.capture_min_btn = QPushButton("Capture Min")
        self.capture_center_btn = QPushButton("Capture Center")
        self.capture_max_btn = QPushButton("Capture Max")
        capture_layout.addWidget(self.capture_min_btn)
        capture_layout.addWidget(self.capture_center_btn)
        capture_layout.addWidget(self.capture_max_btn)

        calibration_form.addRow("Raw Min", self.raw_min)
        calibration_form.addRow("Raw Center", self.raw_center)
        calibration_form.addRow("Raw Max", self.raw_max)
        calibration_form.addRow("Deadzone", self.deadzone)
        calibration_form.addRow("Sensitivity", self.sensitivity)
        calibration_form.addRow("Expo", self.expo)
        calibration_form.addRow("Negative threshold", self.neg_threshold)
        calibration_form.addRow("Positive threshold", self.pos_threshold)
        calibration_form.addRow("Hysteresis", self.hysteresis)
        calibration_form.addRow(self.invert)
        calibration_form.addRow(QLabel("Quick capture"), self._wrap_layout(capture_layout))

        outer_layout.addWidget(mapping_group)
        outer_layout.addWidget(calibration_group)
        outer_layout.addStretch(1)

        for widget in [
            self.mode_combo,
            self.negative_key_edit,
            self.positive_key_edit,
            self.target_combo,
            self.raw_min,
            self.raw_center,
            self.raw_max,
            self.deadzone,
            self.sensitivity,
            self.expo,
            self.neg_threshold,
            self.pos_threshold,
            self.hysteresis,
            self.invert,
        ]:
            if hasattr(widget, "editingFinished"):
                widget.editingFinished.connect(self._emit_change)
            if hasattr(widget, "valueChanged"):
                widget.valueChanged.connect(self._emit_change)
            if hasattr(widget, "currentTextChanged"):
                widget.currentTextChanged.connect(self._emit_change)
            if hasattr(widget, "stateChanged"):
                widget.stateChanged.connect(self._emit_change)

        self.capture_min_btn.clicked.connect(lambda: self.capture_requested.emit(self.axis_name, "min"))
        self.capture_center_btn.clicked.connect(lambda: self.capture_requested.emit(self.axis_name, "center"))
        self.capture_max_btn.clicked.connect(lambda: self.capture_requested.emit(self.axis_name, "max"))

    @staticmethod
    def _wrap_layout(layout: QHBoxLayout) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def set_mapping(self, mapping: AxisMapping) -> None:
        blockers = [
            QSignalBlocker(self.mode_combo),
            QSignalBlocker(self.negative_key_edit),
            QSignalBlocker(self.positive_key_edit),
            QSignalBlocker(self.target_combo),
            QSignalBlocker(self.raw_min),
            QSignalBlocker(self.raw_center),
            QSignalBlocker(self.raw_max),
            QSignalBlocker(self.deadzone),
            QSignalBlocker(self.sensitivity),
            QSignalBlocker(self.expo),
            QSignalBlocker(self.neg_threshold),
            QSignalBlocker(self.pos_threshold),
            QSignalBlocker(self.hysteresis),
            QSignalBlocker(self.invert),
        ]
        self.mode_combo.setCurrentText(mapping.mode)
        self.negative_key_edit.setText(mapping.negative_key)
        self.positive_key_edit.setText(mapping.positive_key)
        self.target_combo.setCurrentText(mapping.target)

        calibration = mapping.calibration
        self.raw_min.setValue(calibration.raw_min)
        self.raw_center.setValue(calibration.raw_center)
        self.raw_max.setValue(calibration.raw_max)
        self.deadzone.setValue(calibration.deadzone)
        self.sensitivity.setValue(calibration.sensitivity)
        self.expo.setValue(calibration.expo)
        self.neg_threshold.setValue(calibration.negative_threshold)
        self.pos_threshold.setValue(calibration.positive_threshold)
        self.hysteresis.setValue(calibration.hysteresis)
        self.invert.setChecked(calibration.invert)
        del blockers

    def _emit_change(self, *args) -> None:
        mapping = AxisMapping(
            mode=self.mode_combo.currentText(),
            negative_key=self.negative_key_edit.text().strip() or "a",
            positive_key=self.positive_key_edit.text().strip() or "d",
            target=self.target_combo.currentText(),
        )
        calibration = mapping.calibration
        calibration.raw_min = self.raw_min.value()
        calibration.raw_center = self.raw_center.value()
        calibration.raw_max = self.raw_max.value()
        calibration.deadzone = self.deadzone.value()
        calibration.sensitivity = self.sensitivity.value()
        calibration.expo = self.expo.value()
        calibration.negative_threshold = self.neg_threshold.value()
        calibration.positive_threshold = self.pos_threshold.value()
        calibration.hysteresis = self.hysteresis.value()
        calibration.invert = self.invert.isChecked()
        self.mapping_changed.emit(self.axis_name, mapping)
