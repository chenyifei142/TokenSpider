"""System tray icon using pystray."""

import threading
from PIL import Image, ImageDraw
import pystray


def _create_icon_image(size=64):
    """Draw a simple spider-web-themed icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r = size // 2 - 4
    # Outer circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 26, 46, 255))
    # Accent dot
    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(77, 124, 255, 255))
    # Web lines
    import math
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        ex = cx + int((r - 2) * math.cos(rad))
        ey = cy + int((r - 2) * math.sin(rad))
        draw.line([cx, cy, ex, ey], fill=(77, 124, 255, 180), width=1)
    return img


class SystemTray:
    def __init__(self, app):
        self.app = app
        self.icon = pystray.Icon(
            "TokenSpider",
            _create_icon_image(),
            "TokenSpider - LLM Usage Monitor",
            menu=pystray.Menu(
                pystray.MenuItem("显示/隐藏", self.toggle_visible, default=True),
                pystray.MenuItem("刷新", lambda: self.app.widget.refresh()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self.quit_app),
            ),
        )

    def toggle_visible(self):
        w = self.app.widget
        if w.winfo_viewable():
            w.withdraw()
        else:
            w.deiconify()
            w.lift()

    def quit_app(self):
        self.icon.stop()
        self.app.widget.destroy()

    def run(self):
        threading.Thread(target=self.icon.run, daemon=True).start()
