import os
from pathlib import Path
import sys


def has_auto_start_flag() -> bool:
    return "--auto-start" in sys.argv


def get_project_root_dir() -> Path:
    """
    Root é a raiz em que a aplicação está = nível anterior do app
    """
    if getattr(sys, "frozen", False):
        # Executável (PyInstaller)
        return Path(sys.executable).resolve().parent
    else:
        # Ambiente de desenvolvimento
        return Path(__file__).resolve().parent.parent.parent


def get_app_base_dir() -> Path:
    """
    Base é a raiz do projeto = ad-bot/
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_bot_user_data_dir(app_name="INKAZA Automation") -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / app_name / "ChromeBotProfile"

    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / app_name
            / "ChromeBotProfile"
        )

    if sys.platform.startswith("linux"):
        return Path.home() / ".config" / app_name / "ChromeBotProfile"

    raise RuntimeError(f"SO não suportado: {sys.platform}")


def get_inkaza_data_dir() -> Path:
    if not getattr(sys, "frozen", False):
        return get_app_base_dir() / "data"

    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "INKAZA"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "INKAZA"

    if sys.platform.startswith("linux"):
        return Path.home() / ".local" / "share" / "INKAZA"

    raise RuntimeError(f"SO não suportado: {sys.platform}")
