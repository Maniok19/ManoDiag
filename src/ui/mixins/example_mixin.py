from PyQt6.QtCore import QTimer
from src.core.position_manager import PositionManager
import json
import os

class ExampleMixin:
    def _load_example(self) -> None:
        # Fichier par défaut (optionnel)
        example_text = """flowchart LR
A[Start] --> B{Decision}
B -->|Yes| C[Action 1]
B -->|No| D[Action 2]
C --> E[End]
D --> E
"""
        try:
            candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exemple.manodiag.json")
            if os.path.exists(candidate):
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                t = data.get("text")
                if t:
                    example_text = t
        except Exception:
            pass
        self.text_editor.setPlainText(self._ensure_fixed_layout_config(example_text))
        self._render_diagram()
        QTimer.singleShot(0, self._reset_view)

    def _load_flowchart_example(self) -> None:
        self._load_example()
        self.status_bar.showMessage("Exemple flowchart chargé")

    def _load_sequence_example(self) -> None:
        seq = """sequence
title Exemple Séquence
participant U as Utilisateur
participant S as Serveur
U ->> S: Requête
S --> U: Réponse
note over U,S: Note partagée
"""
        self.text_editor.setPlainText(seq)
        PositionManager().clear_positions()
        self._render_diagram()
        self.status_bar.showMessage("Exemple sequence chargé")