"""
GridGraphicsView - QGraphicsView avec:
- Grille optionnelle
- Sélection rectangle
- Panoramique (bouton droit en zone vide)
- Zoom (Ctrl + molette)
- Raccourcis: Suppr, Ctrl+A, Échap
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor

class GridGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_grid = True
        self.grid_size = 20

        self.panning = False
        self._pan_start_x = 0.0
        self._pan_start_y = 0.0

        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.ContainsItemShape)

    # --- Souris ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.position().toPoint())
            if item is None:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                self.panning = True
                self._pan_start_x = event.position().x()
                self._pan_start_y = event.position().y()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
            else:
                super().mousePressEvent(event)
        elif event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if item is None:
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            else:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    self.scene().clearSelection()
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning and event.buttons() == Qt.MouseButton.RightButton:
            dx = event.position().x() - self._pan_start_x
            dy = event.position().y() - self._pan_start_y
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(dx))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(dy))
            self._pan_start_x = event.position().x()
            self._pan_start_y = event.position().y()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self.panning:
            self.panning = False
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            if not self.panning:
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.2 if event.angleDelta().y() > 0 else 1.0 / 1.2
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    # --- Clavier ---

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            selected_items = self.scene().selectedItems()
            for item in selected_items:
                if hasattr(item, 'remove_from_scene'):
                    item.remove_from_scene(self.scene())
                else:
                    self.scene().removeItem(item)
        elif event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            from src.graphics.interactive_node import InteractiveNode
            for item in self.scene().items():
                if isinstance(item, InteractiveNode):
                    item.setSelected(True)
        elif event.key() == Qt.Key.Key_Escape:
            self.scene().clearSelection()
        else:
            super().keyPressEvent(event)

    # --- Rendu de la grille ---

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.show_grid:
            return

        painter.setPen(QPen(QColor(220, 220, 220), 1))

        x = int(rect.left() / self.grid_size) * self.grid_size
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self.grid_size

        y = int(rect.top() / self.grid_size) * self.grid_size
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self.grid_size

    def set_grid_visible(self, visible: bool):
        self.show_grid = bool(visible)
        self.viewport().update()