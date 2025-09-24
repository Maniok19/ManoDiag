"""
CodeEditor - Éditeur de texte pour la saisie du diagramme (syntaxe Mermaid)
- Police monospace
- Mise en forme simple
- Placeholder d’exemple
"""

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.setFont(font)

        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                selection-background-color: #3399ff;
                padding: 10px;
            }
        """)

        self.setPlaceholderText(
            "Entrez votre code Mermaid ici...\n\n"
            "Exemple:\n"
            "flowchart TD\n"
            "    A[Début] --> B{Décision}\n"
            "    B -->|Oui| C[Action 1]\n"
            "    B -->|Non| D[Action 2]\n"
            "    C --> E[Fin]\n"
            "    D --> E\n"
        )