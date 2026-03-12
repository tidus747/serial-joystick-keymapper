from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QThread, Signal
import serial

from app.core.models import JoystickState
from .protocol import ProtocolError, parse_frame


class SerialReaderThread(QThread):
    state_received = Signal(object)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    connection_changed = Signal(bool)

    def __init__(self, port: str, baudrate: int, parent=None) -> None:
        super().__init__(parent)
        self._port = port
        self._baudrate = baudrate
        self._stop_requested = False
        self._serial: Optional[serial.Serial] = None

    def stop(self) -> None:
        self._stop_requested = True
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except serial.SerialException:
                pass
        self.wait(1500)

    def run(self) -> None:
        try:
            self.status_changed.emit(f"Opening {self._port} at {self._baudrate} baud")
            self._serial = serial.Serial(self._port, self._baudrate, timeout=0.2)
            self.connection_changed.emit(True)
            self.status_changed.emit("Serial connection established")

            while not self._stop_requested:
                raw = self._serial.readline()
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8", errors="replace")
                    state: JoystickState = parse_frame(line)
                except ProtocolError as exc:
                    self.error_occurred.emit(str(exc))
                    continue
                except UnicodeDecodeError:
                    self.error_occurred.emit("Failed to decode serial frame")
                    continue

                self.state_received.emit(state)

        except serial.SerialException as exc:
            self.error_occurred.emit(f"Serial error: {exc}")
        finally:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except serial.SerialException:
                    pass
            self.connection_changed.emit(False)
            self.status_changed.emit("Serial connection closed")
