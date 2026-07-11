"""Qt system tray integration."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app_identity import APP_DISPLAY_NAME
from ui.qt_theme import app_icon, theme_controller


class SystemTray(QSystemTrayIcon):
    def __init__(self, app):
        super().__init__(app_icon(64), app.widget)
        self.app = app
        self.setToolTip(f"{APP_DISPLAY_NAME} - LLM 用量监控")

        menu = QMenu()
        visible = QAction("显示/隐藏", menu)
        visible.triggered.connect(app.widget.set_visible_from_tray)
        refresh = QAction("刷新", menu)
        refresh.triggered.connect(app.widget.refresh)
        settings = QAction("设置", menu)
        settings.triggered.connect(app.widget.open_settings)
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quit_app)
        menu.addActions((visible, refresh, settings))
        menu.addSeparator()
        menu.addAction(quit_action)
        self._menu = menu
        self.setContextMenu(menu)
        theme_controller().changed.connect(self._refresh_menu_theme)
        self.activated.connect(self._activated)
        self.messageClicked.connect(app.widget.handle_auth_expired_notification_click)

    def _refresh_menu_theme(self, _mode: str, _resolved: str) -> None:
        application = QApplication.instance()
        if application is not None:
            self._menu.setPalette(application.palette())
        self._menu.style().unpolish(self._menu)
        self._menu.style().polish(self._menu)
        self._menu.update()

    def _activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.app.widget.set_visible_from_tray()

    def quit_app(self) -> None:
        self.hide()
        self.app.widget.close()

    def run(self) -> None:
        self.show()

    def stop(self) -> None:
        self.hide()
