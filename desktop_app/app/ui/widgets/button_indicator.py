from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class ButtonIndicator(QFrame):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(110)
        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state = QLabel("Released")
        self._state.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._state)

        self.set_active(False)

    def set_active(self, active: bool) -> None:
        text = "Pressed" if active else "Released"
        self._state.setText(text)
        self.setStyleSheet(
            "QFrame {border: 1px solid #888; border-radius: 6px; background: %s;}"
            % ("#4caf50" if active else "#3a3a3a")
        )
