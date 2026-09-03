import subprocess
import sys
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import PRIMARY, SUCCESS

from ui.widget.scrollable_frame import bring_to_front, center_window
from version import __version__


class LauncherWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self._configure_window()
        self._build_ui()

    def _configure_window(self):
        self.title(f"INKAZA v{__version__}")
        self.resizable(False, False)
        center_window(self, width=460, height=260)
        bring_to_front(self)

    def _build_ui(self):
        container = ttk.Frame(self, padding=32)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="INKAZA",
            font=("Arial", 22, "bold"),
            anchor="center",
        ).pack(fill="x", pady=(0, 26))

        ttk.Button(
            container,
            text="Gerenciar Propriedade",
            style=PRIMARY,
            command=lambda: self._open("--admin"),
        ).pack(fill="x", ipady=9, pady=(0, 14))

        ttk.Button(
            container,
            text="Publicar Propriedade",
            style=SUCCESS,
            state="disabled",
        ).pack(fill="x", ipady=9)

    def _open(self, target: str):
        subprocess.Popen(self._build_command(target))
        self.destroy()

    @staticmethod
    def _build_command(target: str) -> list[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable, target]

        launcher_path = Path(__file__).resolve().parents[2] / "launcher.pyw"
        return [sys.executable, str(launcher_path), target]


def main():
    app = LauncherWindow()
    app.mainloop()
