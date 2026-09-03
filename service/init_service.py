import json
from pathlib import Path
from helper.system_helper import get_project_root_dir

ROOT_DIR = Path(__file__).resolve().parent.parent

FILES = ["anuncios"]


def initialize():
    create_default_files()


def create_default_files():
    for filename in FILES:
        file = get_project_root_dir() / filename
        file.mkdir(parents=True, exist_ok=True)
