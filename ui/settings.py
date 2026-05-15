"""Built-in settings window for editing runtime config.py."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable

import config_manager


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, on_saved: Callable[[], None] | None = None):
        super().__init__(master)
        self.title("TokenSpider 设置")
        self.resizable(False, False)
        self.configure(bg="#171727")
        self.on_saved = on_saved
        self._inputs: dict[str, tk.Entry | tk.Text] = {}

        self.transient(master)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._build()
        self._load_values()
        self.update_idletasks()
        x = master.winfo_x() + 32
        y = master.winfo_y() + 32
        self.geometry(f"+{max(20, x)}+{max(20, y)}")
        self.lift()
        self.focus_force()

    def _build(self) -> None:
        root = tk.Frame(self, bg="#171727", padx=18, pady=16)
        root.pack(fill="both", expand=True)

        tk.Label(
            root,
            text="运行配置",
            bg="#171727",
            fg="#f0f0f5",
            font=("Microsoft YaHei UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(
            root,
            text=f"保存位置：{config_manager.CONFIG_PATH}",
            bg="#171727",
            fg="#8d8dae",
            font=("Microsoft YaHei UI", 8),
            wraplength=520,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

        row = 2
        for key in self._field_keys():
            meta = config_manager.FIELD_META.get(key, {"label": key, "kind": "text"})
            tk.Label(
                root,
                text=meta.get("label", key),
                bg="#171727",
                fg="#babadd",
                font=("Microsoft YaHei UI", 10),
            ).grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=6)

            if meta.get("multiline"):
                widget = tk.Text(
                    root,
                    width=58,
                    height=4,
                    bg="#22223a",
                    fg="#f0f0f5",
                    insertbackground="#f0f0f5",
                    relief="flat",
                    padx=8,
                    pady=6,
                    font=("Microsoft YaHei UI", 9),
                    wrap="word",
                )
            else:
                widget = tk.Entry(
                    root,
                    width=60,
                    bg="#22223a",
                    fg="#f0f0f5",
                    insertbackground="#f0f0f5",
                    relief="flat",
                    font=("Microsoft YaHei UI", 9),
                )
            widget.grid(row=row, column=1, sticky="ew", pady=6)
            self._inputs[key] = widget
            row += 1

        buttons = tk.Frame(root, bg="#171727")
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(16, 0))
        self._button(buttons, "重新载入", self._load_values).pack(side="left", padx=(0, 8))
        self._button(buttons, "保存并生效", self._save, primary=True).pack(side="left", padx=(0, 8))
        self._button(buttons, "关闭", self.destroy).pack(side="left")

    def _button(self, parent, text: str, command: Callable[[], None], primary: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg="#7b6cf6" if primary else "#2b2b48",
            fg="white",
            activebackground="#8b7cff" if primary else "#39395c",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=6,
            font=("Microsoft YaHei UI", 9, "bold" if primary else "normal"),
        )

    def _field_keys(self) -> list[str]:
        values = config_manager.all_config()
        keys = list(config_manager.DEFAULT_CONFIG)
        keys.extend(k for k in sorted(values) if k not in config_manager.DEFAULT_CONFIG)
        return keys

    def _load_values(self) -> None:
        values = config_manager.load_config()
        for key, widget in self._inputs.items():
            value = values.get(key, "")
            if isinstance(value, tuple):
                text = f"{value[0]}, {value[1]}"
            else:
                text = str(value)
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
                widget.insert("1.0", text)
            else:
                widget.delete(0, "end")
                widget.insert(0, text)

    def _widget_value(self, key: str) -> Any:
        widget = self._inputs[key]
        if isinstance(widget, tk.Text):
            raw = widget.get("1.0", "end").strip()
        else:
            raw = widget.get().strip()
        return config_manager._validate_value(key, raw)

    def _save(self) -> None:
        try:
            values = {key: self._widget_value(key) for key in self._inputs}
            config_manager.save_config(values)
        except Exception as exc:
            messagebox.showerror("保存失败", f"配置已回滚，原因：\n{exc}", parent=self)
            return

        if self.on_saved:
            self.on_saved()
        messagebox.showinfo("已保存", "配置已保存并即时生效。", parent=self)
