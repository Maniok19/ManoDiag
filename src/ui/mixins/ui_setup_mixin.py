import logging
from typing import Dict
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGraphicsScene, QStatusBar
from src.core.position_manager import PositionManager
from src.ui.code_editor import CodeEditor
from src.ui.grid_graphics_view import GridGraphicsView
from src.resources.assets import get_logo_path

log = logging.getLogger(__name__)

class UISetupMixin:
    current_settings: Dict[str, object]
    def _setup_base_window(self):
        self.current_settings = {}
        self._initial_fit_done = False
        self.setWindowTitle("ManoDiag Professional - Créateur de Diagrammes")
        self.setGeometry(100, 100, 1600, 1000)
        try:
            logo_path = get_logo_path()
            if logo_path:
                self.setWindowIcon(QIcon(logo_path))
            self._app_logo_path = logo_path or ""
        except Exception:
            self._app_logo_path = ""
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

    def _setup_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        center_widget = QWidget(self)
        center_layout = QVBoxLayout(center_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        self.text_editor = CodeEditor(self)
        self.text_editor.textChanged.connect(self._on_text_changed)

        self.position_manager = PositionManager()
        self.graphics_view = GridGraphicsView(self)
        self.graphics_scene = QGraphicsScene(-50000, -50000, 100000, 100000, self)
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setDragMode(self.graphics_view.DragMode.NoDrag)

        splitter.addWidget(self.text_editor)
        splitter.addWidget(self.graphics_view)
        splitter.setSizes([600, 800])
        center_layout.addWidget(splitter)
        main_layout.addWidget(center_widget)

        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._render_diagram)

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")

    def _apply_settings(self, settings: Dict[str, object]) -> None:
        self.current_settings = settings
        if hasattr(self.diagram_engine, "renderer") and hasattr(self.diagram_engine.renderer, "update_settings"):
            self.diagram_engine.renderer.update_settings(settings)
        self.graphics_view.set_grid_visible(bool(settings.get("show_grid", True)))
        aa = bool(settings.get("antialiasing", True))
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing, aa)
        self._render_diagram()
        self.status_bar.showMessage("Paramètres mis à jour")

    def _normalize_layout(self) -> None:
        try:
            renderer = getattr(self.diagram_engine, "renderer", None)
            if renderer and hasattr(renderer, "normalize_layout"):
                renderer.normalize_layout(self.graphics_scene, direction=getattr(renderer, "direction", None))
                self.status_bar.showMessage("Normalisation effectuée")
            else:
                self.status_bar.showMessage("Renderer non disponible")
        except Exception as e:
            logging.getLogger(__name__).exception("Erreur de normalisation: %s", e)
            self.status_bar.showMessage(f"Erreur de normalisation: {str(e)}")

    def _reset_view(self) -> None:
        try:
            self.graphics_view.resetTransform()
            items = self.graphics_scene.items()
            if items:
                rect = self._items_bounding_rect()
                if rect and rect.isValid():
                    self.graphics_view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            else:
                self.graphics_view.centerOn(0, 0)
            self.status_bar.showMessage("Vue réinitialisée")
        except Exception:
            self.status_bar.showMessage("Erreur lors de la réinitialisation de la vue")

    def _items_bounding_rect(self) -> QRectF:
        rect = None
        for it in self.graphics_scene.items():
            br = it.sceneBoundingRect()
            rect = br if rect is None else rect.united(br)
        return rect or QRectF(-100, -100, 200, 200)