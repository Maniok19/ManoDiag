#!/usr/bin/env python3
"""
ManoDiag - Entrée principale de l'application
- Initialise QApplication
- Configure le logging
- Lance la fenêtre principale
"""

import sys
import os
import logging
import traceback

# Ajoute la racine du projet au PYTHONPATH (exécution locale)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

from src.resources.assets import get_logo_path

def configure_logging():
    """Configure un logging simple en console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

def main():
    configure_logging()
    log = logging.getLogger("ManoDiag")
    log.info("Démarrage de ManoDiag...")

    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName("ManoDiag")
        app.setOrganizationName("ManoDiag")

        # Icône d’application + Splash
        splash = None
        logo_path = get_logo_path()
        if logo_path:
            app.setWindowIcon(QIcon(logo_path))
            try:
                pix = QPixmap(logo_path)
                if not pix.isNull():
                    # Splash propre et net (redimensionné)
                    sp = pix.scaledToWidth(256, Qt.TransformationMode.SmoothTransformation)
                    splash = QSplashScreen(sp)
                    splash.show()
                    app.processEvents()
            except Exception:
                splash = None

        # Import tardif pour accélérer le démarrage et isoler les erreurs d'UI
        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.show()

        if splash:
            splash.finish(window)

        log.info("Application prête. Boucle d'événements en cours...")
        sys.exit(app.exec())

    except Exception as e:
        traceback.print_exc()
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Erreur ManoDiag")
            msg.setText(f"Erreur lors du démarrage:\n\n{str(e)}")
            msg.exec()
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()