"""Floating widget -- auto-scaling UI with budget gauge, model details."""

import tkinter as tk
import threading

from config import REFRESH_INTERVAL
from data.store import TokenData

# ── palette ──────────────────────────────────────────────────────
C_MASK     = "#010101"
C_CARD     = "#22223a"
C_GLOW     = "#4a4a6a"
C_ACCENT   = "#7b6cf6"
C_ACCENT2  = "#00d4aa"
C_TEXT     = "#f0f0f5"
C_SUBTEXT  = "#a0a0c0"
C_BORDER   = "#35355a"
C_ROW_BG   = "#1c1c32"
C_TIME     = "#8888b0"
C_GREEN    = "#00d4aa"
C_YELLOW   = "#f0c040"
C_RED      = "#f05050"
C_BAR_BG   = "#2e2e4a"

# ── base font sizes (scaled dynamically) ─────────────────────────
# format: (family, size, *styles)
BF_LABEL  = ("Segoe UI", 9)
BF_VALUE  = ("Consolas", 11, "bold")
BF_COST   = ("Consolas", 10, "bold")
BF_TIME   = ("Consolas", 8)
BF_TITLE  = ("Segoe UI", 14, "bold")
BF_SECTION = ("Consolas", 10, "bold")
BF_LABEL_L = ("Segoe UI", 11)
BF_VALUE_L = ("Consolas", 13, "bold")
BF_TIME_L  = ("Consolas", 9)
BF_MODEL   = ("Consolas", 9, "bold")
BF_MODEL_V = ("Consolas", 9)
BF_PCT     = ("Segoe UI", 11, "bold")

# ── default dimensions (scale = 1.0) ─────────────────────────────
DEF_COMPACT_W = 290
DEF_COMPACT_H = 120
DEF_EXPAND_W  = 390
DEF_EXPAND_H  = 710
R_CARD_SM = 22
R_CARD_LG = 24
R_ROW     = 10
MIN_W, MIN_H = 200, 70


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = (
        x1 + r, y1,  x2 - r, y1,  x2, y1,  x2, y1 + r,
        x2, y2 - r,  x2, y2,  x2 - r, y2,  x1 + r, y2,
        x1, y2,  x1, y2 - r,  x1, y1 + r,  x1, y1,
    )
    return c.create_polygon(pts, smooth=True, **kw)


class FloatingWidget(tk.Tk):
    EDGE_WIDTH = 8

    def __init__(self, tray_icon):
        super().__init__()
        self.tray = tray_icon
        self._expanded = False
        self._data = TokenData()
        self._drag_started = False
        self._drag_x = 0
        self._drag_y = 0
        self._hover = False
        # Resize state
        self._resize_edge = None
        self._resize_orig_x = 0
        self._resize_orig_y = 0
        self._resize_orig_w = 0
        self._resize_orig_h = 0
        self._resize_orig_win_x = 0
        self._resize_orig_win_y = 0
        self._win_w = DEF_COMPACT_W
        self._win_h = DEF_COMPACT_H
        self._scale = 1.0

        self._setup_window()
        self._build_compact()
        self._build_expanded()
        self._show_compact()
        self._start_refresh()

    # ================================================================
    #  Font scaling
    # ================================================================

    def _update_scale(self):
        """Recalc scale factor based on current vs default dimensions."""
        if self._expanded:
            dw, dh = DEF_EXPAND_W, DEF_EXPAND_H
        else:
            dw, dh = DEF_COMPACT_W, DEF_COMPACT_H
        sx = self._win_w / dw if dw else 1
        sy = self._win_h / dh if dh else 1
        self._scale = max(0.45, min(2.0, min(sx, sy)))

    def _s(self, base_font):
        """Return a scaled font tuple from a base font spec."""
        family, size = base_font[0], base_font[1]
        extras = base_font[2:]
        return (family, max(5, int(size * self._scale)), *extras)

    # ================================================================
    #  Helpers
    # ================================================================

    @staticmethod
    def _fmt_num(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    def _remaining_pct(self) -> float:
        d = self._data
        total = d.balance_cny + d.monthly_cost_cny
        if total <= 0:
            return 100.0
        return d.balance_cny / total * 100

    @staticmethod
    def _bar_color(pct: float) -> str:
        if pct < 10:
            return C_RED
        if pct < 20:
            return C_YELLOW
        return C_GREEN

    def _draw_bar(self, c, x1, y1, x2, y2, pct):
        w  = x2 - x1
        bw = y2 - y1
        r  = bw // 2
        fill_w = max(0, min(w, int(w * pct / 100)))
        _round_rect(c, x1, y1, x2, y2, r, fill=C_BAR_BG, outline="")
        if fill_w > r * 2:
            _round_rect(c, x1, y1, x1 + fill_w, y2, r,
                        fill=self._bar_color(pct), outline="")
        elif fill_w > 0:
            c.create_oval(x1, y1 + 1, x1 + fill_w * 2, y2 - 1,
                          fill=self._bar_color(pct), outline="")

    # ================================================================
    #  Window
    # ================================================================

    def _setup_window(self):
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        x = self.winfo_screenwidth() - DEF_COMPACT_W - 24
        self.geometry(f"{DEF_COMPACT_W}x{DEF_COMPACT_H}+{x}+40")
        self.configure(bg=C_MASK)
        self.attributes("-alpha", 0.94)
        try:
            self.attributes("-transparentcolor", C_MASK)
        except Exception:
            pass
        self.bind("<Button-1>",        self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<Motion>",          self._on_motion)
        self.bind("<Button-3>",        self._on_right_click)
        self.bind("<Enter>",           lambda e: self._on_hover(True))
        self.bind("<Leave>",           lambda e: self._on_hover(False))

    # ================================================================
    #  Compact card
    # ================================================================

    def _build_compact(self):
        c = tk.Canvas(self, bg=C_MASK, highlightthickness=0)
        self._compact_canvas = c
        c.pack(fill="both", expand=True)

    def _draw_compact(self):
        c = self._compact_canvas
        c.delete("all")
        w, h = self._win_w, self._win_h
        self._update_scale()
        s = self._s
        c.configure(width=w, height=h)

        # Glow + card bg
        _round_rect(c, 0, 0, w, h, R_CARD_SM,
                    fill="", outline=C_GLOW, width=3)
        _round_rect(c, 2, 2, w - 2, h - 2, R_CARD_SM - 2,
                    fill=C_CARD, outline=C_BORDER, width=1)

        pct = self._remaining_pct()
        d = self._data

        col_label = int(w * 0.10)
        col_cost  = w - int(w * 0.10)

        # 3 data rows: Wallet, Today Cost, Week Cost
        data_rows = [
            ("Wallet",     f"Y {d.balance_cny:.4f}",    C_ACCENT2, BF_COST),
            ("Today Cost", f"Y {d.today_cost_cny:.4f}",  C_ACCENT2, BF_COST),
            ("Week  Cost", f"Y {d.weekly_cost_cny:.4f}", C_ACCENT2, BF_COST),
        ]
        row_step = int(h * 0.17)
        row_start = int(h * 0.09)

        for i, (label, val_str, color, font) in enumerate(data_rows):
            y = row_start + i * row_step + row_step // 2
            c.create_text(col_label, y, text=label,
                          fill=C_SUBTEXT, font=s(BF_LABEL), anchor="w")
            c.create_text(col_cost, y, text=val_str,
                          fill=color, font=s(font), anchor="e")

        # Bar section
        bar_y = row_start + len(data_rows) * row_step + int(h * 0.12)
        bar_h = max(5, int(h * 0.045))
        bar_left = int(w * 0.10)

        c.create_text(bar_left, bar_y - int(h * 0.05), text="budget",
                      fill=C_TIME, font=s(("Segoe UI", 6)), anchor="w")

        self._draw_bar(c, bar_left, bar_y, w - bar_left, bar_y + bar_h, pct)
        c.create_text(w - bar_left, bar_y - int(h * 0.05),
                      text=f"{pct:.0f}%", fill=self._bar_color(pct),
                      font=s(("Consolas", 7, "bold")), anchor="e")

        c.create_text(w // 2, h - int(h * 0.06),
                      text=f"updated  {d.last_updated}",
                      fill=C_TIME, font=s(("Consolas", 7)))

    def _show_compact(self):
        if hasattr(self, '_expanded_canvas') and self._expanded_canvas.winfo_ismapped():
            self._expanded_canvas.pack_forget()
        self._compact_canvas.pack(fill="both", expand=True)
        self.geometry(f"{self._win_w}x{self._win_h}")

    # ================================================================
    #  Expanded panel
    # ================================================================

    def _build_expanded(self):
        c = tk.Canvas(self, bg=C_MASK, highlightthickness=0)
        self._expanded_canvas = c
        c.pack()

    def _redraw_expanded(self):
        c = self._expanded_canvas
        c.delete("all")
        w, h = self._win_w, self._win_h
        self._update_scale()
        s = self._s
        c.configure(width=w, height=h)

        # Glow + card bg
        _round_rect(c, 0, 0, w, h, R_CARD_LG,
                    fill="", outline=C_GLOW, width=3)
        _round_rect(c, 2, 2, w - 2, h - 2, R_CARD_LG - 2,
                    fill=C_CARD, outline=C_BORDER, width=1)

        # ── Title ──
        c.create_text(w // 2, int(h * 0.042), text="TokenSpider",
                      fill=C_ACCENT, font=s(BF_TITLE))
        sep1_y = int(h * 0.074)
        c.create_line(24, sep1_y, w - 24, sep1_y, fill=C_BORDER, width=1)

        # ── Budget gauge ──
        gauge_y = int(h * 0.096)
        c.create_text(28, gauge_y, text="BUDGET", fill=C_ACCENT,
                      font=s(BF_SECTION), anchor="w")

        bar_x1, bar_x2 = 28, w - 28
        bar_y1 = gauge_y + int(h * 0.020)
        bar_y2 = gauge_y + int(h * 0.048)
        self._gauge_bar_coords = (bar_x1, bar_y1, bar_x2, bar_y2)

        self._gauge_pct_id = c.create_text(
            bar_x2, bar_y1 - int(h * 0.024), text="",
            font=s(BF_PCT), anchor="e")
        self._gauge_sub_id = c.create_text(
            bar_x1, bar_y2 + int(h * 0.024), text="",
            fill=C_SUBTEXT, font=s(("Segoe UI", 8)), anchor="w")

        # ── Summary rows ──
        sum_y = gauge_y + int(h * 0.090)
        c.create_line(24, sum_y, w - 24, sum_y, fill=C_BORDER, width=1)
        c.create_text(28, sum_y + int(h * 0.024), text="SUMMARY",
                      fill=C_ACCENT, font=s(BF_SECTION), anchor="w")

        self._stat_rows = []
        labels = [
            "Wallet", "Avail Tokens",
            "Today  Cost", "Today  Tokens",
            "Week   Cost", "Week   Tokens",
            "Month Cost",  "Month Tokens",
        ]
        keys = [
            "balance_cny", "balance_tokens",
            "today_cost_cny", "today_tokens",
            "weekly_cost_cny", "weekly_tokens",
            "monthly_cost_cny", "monthly_usage_tokens",
        ]
        fmts = [
            lambda v: f"Y {v:.4f}", lambda v: f"{v:,}",
            lambda v: f"Y {v:.4f}", lambda v: f"{v:,}",
            lambda v: f"Y {v:.4f}", lambda v: f"{v:,}",
            lambda v: f"Y {v:.4f}", lambda v: f"{v:,}",
        ]
        row_step = int(h * 0.044)
        row_h    = int(h * 0.036)
        row_start = sum_y + int(h * 0.062)

        for i in range(8):
            y = row_start + i * row_step
            _round_rect(c, 20, y - 4, w - 20, y + row_h - 4, R_ROW,
                        fill=C_ROW_BG, outline="")
            c.create_text(34, y + (row_h - 4) // 2, text=labels[i],
                          fill=C_SUBTEXT, font=s(BF_LABEL_L), anchor="w")
            vid = c.create_text(w - 34, y + (row_h - 4) // 2, text="--",
                                fill=C_TEXT, font=s(BF_VALUE_L), anchor="e")
            self._stat_rows.append((keys[i], fmts[i], vid))

        # ── Model breakdown ──
        model_y = row_start + 8 * row_step + int(h * 0.022)
        c.create_line(24, model_y, w - 24, model_y, fill=C_BORDER, width=1)
        c.create_text(28, model_y + int(h * 0.024), text="MODELS",
                      fill=C_ACCENT, font=s(BF_SECTION), anchor="w")

        self._model_rows = []
        model_names = [
            ("deepseek-v4-pro",   C_ACCENT),
            ("deepseek-v4-flash", C_ACCENT2),
            ("deepseek-chat",     C_SUBTEXT),
        ]
        m_step   = int(h * 0.080)
        m_row_h  = int(h * 0.070)
        m_start  = model_y + int(h * 0.054)

        for i, (name, color) in enumerate(model_names):
            ry = m_start + i * m_step
            _round_rect(c, 20, ry - 2, w - 20, ry + m_row_h - 2, R_ROW,
                        fill=C_ROW_BG, outline="")
            c.create_text(32, ry + int(m_row_h * 0.22), text=name,
                          fill=color, font=s(BF_MODEL), anchor="w")
            tk_lbl = c.create_text(32, ry + int(m_row_h * 0.62),
                                   text="tk  --", fill=C_SUBTEXT,
                                   font=s(BF_MODEL_V), anchor="w")
            co_lbl = c.create_text(w - 32, ry + int(m_row_h * 0.62),
                                   text="Y  --", fill=C_ACCENT2,
                                   font=s(BF_MODEL_V), anchor="e")
            self._model_rows.append((name, color, tk_lbl, co_lbl))

        # ── Bottom bar ──
        bot_y = h - int(h * 0.054)
        c.create_line(24, bot_y - 4, w - 24, bot_y - 4,
                      fill=C_BORDER, width=1)
        self._updated_id = c.create_text(
            32, bot_y + int(h * 0.017), text="",
            fill=C_TIME, font=s(BF_TIME_L), anchor="w")

        btn_x1, btn_x2 = w - 96, w - 20
        btn_mid = (btn_x1 + btn_x2) // 2
        btn = _round_rect(c, btn_x1, bot_y, btn_x2, bot_y + int(h * 0.031), 11,
                          fill=C_ACCENT, outline="")
        btn_txt = c.create_text(btn_mid, bot_y + int(h * 0.016),
                                text="refresh", fill="white",
                                font=s(("Consolas", 9, "bold")))
        c.tag_bind(btn,     "<Button-1>", lambda e: self.refresh())
        c.tag_bind(btn_txt, "<Button-1>", lambda e: self.refresh())

        c.create_text(w // 2, h - int(h * 0.016),
                      text="drag to move  |  click to fold",
                      fill="#5a5a78", font=(self._s(BF_TIME)[0], max(5, int(7 * self._scale))))

    # ================================================================
    #  Data update  (fonts unchanged, only values)
    # ================================================================

    def _update_stats(self):
        c = self._expanded_canvas
        d = self._data

        pct = self._remaining_pct()
        total = d.balance_cny + d.monthly_cost_cny
        color = self._bar_color(pct)

        x1, y1, x2, y2 = self._gauge_bar_coords
        self._draw_gauge(c, x1, y1, x2, y2, pct)
        c.itemconfigure(self._gauge_pct_id, text=f"{pct:.1f}%", fill=color)
        c.itemconfigure(self._gauge_sub_id,
                        text=f"remaining Y {d.balance_cny:.4f}  /  total Y {total:.4f}")

        for key, fmt, vid in self._stat_rows:
            val = getattr(d, key, 0)
            c.itemconfigure(vid, text=fmt(val))

        def _model_tokens(name):
            total = 0
            for m in d.per_model_amount:
                if name in m["model"]:
                    for u in m.get("usage", []):
                        if u["type"] in ("PROMPT_CACHE_HIT_TOKEN",
                                         "PROMPT_CACHE_MISS_TOKEN",
                                         "RESPONSE_TOKEN"):
                            total += int(float(u["amount"]))
            return total

        def _model_cost(name):
            total = 0.0
            for m in d.per_model_cost:
                if name in m["model"]:
                    for u in m.get("usage", []):
                        if u["type"] in ("PROMPT_CACHE_HIT_TOKEN",
                                         "PROMPT_CACHE_MISS_TOKEN",
                                         "RESPONSE_TOKEN"):
                            total += float(u["amount"])
            return total

        for name, color, tk_lbl, co_lbl in self._model_rows:
            c.itemconfigure(tk_lbl, text=f"tk  {self._fmt_num(_model_tokens(name))}")
            c.itemconfigure(co_lbl, text=f"Y  {_model_cost(name):.4f}")

        c.itemconfigure(self._updated_id, text=f"updated  {d.last_updated}")

    def _draw_gauge(self, c, x1, y1, x2, y2, pct):
        c.delete("gauge")
        w, bar_h = x2 - x1, y2 - y1
        r = bar_h // 2
        fill_w = max(0, min(w, int(w * pct / 100)))
        _round_rect(c, x1, y1, x2, y2, r, fill=C_BAR_BG, outline="", tags="gauge")
        if fill_w > r * 2:
            _round_rect(c, x1, y1, x1 + fill_w, y2, r,
                        fill=self._bar_color(pct), outline="", tags="gauge")
        elif fill_w > 0:
            c.create_oval(x1, y1 + 1, x1 + fill_w * 2, y2 - 1,
                          fill=self._bar_color(pct), outline="", tags="gauge")

    def _show_expanded(self):
        if self._compact_canvas.winfo_ismapped():
            self._compact_canvas.pack_forget()
        self._expanded_canvas.pack(fill="both", expand=True)
        self.geometry(f"{self._win_w}x{self._win_h}")
        self._redraw_expanded()
        self._update_stats()

    # ================================================================
    #  Interactions
    # ================================================================

    def _edge_from_xy(self, x, y):
        w, h = self._win_w, self._win_h
        e = self.EDGE_WIDTH
        l, r, t, b = x <= e, x >= w - e, y <= e, y >= h - e
        if l and t:   return "nw"
        if r and t:   return "ne"
        if l and b:   return "sw"
        if r and b:   return "se"
        if l:         return "w"
        if r:         return "e"
        if t:         return "n"
        if b:         return "s"
        return None

    def _cursor_for(self, edge):
        cursors = {
            "nw": "top_left_corner", "se": "bottom_right_corner",
            "ne": "top_right_corner", "sw": "bottom_left_corner",
            "n":  "top_side", "s": "bottom_side",
            "e":  "right_side", "w": "left_side",
        }
        self.configure(cursor=cursors.get(edge, "arrow"))

    def _on_press(self, event):
        edge = self._edge_from_xy(event.x, event.y)
        if edge:
            self._resize_edge = edge
            self._resize_orig_x = event.x_root
            self._resize_orig_y = event.y_root
            self._resize_orig_w = self._win_w
            self._resize_orig_h = self._win_h
            self._resize_orig_win_x = self.winfo_x()
            self._resize_orig_win_y = self.winfo_y()
            self._drag_started = False
        else:
            self._resize_edge = None
            self._drag_started = False
        self._drag_x, self._drag_y = event.x, event.y

    def _on_release(self, event):
        if self._resize_edge:
            self._resize_edge = None
            self.configure(cursor="arrow")
        elif not self._drag_started:
            self.toggle()
        self._drag_started = False

    def _on_motion(self, event):
        self._cursor_for(self._edge_from_xy(event.x, event.y))

    def _on_drag(self, event):
        if self._resize_edge:
            self._do_resize(event)
            return
        if not self._drag_started:
            self._drag_started = True
            self._drag_x, self._drag_y = event.x, event.y
        self.geometry(
            f"+{self.winfo_x() + event.x - self._drag_x}"
            f"+{self.winfo_y() + event.y - self._drag_y}"
        )

    def _do_resize(self, event):
        dx = event.x_root - self._resize_orig_x
        dy = event.y_root - self._resize_orig_y
        edge = self._resize_edge

        new_x = self._resize_orig_win_x
        new_y = self._resize_orig_win_y
        new_w = self._resize_orig_w
        new_h = self._resize_orig_h

        if "e" in edge:
            new_w = max(MIN_W, self._resize_orig_w + dx)
        if "w" in edge:
            new_w = max(MIN_W, self._resize_orig_w - dx)
            new_x = self._resize_orig_win_x + (self._resize_orig_w - new_w)
        if "s" in edge:
            new_h = max(MIN_H, self._resize_orig_h + dy)
        if "n" in edge:
            new_h = max(MIN_H, self._resize_orig_h - dy)
            new_y = self._resize_orig_win_y + (self._resize_orig_h - new_h)

        self._win_w, self._win_h = new_w, new_h
        self.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")

        if self._expanded:
            self._redraw_expanded()
            self._update_stats()
        else:
            self._draw_compact()

    def _on_right_click(self, event):
        menu = tk.Menu(self, tearoff=0,
                       bg=C_CARD, fg=C_TEXT,
                       activebackground=C_ACCENT, activeforeground="white",
                       relief="flat", bd=0)
        menu.add_command(label="Refresh", command=self.refresh)
        menu.add_command(label="Expand / Collapse", command=self.toggle)
        menu.add_separator()
        menu.add_command(label="Quit", command=self.tray.quit_app)
        menu.post(event.x_root, event.y_root)

    def _on_hover(self, entering: bool):
        self._hover = entering
        if not self._expanded:
            self.attributes("-alpha", 0.98 if entering else 0.85)

    def toggle(self):
        if self._expanded:
            self._expanded = False
            self._win_w, self._win_h = DEF_COMPACT_W, DEF_COMPACT_H
            self._show_compact()
            self._draw_compact()
        else:
            self._expanded = True
            self._win_w, self._win_h = DEF_EXPAND_W, DEF_EXPAND_H
            self._show_expanded()

    # ================================================================
    #  Data refresh
    # ================================================================

    def refresh(self):
        def _fetch():
            self._data = TokenData.fetch()
            self.after(0, self._apply_update)
        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_update(self):
        if self._expanded:
            self._update_stats()
        self._draw_compact()

    def _start_refresh(self):
        self.refresh()
        self.after(REFRESH_INTERVAL, self._periodic_refresh)

    def _periodic_refresh(self):
        self.refresh()
        self.after(REFRESH_INTERVAL, self._periodic_refresh)
