"""Custom-painted floating usage ball."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from ui.qt_theme import current_theme, theme_controller


DESIGN_SIZE = 120


class FloatingUsageBall(QWidget):
    pressed = Signal(QPoint)
    dragged = Signal(QPoint)
    released = Signal(QPoint)

    def __init__(self, size: int = 88, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._today = "--"
        self._balance = "--"
        self._peak_highlight = False
        self._hovered = False
        self._active = False
        theme_controller().changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _mode: str, _resolved: str) -> None:
        self.update()

    def set_values(self, today: str, balance: str) -> None:
        if self._today == today and self._balance == balance:
            return
        self._today = today
        self._balance = balance
        self.update()

    def set_peak_highlight(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._peak_highlight == enabled:
            return
        self._peak_highlight = enabled
        self.update()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
            self.pressed.emit(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.dragged.emit(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.update()
            self.released.emit(event.globalPosition().toPoint())
            event.accept()

    def paintEvent(self, _event) -> None:
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        side = min(self.width(), self.height())
        painter.scale(side / DESIGN_SIZE, side / DESIGN_SIZE)
        side = DESIGN_SIZE
        center = QPointF(side / 2, side / 2)

        # The light warning token is tuned for text contrast and looks brown as
        # emitted light; use saturated amber for the peak glow instead.
        peak_color = QColor("#FFB000" if theme.name == "light" else theme.warning)
        ball_radius = side / 2 - (8 if self._peak_highlight else 3)
        if self._peak_highlight:
            # Keep the outermost pixels transparent so antialiasing is completed
            # inside the widget instead of being clipped into a jagged edge.
            halo_radius = side / 2 - 2
            halo = QRadialGradient(center, halo_radius)
            transparent_warning = QColor(peak_color)
            transparent_warning.setAlpha(0)
            soft_warning = QColor(peak_color)
            soft_warning.setAlpha(64 if self._hovered else 48)
            bright_warning = QColor(peak_color)
            bright_warning.setAlpha(220 if self._hovered else 190)
            outer_warning = QColor(peak_color)
            outer_warning.setAlpha(82 if self._hovered else 62)
            halo.setColorAt(0.82, transparent_warning)
            halo.setColorAt(0.88, soft_warning)
            halo.setColorAt(0.93, bright_warning)
            halo.setColorAt(0.97, outer_warning)
            halo.setColorAt(1.0, transparent_warning)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(halo)
            painter.drawEllipse(center, halo_radius, halo_radius)
        else:
            glow = QColor(theme.accent)
            glow.setAlpha(24 if self._active else 70 if self._hovered else 36)
            painter.setPen(QPen(glow, 4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, side / 2 - 3, side / 2 - 3)

        outer = QRadialGradient(center, ball_radius)
        outer.setColorAt(0.0, QColor(theme.elevated))
        outer.setColorAt(0.72, QColor(theme.surface))
        outer.setColorAt(1.0, QColor(theme.window))
        painter.setBrush(outer)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, ball_radius, ball_radius)

        if self._peak_highlight:
            border_color = QColor(peak_color)
            border_color.setAlpha(210 if self._active else 235)
            painter.setPen(QPen(border_color, 3))
        else:
            painter.setPen(
                QPen(QColor(theme.border_hover if self._hovered else theme.accent), 2)
            )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, ball_radius, ball_radius)

        highlight = QLinearGradient(0, 8, 0, side * 0.55)
        highlight_start = QColor(theme.accent)
        highlight_start.setAlpha(42)
        highlight_end = QColor(theme.accent)
        highlight_end.setAlpha(0)
        highlight.setColorAt(0.0, highlight_start)
        highlight.setColorAt(1.0, highlight_end)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(highlight)
        painter.drawEllipse(QRectF(16, 12, side - 32, side * 0.42))

        painter.setPen(QColor(theme.subtext))
        painter.setFont(QFont("Microsoft YaHei UI", 9))
        painter.drawText(
            QRectF(10, 18, side - 20, 18),
            Qt.AlignmentFlag.AlignCenter,
            "今日使用",
        )

        painter.setPen(QColor(theme.value))
        value_size = 16 if len(self._today) <= 8 else 12
        painter.setFont(QFont("Microsoft YaHei UI", value_size, QFont.Weight.Bold))
        painter.drawText(QRectF(8, 34, side - 16, 25), Qt.AlignmentFlag.AlignCenter, self._today)

        painter.setPen(QPen(QColor(theme.border), 1))
        painter.drawLine(QPointF(side * 0.25, 64), QPointF(side * 0.75, 64))
        painter.setPen(QColor(theme.subtext))
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.drawText(QRectF(10, 65, side - 20, 15), Qt.AlignmentFlag.AlignCenter, "余额")
        painter.setPen(QColor(theme.accent_hover))
        balance_size = 11 if len(self._balance) <= 8 else 9
        painter.setFont(QFont("Microsoft YaHei UI", balance_size, QFont.Weight.DemiBold))
        painter.drawText(QRectF(14, 80, side - 28, 19), Qt.AlignmentFlag.AlignCenter, self._balance)
        painter.end()
