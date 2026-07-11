"""Codex-inspired monitoring panel built from PySide6 widgets."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pyqtgraph as pg
from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStyle,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

import config_manager
from data.store import TokenData
from ui.activity import compact_tokens
from ui.qt_heatmap import TokenActivityHeatmap
from ui.qt_theme import app_icon, current_theme, fluent_icon, theme_controller


PANEL_MIN_WIDTH = 640
PANEL_MAX_WIDTH = 820
PANEL_HEIGHT = 550
HEADER_HEIGHT = 50
TOP_SECTION_HEIGHT = 154
ACTIVITY_SECTION_HEIGHT = 176
STATISTICS_SECTION_HEIGHT = 92
STATUS_SECTION_HEIGHT = 38
SECTION_SPACING = 8
SECTION_HORIZONTAL_MARGIN = 22


def format_money(value: float | Decimal | None) -> str:
    if value is None:
        return "--"
    amount = float(value)
    decimals = 4 if 0 < abs(amount) < 0.01 else 2
    return f"¥{amount:.{decimals}f}"


def format_token_axis(value: float) -> str:
    return compact_tokens(int(round(value)))


def format_money_axis(value: float) -> str:
    absolute = abs(value)
    if absolute >= 100:
        return f"¥{value:,.0f}"
    decimals = 4 if 0 < absolute < 0.01 else 2
    return f"¥{value:.{decimals}f}"


class MoneyAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [format_money_axis(value * scale) for value in values]


class DraggableHeader(QFrame):
    """Header drag surface used to move the entire frameless window."""

    pressed = Signal(QPoint)
    dragged = Signal(QPoint)
    released = Signal(QPoint)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed.emit(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.dragged.emit(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.released.emit(event.globalPosition().toPoint())
            event.accept()


class StatusDot(QWidget):
    """Small semantic status mark that follows live theme changes."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._role = "accent"
        self._explicit_color: QColor | None = None
        self.setFixedSize(12, 12)

    def set_role(self, role: str) -> None:
        self._role = role
        self._explicit_color = None
        self.update()

    def set_color(self, color: str) -> None:
        """Keep the old color API available for callers outside MainPanel."""
        self._explicit_color = QColor(color)
        self.update()

    def refresh_theme(self) -> None:
        self.update()

    def paintEvent(self, _event) -> None:
        tokens = current_theme()
        color = self._explicit_color or QColor(getattr(tokens, self._role, tokens.accent))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(2, 2, 8, 8)
        painter.end()


class MetricCard(QFrame):
    """One logical metric in the flat top summary area."""

    def __init__(self, title: str, icon_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricLabel")
        self.value = QLabel("--")
        self.value.setObjectName("metricValue")
        self.detail = QLabel()
        self.detail.setObjectName("metricDetail")
        self.footer = QLabel()
        self.footer.setObjectName("muted")
        # The third visual direction intentionally keeps the summary sparse.
        # Detail values remain populated for compatibility and accessibility.
        self.detail.hide()
        self.footer.hide()

        layout.addWidget(self.title_label)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)
        layout.addWidget(self.footer)
        layout.addStretch(1)

    def set_variant(self, variant: str) -> None:
        self.value.setObjectName("heroValue" if variant == "hero" else "metricValue")
        self.setProperty("variant", variant)

    def set_values(self, value: str, detail: str = "", footer: str = "") -> None:
        self.value.setText(value)
        self.detail.setText(detail)
        self.footer.setText(footer)
        self.detail.setToolTip(detail)
        self.footer.setToolTip(footer)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)


class TrendCard(QFrame):
    """Seven-day cost chart rendered as seven flat bars."""

    BAR_WIDTH = 0.36

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("trendSection")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 0, 2)
        layout.setSpacing(2)

        self.title = QLabel("近 7 天使用金额")
        self.title.setObjectName("sectionTitle")
        layout.addWidget(self.title)

        self.plot = pg.PlotWidget(
            axisItems={"left": MoneyAxis(orientation="left")},
        )
        self.plot.setStyleSheet("border: 0;")
        self.plot.setMinimumHeight(100)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(x=False, y=True, alpha=0.14)

        axis_font = QFont("Microsoft YaHei UI", 8)
        left_axis = self.plot.getAxis("left")
        bottom_axis = self.plot.getAxis("bottom")
        left_axis.setTickFont(axis_font)
        bottom_axis.setTickFont(axis_font)
        bottom_axis.setStyle(hideOverlappingLabels=False)
        left_axis.setStyle(hideOverlappingLabels=False)
        left_axis.setWidth(44)
        left_axis.enableAutoSIPrefix(False)
        bottom_axis.setHeight(22)
        self.plot.getViewBox().setLimits(xMin=-0.5, xMax=6.5, yMin=0)

        self._dates: list[date] = []
        self._values: list[float] = []
        self._series: pg.BarGraphItem | None = None
        self._hover_index: int | None = None
        self._mouse_proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_mouse_moved,
        )
        layout.addWidget(self.plot, 1)
        self._connect_theme_changes()
        self.set_rows([])

    def _connect_theme_changes(self) -> None:
        try:
            theme_controller().changed.connect(self._on_theme_changed)
        except RuntimeError:
            # Standalone component tests may construct the chart before an app-level
            # controller exists; production configures the theme before any window.
            pass

    def set_rows(self, rows: list[dict], today: date | None = None) -> None:
        current = today or date.today()
        by_date = {str(row.get("date")): row for row in rows}
        self._dates = [current - timedelta(days=offset) for offset in range(6, -1, -1)]
        self._values = [
            float(by_date.get(day.isoformat(), {}).get("cost_cny", 0) or 0)
            for day in self._dates
        ]
        self.plot.clear()

        tokens = current_theme()
        self._series = pg.BarGraphItem(
            x=list(range(7)),
            height=self._values,
            width=self.BAR_WIDTH,
            pen=pg.mkPen(tokens.accent),
            brush=pg.mkBrush(tokens.accent),
        )
        self.plot.addItem(self._series)

        self.plot.getAxis("bottom").setTicks(
            [[(index, day.strftime("%m/%d")) for index, day in enumerate(self._dates)]]
        )
        # Preserve half a day at each edge so all seven bars stay fully visible.
        self.plot.setXRange(-0.5, 6.5, padding=0)
        maximum = max(self._values, default=0.0)
        tick_max = max(0.01, maximum)
        range_max = tick_max * 1.08 if maximum > 0 else tick_max
        self.plot.setYRange(0, range_max, padding=0)
        self.plot.getAxis("left").setTicks(
            [[
                (tick_max * index / 3, format_money_axis(tick_max * index / 3))
                for index in range(4)
            ]]
        )
        self._hover_index = None
        self.refresh_theme()

    def refresh_theme(self) -> None:
        tokens = current_theme()
        # The selected layout is one continuous surface; the chart must not
        # introduce a nested rectangular card behind the bars.
        self.plot.setBackground(tokens.window)
        left_axis = self.plot.getAxis("left")
        bottom_axis = self.plot.getAxis("bottom")
        left_axis.setTextPen(pg.mkPen(tokens.subtext))
        bottom_axis.setTextPen(pg.mkPen(tokens.subtext))
        axis_color = QColor(tokens.border)
        axis_color.setAlpha(96)
        left_axis.setPen(pg.mkPen(axis_color))
        bottom_axis.setPen(pg.mkPen(axis_color))
        if self._series is not None:
            if self._hover_index is None:
                self._series.setOpts(
                    pens=None,
                    brushes=None,
                    pen=pg.mkPen(tokens.accent),
                    brush=pg.mkBrush(tokens.accent),
                )
            else:
                self._series.setOpts(
                    pens=[
                        pg.mkPen(tokens.accent_hover if index == self._hover_index else tokens.accent)
                        for index in range(len(self._values))
                    ],
                    brushes=[
                        pg.mkBrush(tokens.accent_hover if index == self._hover_index else tokens.accent)
                        for index in range(len(self._values))
                    ],
                )

    def _on_theme_changed(self, _mode: str, _resolved: str) -> None:
        self.refresh_theme()

    def _on_mouse_moved(self, event) -> None:
        scene_pos = event[0]
        if not self.plot.sceneBoundingRect().contains(scene_pos):
            self._hide_hover()
            return
        point = self.plot.getViewBox().mapSceneToView(scene_pos)
        index = int(round(point.x()))
        if not 0 <= index < len(self._values) or abs(point.x() - index) > self.BAR_WIDTH / 2:
            self._hide_hover()
            return

        self._hover_index = index
        self.refresh_theme()
        local = self.plot.mapFromScene(scene_pos)
        QToolTip.showText(
            self.plot.mapToGlobal(local),
            self.tooltip_text(index),
            self.plot,
        )

    def _hide_hover(self) -> None:
        had_hover = self._hover_index is not None
        self._hover_index = None
        if had_hover:
            self.refresh_theme()
        QToolTip.hideText()

    def tooltip_text(self, index: int) -> str:
        return (
            f"{self._dates[index].isoformat()}\n"
            f"使用金额：{format_money(self._values[index])}"
        )


class StatisticsCard(QFrame):
    """Five equal columns matching the selected third-direction mockup."""

    LABELS = (
        "本月使用金额",
        "历史使用总金额",
        "本月 Token",
        "近 7 天使用金额",
        "近 7 天 Token",
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("statisticsSection")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SECTION_HORIZONTAL_MARGIN, 0, SECTION_HORIZONTAL_MARGIN, 2)
        layout.setSpacing(3)

        line = QFrame()
        line.setObjectName("divider")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        layout.addWidget(line)

        title = QLabel("使用统计")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        columns = QHBoxLayout()
        columns.setContentsMargins(10, 0, 10, 0)
        columns.setSpacing(0)
        self._values: list[QLabel] = []
        self._names: list[QLabel] = []
        for index, label in enumerate(self.LABELS):
            column = QWidget()
            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.setSpacing(1)
            name = QLabel(label)
            name.setObjectName("statLabel")
            name.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            if label == "历史使用总金额":
                # The provider has no lifetime total; this value is the local cache scope.
                name.setToolTip("按本机已缓存账单累计，未同步的早期账单不计入")
            value = QLabel("--")
            value.setObjectName("statValue")
            value.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            column_layout.addWidget(name)
            column_layout.addWidget(value)
            columns.addWidget(column, 1)
            self._names.append(name)
            self._values.append(value)
            if index < len(self.LABELS) - 1:
                separator = QFrame()
                separator.setObjectName("divider")
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFixedSize(1, 46)
                columns.addWidget(separator, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(columns, 1)

    def set_data(self, data: TokenData) -> None:
        recent_rows = {str(row.get("date")): row for row in data.daily_usage}
        recent_dates = [date.today() - timedelta(days=offset) for offset in range(6, -1, -1)]
        recent_cost = sum(
            float(recent_rows.get(day.isoformat(), {}).get("cost_cny", 0) or 0)
            for day in recent_dates
        )
        recent_tokens = sum(
            int(recent_rows.get(day.isoformat(), {}).get("tokens", 0) or 0)
            for day in recent_dates
        )
        has_daily_data = data.today_tokens is not None
        values = (
            format_money(data.monthly_cost_cny),
            format_money(data.total_cost_cny),
            compact_tokens(data.monthly_usage_tokens) if data.monthly_usage_tokens is not None else "--",
            format_money(recent_cost) if has_daily_data else "--",
            compact_tokens(recent_tokens) if has_daily_data else "--",
        )
        for label, value in zip(self._values, values):
            label.setText(value)


class MainPanel(QFrame):
    settings_requested = Signal()
    refresh_requested = Signal()
    close_requested = Signal()
    theme_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("panelFrame")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(PANEL_MIN_WIDTH, PANEL_HEIGHT)
        self.setMaximumSize(PANEL_MAX_WIDTH, PANEL_HEIGHT)
        self._theme_mode = "dark"
        self._resolved_theme = current_theme().name
        self._theme_feedback_message = ""
        self._button_specs: list[tuple[QToolButton, str, QStyle.StandardPixmap, str]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.header = DraggableHeader()
        self.header.setObjectName("panelHeader")
        self.header.setFixedHeight(HEADER_HEIGHT)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 7, 12, 7)
        header_layout.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(app_icon(28).pixmap(28, 28))
        logo.setFixedSize(28, 28)
        self._title_label = QLabel("TokenSpider")
        self._title_label.setObjectName("panelTitle")
        provider_id = str(config_manager.get("ACTIVE_PROVIDER", "deepseek"))
        provider_name = {"deepseek": "DeepSeek", "mimo": "小米 MiMo"}.get(
            provider_id, provider_id
        )
        self._provider_label = QLabel(f" · {provider_name}" if provider_name else "")
        self._provider_label.setObjectName("panelSubtitle")
        header_layout.addWidget(logo)
        header_layout.addWidget(self._title_label)
        header_layout.addWidget(self._provider_label)
        header_layout.addStretch(1)

        self.theme_segment = QFrame()
        self.theme_segment.setObjectName("themeSegment")
        self.theme_segment.setFixedHeight(30)
        theme_layout = QHBoxLayout(self.theme_segment)
        theme_layout.setContentsMargins(2, 2, 2, 2)
        theme_layout.setSpacing(0)
        self._theme_group = QButtonGroup(self)
        self._theme_group.setExclusive(True)
        self.light_theme_button = self._theme_button("sun", "light", "切换到浅色主题")
        self.dark_theme_button = self._theme_button("moon", "dark", "切换到深色主题")
        for button in (self.light_theme_button, self.dark_theme_button):
            self._theme_group.addButton(button)
            theme_layout.addWidget(button)
        header_layout.addWidget(self.theme_segment)

        header_divider = QFrame()
        header_divider.setObjectName("divider")
        header_divider.setFrameShape(QFrame.Shape.VLine)
        header_divider.setFixedSize(1, 22)
        header_layout.addWidget(header_divider)

        self.settings_button = self._tool_button(
            "settings", QStyle.StandardPixmap.SP_FileDialogDetailedView, "设置"
        )
        self.refresh_button = self._tool_button(
            "refresh", QStyle.StandardPixmap.SP_BrowserReload, "刷新"
        )
        self.close_button = self._tool_button(
            "close", QStyle.StandardPixmap.SP_TitleBarCloseButton, "收起", role="close"
        )
        self.settings_button.clicked.connect(self.settings_requested)
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.close_button.clicked.connect(self.close_requested)
        for button in (self.settings_button, self.refresh_button, self.close_button):
            header_layout.addWidget(button)
        root.addWidget(self.header)

        body = QWidget()
        body.setObjectName("panelRoot")
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 7, 0, 7)
        content.setSpacing(SECTION_SPACING)

        self.top_section = QFrame()
        self.top_section.setObjectName("topSection")
        self.top_section.setFixedHeight(TOP_SECTION_HEIGHT)
        top_layout = QHBoxLayout(self.top_section)
        top_layout.setContentsMargins(SECTION_HORIZONTAL_MARGIN, 5, SECTION_HORIZONTAL_MARGIN, 5)
        top_layout.setSpacing(16)

        self.metrics_container = QWidget()
        self.metrics_container.setObjectName("metricsContainer")
        self.metrics_container.setMinimumWidth(205)
        metrics_layout = QVBoxLayout(self.metrics_container)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(3)

        self.today_card = MetricCard("今日使用金额", "usage")
        self.today_card.set_variant("hero")
        self.balance_card = MetricCard("账户余额", "balance")
        self.balance_card.set_variant("compact")
        self.month_card = MetricCard("本月累计", "month")
        self.month_card.set_variant("compact")
        metrics_layout.addWidget(self.today_card, 3)

        compact_metrics = QHBoxLayout()
        compact_metrics.setContentsMargins(0, 0, 0, 0)
        compact_metrics.setSpacing(14)
        compact_metrics.addWidget(self.balance_card, 1)
        metric_divider = QFrame()
        metric_divider.setObjectName("divider")
        metric_divider.setFrameShape(QFrame.Shape.VLine)
        metric_divider.setFixedWidth(1)
        compact_metrics.addWidget(metric_divider)
        compact_metrics.addWidget(self.month_card, 1)
        metrics_layout.addLayout(compact_metrics, 2)
        top_layout.addWidget(self.metrics_container, 5)

        main_divider = QFrame()
        main_divider.setObjectName("divider")
        main_divider.setFrameShape(QFrame.Shape.VLine)
        main_divider.setFixedWidth(1)
        top_layout.addWidget(main_divider)

        self.trend = TrendCard()
        self.trend.setMinimumWidth(300)
        top_layout.addWidget(self.trend, 11)
        content.addWidget(self.top_section)

        self.activity_card = QFrame()
        self.activity_card.setObjectName("activitySection")
        self.activity_card.setFixedHeight(ACTIVITY_SECTION_HEIGHT)
        activity_layout = QVBoxLayout(self.activity_card)
        activity_layout.setContentsMargins(SECTION_HORIZONTAL_MARGIN, 0, SECTION_HORIZONTAL_MARGIN, 3)
        activity_layout.setSpacing(4)

        activity_divider = QFrame()
        activity_divider.setObjectName("divider")
        activity_divider.setFrameShape(QFrame.Shape.HLine)
        activity_divider.setFixedHeight(1)
        activity_layout.addWidget(activity_divider)

        activity_header = QHBoxLayout()
        activity_header.setContentsMargins(0, 0, 0, 0)
        activity_header.setSpacing(8)
        activity_title = QLabel("Token 活动")
        activity_title.setObjectName("sectionTitle")
        self.activity_summary = QLabel("暂无 Token 活动")
        self.activity_summary.setObjectName("muted")
        activity_header.addWidget(activity_title)
        activity_header.addStretch(1)
        activity_header.addWidget(self.activity_summary)
        activity_layout.addLayout(activity_header)

        self.activity_scroll = QScrollArea()
        self.activity_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.activity_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Do not style the viewport locally: Qt cascades such rules into the
        # heatmap tooltip. The application palette supplies the themed surface.
        self.activity = TokenActivityHeatmap()
        self._fit_activity_heatmap()
        self.activity_scroll.setWidget(self.activity)
        self.activity_scroll.setFixedHeight(self.activity.height())
        activity_layout.addWidget(self.activity_scroll)
        content.addWidget(self.activity_card)
        self.middle_section = self.activity_card

        self.statistics = StatisticsCard()
        self.statistics.setFixedHeight(STATISTICS_SECTION_HEIGHT)
        content.addWidget(self.statistics)
        self.bottom_section = self.statistics

        footer_widget = QWidget()
        footer_widget.setObjectName("statusBar")
        footer_widget.setFixedHeight(STATUS_SECTION_HEIGHT)
        footer = QHBoxLayout(footer_widget)
        footer.setContentsMargins(SECTION_HORIZONTAL_MARGIN, 0, SECTION_HORIZONTAL_MARGIN, 0)
        footer.setSpacing(8)
        self.status_dot = StatusDot()
        self.status_text = QLabel("等待连接")
        self.status_text.setObjectName("statusText")
        self.updated_text = QLabel()
        self.updated_text.setObjectName("statusText")
        footer.addWidget(self.status_dot)
        footer.addWidget(self.status_text)
        footer.addStretch(1)
        footer.addWidget(self.updated_text)
        content.addWidget(footer_widget)
        root.addWidget(body, 1)

        configured_mode = str(config_manager.get("UI_THEME", "dark"))
        self.set_theme_mode(configured_mode, current_theme().name)
        try:
            theme_controller().changed.connect(self._on_theme_changed)
        except RuntimeError:
            # Preserve standalone construction compatibility for callers that do
            # not own application startup; the desktop app configures this first.
            pass
        self._refresh_icons()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "activity"):
            self._fit_activity_heatmap()

    def _fit_activity_heatmap(self) -> None:
        # At the supported 640 px minimum, the full 53-week calendar must stay
        # visible without a scrollbar stealing vertical room from the last row.
        compact = self.width() < 775
        self.activity.CELL = 9 if compact else 11
        self.activity.MIN_HORIZONTAL_GAP = 1 if compact else 2
        required_width = (
            self.activity.LEFT
            + self.activity.period.week_count
            * (self.activity.CELL + self.activity.MIN_HORIZONTAL_GAP)
            + 12
        )
        self.activity.setMinimumWidth(required_width)
        self.activity.update()

    def _theme_button(self, icon_name: str, mode: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName("themeButton")
        button.setProperty("themeValue", mode)
        button.setCheckable(True)
        button.setAutoRaise(True)
        button.setFixedSize(24, 24)
        button.setIconSize(QSize(14, 14))
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.clicked.connect(lambda _checked=False, value=mode: self._request_theme(value))
        button._theme_icon_name = icon_name
        return button

    def _tool_button(
        self,
        name: str,
        standard: QStyle.StandardPixmap,
        tooltip: str,
        role: str = "",
    ) -> QToolButton:
        button = QToolButton()
        button.setIconSize(QSize(18, 18))
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setObjectName("panelToolButton")
        if role:
            button.setProperty("role", role)
        button.setFixedSize(32, 32)
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._button_specs.append((button, name, standard, role))
        return button

    def _request_theme(self, mode: str) -> None:
        self.set_theme_mode(mode, mode)
        self.theme_requested.emit(mode)

    def set_theme_mode(self, mode: str, resolved: str | None = None) -> None:
        """Synchronize the header selector with the configured and resolved mode."""
        normalized_mode = mode if mode in {"system", "light", "dark"} else "dark"
        normalized_resolved = resolved if resolved in {"light", "dark"} else current_theme().name
        if normalized_resolved not in {"light", "dark"}:
            normalized_resolved = "dark"
        self._theme_mode = normalized_mode
        self._resolved_theme = normalized_resolved
        self._theme_feedback_message = ""

        is_light = normalized_resolved == "light"
        self.light_theme_button.setChecked(is_light)
        self.dark_theme_button.setChecked(not is_light)
        for button, selected in (
            (self.light_theme_button, is_light),
            (self.dark_theme_button, not is_light),
        ):
            button.setProperty("selected", selected)
            button.style().unpolish(button)
            button.style().polish(button)

        if normalized_mode == "system":
            theme_name = "浅色" if is_light else "深色"
            segment_tip = f"跟随系统（当前为{theme_name}主题）"
            self.light_theme_button.setToolTip(f"{segment_tip}；点击固定为浅色主题")
            self.dark_theme_button.setToolTip(f"{segment_tip}；点击固定为深色主题")
        else:
            segment_tip = "浅色主题" if is_light else "深色主题"
            self.light_theme_button.setToolTip("浅色主题（当前）" if is_light else "切换到浅色主题")
            self.dark_theme_button.setToolTip("深色主题（当前）" if not is_light else "切换到深色主题")
        self.theme_segment.setToolTip(segment_tip)
        self.theme_segment.setAccessibleDescription(segment_tip)

    def set_theme_feedback(self, message: str, tone: str = "danger") -> None:
        """Expose persistence feedback without replacing provider connection status."""
        self._theme_feedback_message = message.strip()
        self.theme_segment.setProperty("feedbackTone", tone)
        if self._theme_feedback_message:
            self.theme_segment.setToolTip(self._theme_feedback_message)
            self.light_theme_button.setToolTip(self._theme_feedback_message)
            self.dark_theme_button.setToolTip(self._theme_feedback_message)

    def _on_theme_changed(self, mode: str, resolved: str) -> None:
        self.set_theme_mode(mode, resolved)
        self.status_dot.refresh_theme()
        self._refresh_icons()
        self.update()

    def _refresh_icons(self) -> None:
        tokens = current_theme()
        for button, name, standard, role in self._button_specs:
            active_color = tokens.danger if role == "close" else tokens.accent_hover
            icon = fluent_icon(name, active_color=active_color)
            button.setIcon(icon if not icon.isNull() else self.style().standardIcon(standard))
        for button in (self.light_theme_button, self.dark_theme_button):
            icon = fluent_icon(button._theme_icon_name, size=14, active_color=tokens.text)
            button.setIcon(icon)

    def set_refreshing(self, refreshing: bool) -> None:
        self.refresh_button.setEnabled(not refreshing)
        self.refresh_button.setToolTip("刷新中" if refreshing else "刷新")

    def update_data(self, data: TokenData, loading: bool = False) -> None:
        money = lambda value: "--" if loading else format_money(value)
        tokens = lambda value: "--" if loading or value is None else compact_tokens(int(value))
        if data.per_provider:
            provider_name = data.per_provider[0].provider_name
            self._provider_label.setText(f" · {provider_name}")

        self.today_card.set_title("今日使用金额")
        self.balance_card.set_title("账户余额")
        self.month_card.set_title("本月累计")
        self.today_card.set_values(money(data.today_cost_cny), tokens(data.today_tokens), "")
        self.balance_card.set_values(
            money(data.balance_cny),
            f"约 {tokens(data.balance_tokens)}" if data.balance_tokens else "账户可用余额",
            "",
        )
        self.month_card.set_values(
            money(data.monthly_cost_cny),
            tokens(data.monthly_usage_tokens),
            "",
        )

        self.activity.set_activity(data.daily_usage)
        source_days = [day for day in self.activity.days if day.has_source_data]
        total = sum(day.token_count for day in source_days)
        if not source_days:
            summary = "暂无 Token 活动"
        else:
            first = min(day.date for day in source_days)
            if first > self.activity.period.start:
                summary = f"数据始于 {first.isoformat()} · 共 {compact_tokens(total)}"
            else:
                summary = f"过去 12 个月共使用 {compact_tokens(total)}"
        self.activity_summary.setText(summary)

        self.trend.set_rows(data.daily_usage)
        self.statistics.set_data(data)
        status, _color = self.status_summary(data, loading)
        self.status_text.setText(status)
        self.status_dot.set_role(self.status_role(data, loading))
        self.updated_text.setText(self.relative_update_time(data))

    @staticmethod
    def status_role(data: TokenData, loading: bool = False) -> str:
        if loading:
            return "accent"
        codes = {error.code for error in data.errors}
        if "NOT_CONFIGURED" in codes or data.status == "not_configured":
            return "warning"
        if codes & {"AUTH_EXPIRED", "NETWORK_TIMEOUT", "NETWORK_ERROR", "SERVER_ERROR"}:
            return "danger"
        if data.status == "partial":
            return "warning"
        if data.status == "error":
            return "danger"
        if data.status == "ok":
            return "success"
        return "accent"

    @staticmethod
    def status_summary(data: TokenData, loading: bool = False) -> tuple[str, str]:
        theme = current_theme()
        if loading:
            return "正在更新", theme.accent
        codes = {error.code for error in data.errors}
        if "NOT_CONFIGURED" in codes:
            return "尚未配置 Token/Cookie，请前往设置", theme.warning
        if "AUTH_EXPIRED" in codes:
            return "认证信息已失效，请重新配置", theme.danger
        if codes & {"NETWORK_TIMEOUT", "NETWORK_ERROR"}:
            return "网络连接失败", theme.danger
        if "SERVER_ERROR" in codes:
            return "API 服务异常", theme.danger
        if data.status == "not_configured":
            return "尚未配置凭据，请前往设置", theme.warning
        if data.status == "ok" and data.today_tokens is None:
            return "连接正常，平台未提供按日明细", theme.success
        if data.status == "ok" and not any(day.get("tokens", 0) for day in data.daily_usage):
            return "连接正常，暂无 Token 活动", theme.success
        return {
            "ok": ("连接正常", theme.success),
            "partial": ("部分数据异常，显示可用数据", theme.warning),
            "error": ("连接异常", theme.danger),
        }.get(data.status, ("等待连接", theme.accent))

    @staticmethod
    def relative_update_time(data: TokenData) -> str:
        if not data.last_success_at:
            return "等待首次更新"
        seconds = max(0, int((datetime.now() - data.last_success_at).total_seconds()))
        if seconds < 60:
            return "数据更新于刚刚"
        minutes = seconds // 60
        if minutes < 60:
            return f"数据更新于 {minutes} 分钟前"
        return f"数据更新于 {minutes // 60} 小时前"
