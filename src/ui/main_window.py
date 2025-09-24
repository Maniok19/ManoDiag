"""
MainWindow - Fenêtre principale de ManoDiag
- Barre de menus (Fichier, Vue, Help)
- Éditeur de texte (Mermaid-like) + Vue graphique (QGraphicsView)
- Rendu via DiagramEngine
- Export PNG, sauvegarde/restauration, réglages d'affichage
"""

from __future__ import annotations
from typing import Dict
import os
import json
import math
import logging
import traceback
import os
import json
from typing import Dict

from PyQt6.QtCore import Qt, QTimer, QRectF, QMarginsF
from PyQt6.QtGui import QAction, QPainter, QColor, QKeySequence, QImage, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGraphicsScene,
    QFileDialog, QMessageBox, QStatusBar, QDialog, QTextBrowser, QPushButton
)

from src.core.diagram_engine import DiagramEngine
from src.core.position_manager import PositionManager
from src.ui.code_editor import CodeEditor
from src.ui.grid_graphics_view import GridGraphicsView
from src.resources.help import HELP_HTML
from src.resources.assets import get_logo_path

log = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application ManoDiag."""

    def __init__(self) -> None:
        super().__init__()
        self.current_settings: Dict[str, object] = {}
        self._initial_fit_done = False  # <- ajouté

        self.setWindowTitle("ManoDiag Professional - Créateur de Diagrammes")
        self.setGeometry(100, 100, 1600, 1000)

        # Icône de fenêtre
        try:
            logo_path = get_logo_path()
            if logo_path:
                self.setWindowIcon(QIcon(logo_path))
            self._app_logo_path = logo_path  # pour About/Help
        except Exception:
            self._app_logo_path = ""

        # Thème simple
        self.setStyleSheet("""
            QMainWindow { background-color: #f8f9fa; }
            QMenuBar { background-color: #2c3e50; color: white; padding: 5px; }
            QMenuBar::item { padding: 8px 12px; }
            QMenuBar::item:selected { background-color: #34495e; }
            QStatusBar { background-color: #2c3e50; color: white; padding: 5px; }
            QGraphicsView {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
        """)

        try:
            self._setup_ui()
            self._setup_menu_bar()
            self._setup_status_bar()
            self._setup_engine()
            self._load_example()
            log.info("MainWindow initialisée.")
        except Exception as e:
            log.exception("Erreur lors de l'initialisation: %s", e)

    # ---------- Initialisation UI ----------
    def _normalize_layout(self) -> None:
        """Ajuste la taille des nœuds au texte, aligne sur la grille et réaligne légèrement via les arêtes."""
        try:
            renderer = getattr(self.diagram_engine, "renderer", None)
            if renderer and hasattr(renderer, "normalize_layout"):
                renderer.normalize_layout(self.graphics_scene, direction=None)
                # Rafraîchir la vue
                self.graphics_scene.update()
                self.status_bar.showMessage("Mise en page normalisée")
            else:
                QMessageBox.information(self, "Normaliser", "Fonction non disponible.")
        except Exception as e:
            import traceback, logging
            logging.getLogger(__name__).exception("Erreur de normalisation: %s", e)
            self.status_bar.showMessage(f"Erreur de normalisation: {str(e)}")

    def _setup_ui(self) -> None:
        """Construit l'éditeur + la scène de rendu avec un splitter."""
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        center_widget = QWidget(self)
        center_layout = QVBoxLayout(center_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Éditeur
        self.text_editor = CodeEditor(self)
        self.text_editor.textChanged.connect(self._on_text_changed)

        # Vue/Scène
        self.position_manager = PositionManager()
        self.graphics_view = GridGraphicsView(self)
        # GRAND RECT LIBRE (100k x 100k) centré sur (0,0)
        self.graphics_scene = QGraphicsScene(-50000, -50000, 100000, 100000, self)
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setDragMode(self.graphics_view.DragMode.NoDrag)

        splitter.addWidget(self.text_editor)
        splitter.addWidget(self.graphics_view)
        splitter.setSizes([600, 800])

        center_layout.addWidget(splitter)
        main_layout.addWidget(center_widget)

        # Timer d'anti-rebond pour le rendu
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._render_diagram)

    def _setup_status_bar(self) -> None:
        """Crée une barre de statut simple."""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")

    def _setup_engine(self) -> None:
        """Instancie le moteur (parser + renderer) et initialise les réglages."""
        self.diagram_engine = DiagramEngine()
        log.info("Moteur de diagramme initialisé.")

        # IMPORTANT: écoute des déplacements de nœuds pour forcer layout: fixed dans l’éditeur
        try:
            self.diagram_engine.renderer.signal_emitter.position_changed.connect(
                self._on_node_position_signal
            )
        except Exception as e:
            log.warning("Impossible de connecter le signal de position: %s", e)

        # Réglages par défaut
        self.current_settings = {
            "show_grid": True,
            "antialiasing": True,
            "node_color": QColor(220, 221, 255),
            "border_color": QColor(100, 100, 200),
        }
        self._apply_settings(self.current_settings)

    def _setup_menu_bar(self) -> None:
        """Construit la barre de menus (Fichier, Vue, Help)."""
        menubar = self.menuBar()

        # Fichier
        file_menu = menubar.addMenu("Fichier")

        new_action = QAction("Nouveau", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_diagram)
        file_menu.addAction(new_action)

        open_action = QAction("Ouvrir…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_diagram)
        file_menu.addAction(open_action)

        save_action = QAction("Sauvegarder…", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_diagram)
        file_menu.addAction(save_action)

        export_action = QAction("Exporter en PNG", self)
        export_action.triggered.connect(self._export_png)
        file_menu.addAction(export_action)

        # Vue
        view_menu = menubar.addMenu("Vue")

        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        fit_action = QAction("Ajuster à la fenêtre", self)
        fit_action.triggered.connect(self._fit_in_view)
        view_menu.addAction(fit_action)

        view_menu.addSeparator()

        self.action_show_grid = QAction("Afficher la grille", self, checkable=True)
        self.action_show_grid.setChecked(True)
        self.action_show_grid.toggled.connect(self._update_settings_from_menu)
        view_menu.addAction(self.action_show_grid)

        self.action_antialiasing = QAction("Anticrénelage", self, checkable=True)
        self.action_antialiasing.setChecked(True)
        self.action_antialiasing.toggled.connect(self._update_settings_from_menu)
        view_menu.addAction(self.action_antialiasing)

        view_menu.addSeparator()

        self.action_node_color = QAction("Couleur des nœuds…", self)
        self.action_node_color.triggered.connect(self._choose_node_color)
        view_menu.addAction(self.action_node_color)

        self.action_border_color = QAction("Couleur de la bordure…", self)
        self.action_border_color.triggered.connect(self._choose_border_color)
        view_menu.addAction(self.action_border_color)

        view_menu.addSeparator()

        reset_view_action = QAction("Réinitialiser la vue", self)
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)

        reset_pos_action = QAction("Réinitialiser les positions", self)
        reset_pos_action.triggered.connect(self._confirm_reset_positions)
        view_menu.addAction(reset_pos_action)

        # Éditer
        edit_menu = menubar.addMenu("Éditer")

        normalize_action = QAction("Normaliser", self)
        normalize_action.setToolTip("Ajuster la taille des nœuds au texte et aligner les positions sur la grille")
        normalize_action.triggered.connect(self._normalize_layout)
        edit_menu.addAction(normalize_action)

        # Nouveaux exemples
        edit_menu.addSeparator()
        load_flow_example_action = QAction("Charger l'exemple de flowchart", self)
        load_flow_example_action.triggered.connect(self._load_flowchart_example)
        edit_menu.addAction(load_flow_example_action)

        load_seq_example_action = QAction("Charger l'exemple de sequence", self)
        load_seq_example_action.triggered.connect(self._load_sequence_example)
        edit_menu.addAction(load_seq_example_action)

        # Help
        help_menu = menubar.addMenu("Help")

        help_action = QAction("User Guide…", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._show_help_dialog)
        help_menu.addAction(help_action)

        about_action = QAction("About ManoDiag", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    # ---------- Slots / Actions ----------

    def _show_help_dialog(self) -> None:
        """Affiche le guide utilisateur (HTML intégré)."""
        dlg = QDialog(self)
        dlg.setWindowTitle("ManoDiag – User Guide")
        dlg.resize(900, 650)

        layout = QVBoxLayout(dlg)
        browser = QTextBrowser(dlg)
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        layout.addWidget(browser)

        btn_close = QPushButton("Fermer", dlg)
        btn_close.clicked.connect(dlg.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn_close)
        layout.addLayout(row)

        dlg.setModal(True)
        dlg.exec()

    def _show_about_dialog(self) -> None:
        """Affiche la boîte 'À propos'."""
        logo_html = ""
        if getattr(self, "_app_logo_path", ""):
            logo_html = f"<div style='text-align:center;margin-bottom:10px;'><img src='file://{self._app_logo_path}' width='120' height='120' style='border-radius:8px;'/></div>"

        QMessageBox.about(
            self,
            "À propos de ManoDiag",
            (
                f"{logo_html}"
                "<div style='text-align:center;'>"
                "<b>ManoDiag</b><br>"
                "Créateur de diagrammes local basé sur PyQt6.<br><br>"
                "Fonctionnalités : rendu interactif, déplacement/redimensionnement de nœuds, "
                "arêtes Bézier, export PNG, sauvegarde/restauration.<br><br>"
                "<small>© 2025 ManoDiag. Tous droits réservés.</small>"
                "</div>"
            ),
        )

    def _update_settings_from_menu(self) -> None:
        """Applique les réglages depuis les actions du menu."""
        self.current_settings = {
            "show_grid": self.action_show_grid.isChecked(),
            "antialiasing": self.action_antialiasing.isChecked(),
            "node_color": self.current_settings.get("node_color", QColor(220, 221, 255)),
            "border_color": self.current_settings.get("border_color", QColor(100, 100, 200)),
        }
        self._apply_settings(self.current_settings)

    def _choose_node_color(self) -> None:
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self.current_settings.get("node_color", QColor(220, 221, 255)), self, "Choisir la couleur du nœud")
        if color.isValid():
            self.current_settings["node_color"] = color
            self._update_settings_from_menu()

    def _choose_border_color(self) -> None:
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self.current_settings.get("border_color", QColor(100, 100, 200)), self, "Choisir la couleur de bordure")
        if color.isValid():
            self.current_settings["border_color"] = color
            self._update_settings_from_menu()

    def _apply_settings(self, settings: Dict[str, object]) -> None:
        """Applique les paramètres d'affichage au renderer et à la vue."""
        self.current_settings = settings

        # Rendu (noeuds)
        if hasattr(self.diagram_engine, "renderer") and hasattr(self.diagram_engine.renderer, "update_settings"):
            self.diagram_engine.renderer.update_settings(settings)

        # Grille
        self.graphics_view.set_grid_visible(bool(settings.get("show_grid", True)))

        # Anticrénelage
        aa = bool(settings.get("antialiasing", True))
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing, aa)

        # Re-rendu
        self._render_diagram()
        self.status_bar.showMessage("Paramètres mis à jour")

    def _on_text_changed(self) -> None:
        """Anti-rebond du rendu lors des frappes."""
        self.render_timer.start(800)

    def _render_diagram(self) -> None:
        """Parse et rend le diagramme dans la scène."""
        text = self.text_editor.toPlainText().strip()
        try:
            if text:
                self.diagram_engine.render_to_scene(text, self.graphics_scene)

                items = self.graphics_scene.items()
                if items:
                    # NE PLUS RÉTRÉCIR LA SCÈNE : on garde l'espace infini
                    pass

                node_count = sum(1 for it in items if hasattr(it, "node_id"))
                self.status_bar.showMessage(f"Diagramme rendu - {node_count} nœuds")
            else:
                if hasattr(self.diagram_engine, "renderer") and hasattr(self.diagram_engine.renderer, "clear_scene_completely"):
                    self.diagram_engine.renderer.clear_scene_completely(self.graphics_scene)
                else:
                    self.graphics_scene.clear()
                self.status_bar.showMessage("Diagramme vide")
        except Exception as e:
            log.exception("Erreur de rendu: %s", e)
            self.status_bar.showMessage(f"Erreur: {str(e)}")

    def _new_diagram(self) -> None:
        """Nouveau diagramme vide."""
        self.text_editor.clear()
        self.graphics_scene.clear()
        self.position_manager.clear_positions()
        self.status_bar.showMessage("Nouveau diagramme créé")

    def _reset_view(self) -> None:
        """Réinitialise le zoom et recentre la vue."""
        try:
            self.graphics_view.resetTransform()
            items = self.graphics_scene.items()
            if items:
                self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            else:
                self.graphics_view.centerOn(0, 0)
            self.status_bar.showMessage("Vue réinitialisée")
        except Exception as e:
            log.warning("Erreur lors de la réinitialisation de la vue: %s", e)
            self.status_bar.showMessage("Erreur lors de la réinitialisation de la vue")

    def _confirm_reset_positions(self) -> None:
        """Demande confirmation avant d'effacer positions et arêtes personnalisées."""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Confirmer la réinitialisation")
            msg_box.setText("Réinitialiser les positions des éléments ?")
            msg_box.setInformativeText(
                "Cette action va remettre tous les nœuds à leur position par défaut.\n"
                "Toutes les positions personnalisées seront perdues."
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
            no_button = msg_box.button(QMessageBox.StandardButton.No)
            yes_button.setText("Réinitialiser")
            no_button.setText("Annuler")

            result = msg_box.exec()
            if result == QMessageBox.StandardButton.Yes:
                self._reset_positions()
            else:
                self.status_bar.showMessage("Réinitialisation annulée")
        except Exception as e:
            log.warning("Erreur lors de la confirmation: %s", e)
            self._reset_positions()

    def _reset_positions(self) -> None:
        """Efface les positions/états et réapplique un rendu au layout par défaut."""
        try:
            self.position_manager.clear_positions()

            if hasattr(self.diagram_engine, "renderer") and hasattr(self.diagram_engine.renderer, "clear_scene_completely"):
                self.diagram_engine.renderer.clear_scene_completely(self.graphics_scene)
            else:
                self.graphics_scene.clear()

            text = self.text_editor.toPlainText().strip()
            if text:
                # Retire le bloc YAML principal si présent
                cleaned = self._remove_top_yaml_block(text)
                self.text_editor.setPlainText(cleaned)

                # Re-rendu immédiat
                self.diagram_engine.render_to_scene(cleaned, self.graphics_scene)
                self._reset_view()
                self.status_bar.showMessage("Positions réinitialisées - layout par défaut appliqué")
            else:
                self.status_bar.showMessage("Positions réinitialisées")
        except Exception as e:
            log.exception("Erreur lors de la réinitialisation des positions: %s", e)
            self.status_bar.showMessage(f"Erreur lors de la réinitialisation: {str(e)}")

    def _export_png(self) -> None:
        """Export de la scène en PNG (avec marges sécurisées)."""
        try:
            items = self.graphics_scene.items()
            if not items:
                QMessageBox.information(self, "Exporter en PNG", "Aucun élément à exporter.")
                return
            file_path, _ = QFileDialog.getSaveFileName(self, "Exporter en PNG", "diagramme.png", "Images PNG (*.png)")
            if not file_path:
                return
            # État propre
            try:
                from src.graphics.interactive_node import InteractiveNode
                from src.graphics.interactive_edge import InteractiveEdge
                self.graphics_scene.clearSelection()
                InteractiveEdge.deselect_all_edges()
                for it in self.graphics_scene.items():
                    if hasattr(it, "set_handles_visible"):
                        try:
                            it.set_handles_visible(False)
                        except Exception:
                            pass
            except Exception:
                pass
            bounds: QRectF = self.graphics_scene.itemsBoundingRect()
            if bounds.isEmpty():
                QMessageBox.information(self, "Exporter en PNG", "Rien à exporter (bornes vides).")
                return

            margin = 24
            safe_pad = 2
            bounds = bounds.marginsAdded(QMarginsF(margin + safe_pad, margin + safe_pad, margin + safe_pad, margin + safe_pad))

            width = max(1, int(math.ceil(bounds.width())))
            height = max(1, int(math.ceil(bounds.height())))

            old_scene_rect = self.graphics_scene.sceneRect()
            self.graphics_scene.setSceneRect(bounds)
            self.graphics_scene.update()

            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.setDevicePixelRatio(1.0)
            image.fill(QColor(255, 255, 255, 255))

            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            self.graphics_scene.render(painter, target=QRectF(0, 0, float(width), float(height)), source=bounds)
            painter.end()
            self.graphics_scene.setSceneRect(old_scene_rect)

            if image.save(file_path, "PNG"):
                self.status_bar.showMessage(f"Exporté en PNG: {file_path}")
            else:
                QMessageBox.warning(self, "Exporter en PNG", "Échec de l'enregistrement de l'image.")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Exporter en PNG", f"Erreur: {str(e)}")

    def _zoom_in(self) -> None:
        self.graphics_view.scale(1.2, 1.2)
        self.status_bar.showMessage("Zoom avant")

    def _zoom_out(self) -> None:
        self.graphics_view.scale(0.8, 0.8)
        self.status_bar.showMessage("Zoom arrière")

    def _fit_in_view(self) -> None:
        try:
            items = self.graphics_scene.items()
            if items:
                self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
                self.status_bar.showMessage("Vue ajustée aux éléments")
            else:
                self.graphics_view.centerOn(0, 0)
                self.status_bar.showMessage("Vue centrée")
        except Exception as e:
            log.warning("Erreur lors de l'ajustement de la vue: %s", e)
            self.status_bar.showMessage("Erreur lors de l'ajustement de la vue")

    # ---------- Persistance (fichier) ----------

    def _qcolor_to_hex(self, color: QColor) -> str:
        return color.name()

    def _ensure_fixed_layout_config(self, text: str) -> str:
        """Garantit un bloc YAML layout: fixed pour flowchart uniquement (pas sequence)."""
        stripped = text.lstrip()
        if stripped.lower().startswith("sequence"):
            return text  # ne pas injecter pour diagrammes de séquence
        if "layout: fixed" in text:
            return text
        s = stripped
        if s.startswith('---'):
            start = text.find('---')
            end = text.find('\n---', start + 3)
            if end != -1:
                header = text[start + 3:end].strip('\n')
                body = text[end + 4:]
                lines = header.splitlines()
                replaced = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("layout:"):
                        lines[i] = "layout: fixed"
                        replaced = True
                        break
                if not replaced:
                    lines.append("layout: fixed")
                new_header = '\n'.join(lines)
                return f"---\n{new_header}\n---{body}"
        return """---
layout: fixed
---

""" + text

    def _remove_top_yaml_block(self, text: str) -> str:
        """Supprime le premier bloc YAML top-level, s'il existe."""
        lines = text.split('\n')
        new_lines = []
        skip = False
        for line in lines:
            if line.strip() == '---' and not skip:
                skip = True
                continue
            elif line.strip() == '---' and skip:
                skip = False
                continue
            elif not skip:
                new_lines.append(line)
        return '\n'.join(new_lines)

    def _save_diagram(self) -> None:
        """Sauvegarde texte + positions + réglages en .manodiag.json."""
        try:
            from datetime import datetime
            import json

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder le diagramme",
                "diagram.manodiag.json",
                "ManoDiag (*.manodiag.json);;JSON (*.json)"
            )
            if not file_path:
                return

            text = self.text_editor.toPlainText()
            pm = PositionManager()
            data = {
                "format": "manodiag",
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "diagram": {"text": text},
                "nodes": pm.custom_positions,
                "edges": pm.edge_data,
                "settings": {
                    "show_grid": bool(self.current_settings.get("show_grid", True)),
                    "antialiasing": bool(self.current_settings.get("antialiasing", True)),
                    "node_color": self._qcolor_to_hex(self.current_settings.get("node_color", QColor(220, 221, 255))),
                    "border_color": self._qcolor_to_hex(self.current_settings.get("border_color", QColor(100, 100, 200))),
                },
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.status_bar.showMessage(f"Diagramme sauvegardé: {file_path}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Sauvegarde", f"Erreur: {str(e)}")

    def _open_diagram(self) -> None:
        """Ouvre un fichier .manodiag.json et restaure scène + réglages."""
        try:
            self.position_manager.clear_positions()
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Ouvrir un diagramme",
                "",
                "ManoDiag (*.manodiag.json);;JSON (*.json)"
            )
            if not file_path:
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            text = data.get("diagram", {}).get("text", "")
            pm = PositionManager()
            nodes = data.get("nodes", {})
            if isinstance(nodes, dict):
                pm.custom_positions = nodes
            edges_custom = data.get("edges", data.get("edge_customizations", {}))
            if isinstance(edges_custom, dict):
                pm.edge_data = edges_custom
            pm.save_positions()

            settings = data.get("settings", {})
            if settings:
                if "show_grid" in settings:
                    self.current_settings["show_grid"] = bool(settings["show_grid"])
                if "antialiasing" in settings:
                    self.current_settings["antialiasing"] = bool(settings["antialiasing"])
                if "node_color" in settings:
                    self.current_settings["node_color"] = QColor(settings["node_color"])
                if "border_color" in settings:
                    self.current_settings["border_color"] = QColor(settings["border_color"])
                # N'applique pas encore le re-render forcé (évite double)
            # Ne pas injecter layout fixed si c'est un diagramme de séquence
            clean_text = text if text.lstrip().lower().startswith("sequence") else self._ensure_fixed_layout_config(text)
            self.text_editor.setPlainText(clean_text)

            # Appliquer réglages et rendre
            self._apply_settings(self.current_settings)
            self._reset_view()
            self.status_bar.showMessage(f"Diagramme chargé: {file_path}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ouvrir", f"Erreur: {str(e)}")

    # ---------- Amélioration logique: auto 'layout: fixed' ----------

    def _on_node_position_signal(self, node_id: str, x: float, y: float, w: float, h: float) -> None:
        """Lorsqu’un nœud bouge (signal du renderer), force l'ajout du bloc YAML layout: fixed."""
        text = self.text_editor.toPlainText()
        if "layout: fixed" not in text:
            self.text_editor.blockSignals(True)
            try:
                new_text = self._ensure_fixed_layout_config(text)
                self.text_editor.setPlainText(new_text)
            finally:
                self.text_editor.blockSignals(False)
            # Relance un rendu après courte temporisation
            self._on_text_changed()

    # ---------- Exemple ----------

    def _load_example(self) -> None:
        """Ouvre /exemple.manodiag.json au démarrage (fallback: exemple intégré)."""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            example_path = os.path.join(project_root, "exemple.manodiag.json")
            if os.path.exists(example_path):
                with open(example_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Texte
                text = data.get("diagram", {}).get("text", "") or ""
                text = self._ensure_fixed_layout_config(text)
                self.text_editor.setPlainText(text)

                # Positions/Arêtes
                pm = PositionManager()
                nodes = data.get("nodes", {})
                if isinstance(nodes, dict):
                    pm.custom_positions = nodes
                edges_custom = data.get("edges", data.get("edge_customizations", {}))
                if isinstance(edges_custom, dict):
                    pm.edge_data = edges_custom
                pm.save_positions()

                # Réglages
                settings = data.get("settings", {})
                if settings:
                    if "show_grid" in settings:
                        self.action_show_grid.setChecked(bool(settings["show_grid"]))
                    if "antialiasing" in settings:
                        self.action_antialiasing.setChecked(bool(settings["antialiasing"]))
                    if "node_color" in settings:
                        self.current_settings["node_color"] = QColor(settings["node_color"])
                    if "border_color" in settings:
                        self.current_settings["border_color"] = QColor(settings["border_color"])
                    self._update_settings_from_menu()

                # Rendu + ajustement
                self._render_diagram()
                # self._reset_view()  # <- remplacé
                QTimer.singleShot(0, self._reset_view)  # <- décale le reset après affichage
                self.status_bar.showMessage(f"Exemple chargé: {example_path}")
                return
        except Exception as e:
            logging.getLogger(__name__).warning("Chargement de l'exemple JSON échoué: %s", e)
        # Fallback: exemple intégré
        example = '''flowchart LR
    A["<b>Bienvenue sur ManoDiag</b><br>Créateur de diagrammes professionnels"]
    B["Éditez le code (panneau de gauche)"]
    C["Rendu interactif (panneau de droite)"]
    D["Déplacez / Redimensionnez les nœuds"]
    E["Stylisez avec <code>classDef</code>"]
    F["Export PNG"]
    G["Sauvegarde / Chargement"]
    H["Zoom / Ajuster la vue"]
    I["Arêtes avec label"]
    J["Arêtes bidirectionnelles"]
    K["Cibles multiples"]
    L["Bascule Bézier (clic droit sur l’arête)"]
    M["<b>Bienvenue & bon usage !</b>"]

A --> B
A --> C
B -- saisie --> C
C --> D
D --> E
E --> F
E --> G
A --> H & I & J
I -- exemple --> F
B <--> J
C --> L
L -- clic droit --> J
A -- bienvenue --> M

classDef primary fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
classDef success fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
classDef info fill:#eef7ff,stroke:#0d47a1,stroke-width:2px
classDef warning fill:#fff8e1,stroke:#f57f17,stroke-width:2px
classDef accent fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
classDef emphasis fill:#fff0f2,stroke:#c2185b,stroke-width:2px

A:::primary
D:::info
E:::accent
F:::success
G:::primary
H:::info
I:::warning
J:::warning
K:::accent
L:::accent
M:::success
'''
        self.text_editor.setPlainText(self._ensure_fixed_layout_config(example))
        self._render_diagram()
        # self._reset_view()  # <- remplacé
        QTimer.singleShot(0, self._reset_view)  # <- décale le reset après affichage

    def _load_sequence_example(self) -> None:
        """Charge diagramseq.manodiag.json (exemple de diagramme de séquence)."""
        try:
            from PyQt6.QtGui import QColor
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(project_root, "diagramseq.manodiag.json")
            if not os.path.exists(file_path):
                QMessageBox.information(self, "Exemple sequence", f"Fichier introuvable:\n{file_path}")
                return

            # Réinitialiser état
            self.position_manager.clear_positions()

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            text = data.get("diagram", {}).get("text", "") or ""
            # Ne pas injecter layout: fixed si c'est un diagramme sequence
            if text.lstrip().lower().startswith("flowchart"):
                text = self._ensure_fixed_layout_config(text)

            self.text_editor.setPlainText(text)

            # Positions participants / edges custom
            pm = PositionManager()
            nodes = data.get("nodes", {})
            if isinstance(nodes, dict):
                pm.custom_positions = nodes
            edges_custom = data.get("edges", data.get("edge_customizations", {}))
            if isinstance(edges_custom, dict):
                pm.edge_data = edges_custom
            pm.save_positions()

            # Réglages
            settings = data.get("settings", {})
            if settings:
                if "show_grid" in settings:
                    self.action_show_grid.setChecked(bool(settings["show_grid"]))
                if "antialiasing" in settings:
                    self.action_antialiasing.setChecked(bool(settings["antialiasing"]))
                if "node_color" in settings:
                    self.current_settings["node_color"] = QColor(settings["node_color"])
                if "border_color" in settings:
                    self.current_settings["border_color"] = QColor(settings["border_color"])
                self._apply_settings(self.current_settings)
            else:
                self._render_diagram()

            self._reset_view()
            self.status_bar.showMessage(f"Exemple sequence chargé: {file_path}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Exemple sequence", f"Erreur: {str(e)}")

    def _load_flowchart_example(self) -> None:
        """Charge exemple.manodiag.json (exemple de flowchart)."""
        try:
            from PyQt6.QtGui import QColor
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(project_root, "exemple.manodiag.json")
            if not os.path.exists(file_path):
                QMessageBox.information(self, "Exemple flowchart", f"Fichier introuvable:\n{file_path}")
                return

            # Réinitialiser état
            self.position_manager.clear_positions()

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            text = data.get("diagram", {}).get("text", "") or ""
            if text.strip():
                text = self._ensure_fixed_layout_config(text)
            self.text_editor.setPlainText(text)

            pm = PositionManager()
            nodes = data.get("nodes", {})
            if isinstance(nodes, dict):
                pm.custom_positions = nodes
            edges_custom = data.get("edges", data.get("edge_customizations", {}))
            if isinstance(edges_custom, dict):
                pm.edge_data = edges_custom
            pm.save_positions()

            settings = data.get("settings", {})
            if settings:
                if "show_grid" in settings:
                    self.action_show_grid.setChecked(bool(settings["show_grid"]))
                if "antialiasing" in settings:
                    self.action_antialiasing.setChecked(bool(settings["antialiasing"]))
                if "node_color" in settings:
                    self.current_settings["node_color"] = QColor(settings["node_color"])
                if "border_color" in settings:
                    self.current_settings["border_color"] = QColor(settings["border_color"])
                self._apply_settings(self.current_settings)
            else:
                self._render_diagram()

            self._reset_view()
            self.status_bar.showMessage(f"Exemple flowchart chargé: {file_path}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Exemple flowchart", f"Erreur: {str(e)}")