"""TokenSpider — real-time LLM API usage monitor (floating desktop widget)."""

from ui.widget import FloatingWidget
from ui.tray import SystemTray


class App:
    def __init__(self):
        self.widget = FloatingWidget(tray_icon=None)
        self.tray = SystemTray(self)
        self.widget.tray = self.tray

    def run(self):
        self.tray.run()
        self.widget.attributes("-alpha", 0.65)
        self.widget.mainloop()


if __name__ == "__main__":
    App().run()
