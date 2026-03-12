from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class StickWidget(QWidget):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self._title = title
        self._x = 0.0
        self._y = 0.0
        self.setMinimumSize(220, 220)

    def set_position(self, x_value: float, y_value: float) -> None:
        self._x = max(-1.0, min(1.0, x_value))
        self._y = max(-1.0, min(1.0, y_value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 28, -12, -12)
        square = min(rect.width(), rect.height())
        box = QRectF(rect.center().x() - square / 2, rect.center().y() - square / 2, square, square)

        painter.fillRect(self.rect(), QColor("#202124"))
        painter.setPen(QPen(QColor("#aaaaaa"), 1))
        painter.drawText(12, 20, self._title)

        painter.setPen(QPen(QColor("#777777"), 1))
        painter.drawRect(box)
        painter.drawLine(box.center().x(), box.top(), box.center().x(), box.bottom())
        painter.drawLine(box.left(), box.center().y(), box.right(), box.center().y())

        radius = 6
        center = QPointF(
            box.center().x() + (self._x * (box.width() / 2)),
            box.center().y() - (self._y * (box.height() / 2)),
        )
        painter.setPen(QPen(QColor("#87cefa"), 2))
        painter.setBrush(QColor("#87cefa"))
        painter.drawEllipse(center, radius, radius)
