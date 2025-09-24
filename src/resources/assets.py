from __future__ import annotations
import os
import sys
from typing import Optional

def _project_root() -> str:
    # Support PyInstaller (sys._MEIPASS) et exécution locale
    if hasattr(sys, "_MEIPASS"):
        return getattr(sys, "_MEIPASS")
    # src/resources/assets.py -> remonter à la racine du projet
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _candidates():
    return [
        "logo_ManoDiag.png",
        os.path.join("assets", "logo_ManoDiag.png"),
        os.path.join("src", "resources", "logo_ManoDiag.png"),
        os.path.join("src", "resources", "images", "logo_ManoDiag.png"),
        os.path.join("resources", "logo_ManoDiag.png"),
    ]

def get_logo_path() -> str:
    root = _project_root()
    for rel in _candidates():
        p = os.path.join(root, rel)
        if os.path.exists(p):
            return p
    return ""