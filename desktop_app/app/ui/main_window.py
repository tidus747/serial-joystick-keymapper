from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QStatusBar,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from app.core.controller import ApplicationController
from app.core.models import AXIS_NAMES, BUTTON_NAMES
from app.mapping.axis_processing import normalize_axis
from app.ui.widgets.button_indicator import ButtonIndicator
from app.ui.widgets.calibration_panel import AxisConfigWidget, ButtonConfigWidget
from app.ui.widgets.stick_widget import StickWidget


class MainWindow(QMainWindow):
    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller

        self._is_closing = False
        self._tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        self._minimize_notice_shown = False
        self.tray_icon: QSystemTrayIcon | None = None


        self.setWindowTitle("Serial Joystick Keymapper")
        self.resize(1360, 860)


        self.button_indicators: dict[str, ButtonIndicator] = {}
        self.button_config_widgets: dict[str, ButtonConfigWidget] = {}
        self.axis_config_widgets: dict[str, AxisConfigWidget] = {}

        self._build_ui()
        self._build_tray()
        self._connect_signals()
        self.refresh_ports()
        self.refresh_profiles()
        self.apply_config_to_ui()

    def _build_ui(self) -> None:
        self._build_toolbar()

        central = QWidget()
        layout = QVBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        live_panel = self._build_live_panel()
        config_panel = self._build_config_panel()

        splitter.addWidget(live_panel)
        splitter.addWidget(config_panel)
        splitter.setSizes([600, 700])
        layout.addWidget(splitter)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(500)
        self.log_output.setPlaceholderText("Status and error log")
        layout.addWidget(self.log_output, stretch=0)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addWidget(QLabel("Port"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(180)
        toolbar.addWidget(self.port_combo)

        self.refresh_ports_btn = QPushButton("Refresh")
        toolbar.addWidget(self.refresh_ports_btn)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Baud"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "230400", "250000", "500000"])
        self.baud_combo.setCurrentText("230400")
        toolbar.addWidget(self.baud_combo)

        self.connect_btn = QPushButton("Connect")
        toolbar.addWidget(self.connect_btn)

        toolbar.addSeparator()
        self.mapping_enabled_checkbox = QCheckBox("Enable Mapping")
        toolbar.addWidget(self.mapping_enabled_checkbox)

        self.panic_btn = QPushButton("Panic Stop")
        toolbar.addWidget(self.panic_btn)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Profile"))
        self.profile_combo = QComboBox()
        self.profile_combo.setEditable(True)
        self.profile_combo.setMinimumWidth(180)
        toolbar.addWidget(self.profile_combo)

        self.load_profile_btn = QPushButton("Load")
        self.save_profile_btn = QPushButton("Save")
        toolbar.addWidget(self.load_profile_btn)
        toolbar.addWidget(self.save_profile_btn)

    def _build_live_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        sticks_group = QGroupBox("Live Sticks")
        sticks_layout = QHBoxLayout(sticks_group)
        self.stick1_widget = StickWidget("Stick 1")
        self.stick2_widget = StickWidget("Stick 2")
        sticks_layout.addWidget(self.stick1_widget)
        sticks_layout.addWidget(self.stick2_widget)
        layout.addWidget(sticks_group)

        buttons_group = QGroupBox("Buttons")
        buttons_layout = QGridLayout(buttons_group)
        for idx, name in enumerate(BUTTON_NAMES):
            indicator = ButtonIndicator(name.upper())
            buttons_layout.addWidget(indicator, idx // 2, idx % 2)
            self.button_indicators[name] = indicator
        layout.addWidget(buttons_group)

        raw_group = QGroupBox("Raw ADC Values")
        raw_layout = QGridLayout(raw_group)
        self.raw_labels: dict[str, QLabel] = {}
        for row, axis_name in enumerate(AXIS_NAMES):
            raw_layout.addWidget(QLabel(axis_name), row, 0)
            label = QLabel("512")
            raw_layout.addWidget(label, row, 1)
            self.raw_labels[axis_name] = label
        layout.addWidget(raw_group)
        layout.addStretch(1)
        return panel

    def _build_config_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        tabs = QTabWidget()
        tabs.addTab(self._build_button_tab(), "Buttons")
        tabs.addTab(self._build_axis_tab(), "Axes")
        layout.addWidget(tabs)
        return panel

    def _build_button_tab(self) -> QWidget:
        tab = QWidget()
        layout = QGridLayout(tab)
        for idx, name in enumerate(BUTTON_NAMES):
            widget = ButtonConfigWidget(button_name=name, title=name.upper())
            layout.addWidget(widget, idx // 2, idx % 2)
            self.button_config_widgets[name] = widget
        return tab

    def _build_axis_tab(self) -> QWidget:
        tab = QWidget()
        layout = QGridLayout(tab)
        titles = {
            "stick1_x": "Stick 1 X",
            "stick1_y": "Stick 1 Y",
            "stick2_x": "Stick 2 X",
            "stick2_y": "Stick 2 Y",
        }
        for idx, name in enumerate(AXIS_NAMES):
            widget = AxisConfigWidget(axis_name=name, title=titles[name])
            layout.addWidget(widget, idx // 2, idx % 2)
            self.axis_config_widgets[name] = widget
        return tab

    def _build_tray(self) -> None:
        if not getattr(self, "_tray_available", False):
            self.tray_icon = None
            return

        icon = self.windowIcon()
        if icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            self.setWindowIcon(icon)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Serial Joystick Keymapper")

        show_action = QAction("Open", self)
        show_action.triggered.connect(self.show_normal)
        panic_action = QAction("Panic Stop", self)
        panic_action.triggered.connect(self.controller.panic_stop)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_application)

        tray_menu = QMenu(self)
        tray_menu.addAction(show_action)
        tray_menu.addAction(panic_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _connect_signals(self) -> None:
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.mapping_enabled_checkbox.toggled.connect(self.controller.set_mapping_enabled)
        self.panic_btn.clicked.connect(self.controller.panic_stop)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.load_profile_btn.clicked.connect(self.load_selected_profile)

        self.port_combo.currentTextChanged.connect(
            lambda text: self.controller.update_serial_settings(text, int(self.baud_combo.currentText()))
        )
        self.baud_combo.currentTextChanged.connect(
            lambda text: self.controller.update_serial_settings(self.port_combo.currentText(), int(text))
        )

        for widget in self.button_config_widgets.values():
            widget.mapping_changed.connect(self.controller.update_button_mapping)

        for widget in self.axis_config_widgets.values():
            widget.mapping_changed.connect(self.controller.update_axis_mapping)
            widget.capture_requested.connect(self.capture_axis_point)

        self.controller.status_changed.connect(self.append_log)
        self.controller.error_occurred.connect(self.show_error)
        self.controller.connection_changed.connect(self.on_connection_changed)
        self.controller.config_changed.connect(self._on_config_changed)
        self.controller.joystick_state_changed.connect(self.update_live_view)

    def refresh_ports(self) -> None:
        current = self.port_combo.currentText()
        ports = [port.device for port in list_ports.comports()]
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current and current in ports:
            self.port_combo.setCurrentText(current)
        self.port_combo.blockSignals(False)
        self.append_log(f"Detected serial ports: {', '.join(ports) if ports else 'none'}")

    def _on_config_changed(self, _config) -> None:
        self.apply_config_to_ui()

    def refresh_profiles(self) -> None:
        current = self.profile_combo.currentText()
        profiles = self.controller.list_profiles()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(profiles)
        if current:
            self.profile_combo.setCurrentText(current)
        self.profile_combo.blockSignals(False)

    def apply_config_to_ui(self) -> None:
        config = self.controller.config
        self.port_combo.blockSignals(True)
        if config.serial_port:
            if self.port_combo.findText(config.serial_port) < 0:
                self.port_combo.addItem(config.serial_port)
            self.port_combo.setCurrentText(config.serial_port)
        self.port_combo.blockSignals(False)

        self.baud_combo.blockSignals(True)
        self.baud_combo.setCurrentText(str(config.baudrate))
        self.baud_combo.blockSignals(False)

        self.mapping_enabled_checkbox.blockSignals(True)
        self.mapping_enabled_checkbox.setChecked(config.mapping_enabled)
        self.mapping_enabled_checkbox.blockSignals(False)

        self.profile_combo.blockSignals(True)
        if config.profile_name:
            if self.profile_combo.findText(config.profile_name) < 0:
                self.profile_combo.addItem(config.profile_name)
            self.profile_combo.setCurrentText(config.profile_name)
        self.profile_combo.blockSignals(False)

        for name, widget in self.button_config_widgets.items():
            widget.set_mapping(config.buttons[name])
        for name, widget in self.axis_config_widgets.items():
            widget.set_mapping(config.axes[name])

    def toggle_connection(self) -> None:
        if self.controller.connected:
            self.controller.disconnect_serial()
        else:
            port = self.port_combo.currentText().strip()
            baud = int(self.baud_combo.currentText())
            self.controller.update_serial_settings(port, baud)
            self.controller.connect_serial(port, baud)

    def on_connection_changed(self, connected: bool) -> None:
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self.statusBar().showMessage("Connected" if connected else "Disconnected")

    def update_live_view(self, state) -> None:
        for name, indicator in self.button_indicators.items():
            indicator.set_active(state.buttons[name])
        for name, label in self.raw_labels.items():
            label.setText(str(state.axes_raw[name]))

        x1 = normalize_axis(state.axes_raw["stick1_x"], self.controller.config.axes["stick1_x"].calibration)
        y1 = normalize_axis(state.axes_raw["stick1_y"], self.controller.config.axes["stick1_y"].calibration)
        x2 = normalize_axis(state.axes_raw["stick2_x"], self.controller.config.axes["stick2_x"].calibration)
        y2 = normalize_axis(state.axes_raw["stick2_y"], self.controller.config.axes["stick2_y"].calibration)
        self.stick1_widget.set_position(x1, y1)
        self.stick2_widget.set_position(x2, y2)

    def capture_axis_point(self, axis_name: str, point_type: str) -> None:
        current_value = self.controller.joystick_state.axes_raw[axis_name]
        widget = self.axis_config_widgets[axis_name]
        if point_type == "min":
            widget.raw_min.setValue(current_value)
        elif point_type == "center":
            widget.raw_center.setValue(current_value)
        elif point_type == "max":
            widget.raw_max.setValue(current_value)
        widget._emit_change()
        self.append_log(f"Captured {point_type} for {axis_name}: {current_value}")

    def save_profile(self) -> None:
        name = self.profile_combo.currentText().strip() or "default"
        self.controller.save_profile(name)
        self.refresh_profiles()
        self.profile_combo.setCurrentText(name)

    def load_selected_profile(self) -> None:
        name = self.profile_combo.currentText().strip()
        if not name:
            self.show_error("No profile selected")
            return
        try:
            self.controller.load_profile(name)
            self.refresh_profiles()
        except FileNotFoundError:
            self.show_error(f"Profile not found: {name}")

    def append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)
        self.statusBar().showMessage(message, 5000)

    def show_error(self, message: str) -> None:
        self.append_log(f"ERROR: {message}")
        QMessageBox.warning(self, "Error", message)

    def show_normal(self) -> None:
        self.show()
        self.setWindowState((self.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_normal()

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().changeEvent(event)
        if not self._tray_available:
            return
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.hide)
            if self.tray_icon is not None and not self._minimize_notice_shown:
                self.tray_icon.showMessage(
                    "Serial Joystick Keymapper",
                    "The application is still running in the system tray.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2500,
                )
                self._minimize_notice_shown = True

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._is_closing or not self._tray_available:
            super().closeEvent(event)
            return

        event.ignore()
        self.hide()
        if self.tray_icon is not None:
            self.tray_icon.showMessage(
                "Serial Joystick Keymapper",
                "The application is still running in the system tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )

    def _quit_application(self) -> None:
        self._is_closing = True
        self.controller.disconnect_serial()
        self.controller.panic_stop()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.close()
