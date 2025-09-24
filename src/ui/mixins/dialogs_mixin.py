from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QMessageBox
from src.resources.help import HELP_HTML

class DialogsMixin:
    def _show_help_dialog(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("ManoDiag – User Guide")
        dlg.resize(900, 650)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser(dlg)
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        layout.addWidget(browser)
        row = QHBoxLayout()
        btn = QPushButton("Fermer", dlg)
        btn.clicked.connect(dlg.accept)
        row.addStretch(1); row.addWidget(btn)
        layout.addLayout(row)
        dlg.exec()

    def _show_about_dialog(self) -> None:
        logo_html = ""
        if getattr(self, "_app_logo_path", ""):
            logo_html = f"<div style='text-align:center;margin-bottom:10px;'><img src='file://{self._app_logo_path}' width='120' height='120' style='border-radius:8px;'/></div>"
        QMessageBox.about(
            self,
            "À propos de ManoDiag",
            (
                f"{logo_html}"
                "<div style='text-align:center;'>"
                "<b>ManoDiag</b><br>Créateur de diagrammes local basé sur PyQt6.<br><br>"
                "Rendu interactif, déplacement/redimensionnement, arêtes Bézier, export PNG, sauvegarde/restauration.<br><br>"
                "<small>© 2025 ManoDiag. Tous droits réservés.</small>"
                "</div>"
            ),
        )