"""
Arêtes interactives avec support de déformation et contrôle par points d'ancrage
"""

from PyQt6.QtWidgets import (QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsTextItem, 
                             QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem)
from PyQt6.QtCore import QRectF, QPointF, Qt, QObject, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPolygonF, QFont, QPainterPath, QCursor, QPainterPathStroker
import math
from ..core.position_manager import PositionManager


class EdgeControlPoint(QGraphicsEllipseItem):
    """Point de contrôle pour déformer les arêtes"""
    
    def __init__(self, edge, point_type: str):
        super().__init__(-6, -6, 12, 12)  # Cercle de 12px
        self.edge = edge
        self.point_type = point_type  # 'start', 'end', 'control1', 'control2'
        
        # Style du point de contrôle
        if point_type in ['start', 'end']:
            # Points d'ancrage - carrés verts
            self.setRect(-5, -5, 10, 10)
            self.setBrush(QBrush(QColor(46, 204, 113)))  # Vert
            self.setPen(QPen(QColor(39, 174, 96), 2))
        else:
            # Points de contrôle - cercles bleus
            self.setBrush(QBrush(QColor(52, 152, 219)))  # Bleu
            self.setPen(QPen(QColor(41, 128, 185), 2))
        
        # Configuration
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                     QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setZValue(150)
        self.setAcceptHoverEvents(True)
        self.setVisible(False)  # Caché par défaut
        
        # État
        self.is_hovered = False
        self.is_moving = False
        self.drag_start_pos = None
    
    def hoverEnterEvent(self, event):
        """Effet de survol"""
        self.is_hovered = True
        self.setScale(1.2)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol"""
        self.is_hovered = False
        self.setScale(1.0)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Début du déplacement"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_moving = True
            self.drag_start_pos = event.scenePos()
            event.accept()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Déplacement du point"""
        if self.is_moving and event.buttons() == Qt.MouseButton.LeftButton:
            current_pos = event.scenePos()
            
            if self.point_type == 'start':
                new_pos = self.edge.constrain_to_node_border(current_pos, self.edge.source_node)
                self.setPos(new_pos)
                self.edge.set_custom_start_point(new_pos)  # persist inside
            elif self.point_type == 'end':
                new_pos = self.edge.constrain_to_node_border(current_pos, self.edge.target_node)
                self.setPos(new_pos)
                self.edge.set_custom_end_point(new_pos)    # persist inside
            else:
                # Points de contrôle libres
                delta = current_pos - self.drag_start_pos
                new_pos = self.pos() + delta
                self.setPos(new_pos)
                self.drag_start_pos = current_pos
                
                if self.point_type == 'control1':
                    self.edge.control_point1 = self.pos()
                elif self.point_type == 'control2':
                    self.edge.control_point2 = self.pos()
                # Persist control points
                self.edge._persist_edge_state()

            # Mettre à jour l'arête
            self.edge.update_position()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Fin du déplacement"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_moving = False
            self.drag_start_pos = None
            event.accept()
        super().mouseReleaseEvent(event)

class ClickablePathItem(QGraphicsPathItem):
    """Path item personnalisé avec zone de clic élargie et gestion de la sélection"""
    
    def __init__(self, parent_edge):
        super().__init__()
        self.parent_edge = parent_edge
        self.click_tolerance = 8  # Pixels de tolérance pour le clic
        
        # Configuration
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def shape(self):
        """Retourne une forme élargie pour faciliter la sélection"""
        if not self.path().elementCount():
            return super().shape()
        
        # Créer un stroke plus large pour la zone de clic
        stroker = QPainterPathStroker()
        stroker.setWidth(self.click_tolerance * 2)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        return stroker.createStroke(self.path())
    
    def hoverEnterEvent(self, event):
        """Effet de survol de l'arête"""
        if not self.parent_edge.is_selected:
            # Surbrillance légère au survol
            pen = QPen(self.parent_edge.line_color.lighter(130), self.parent_edge.line_width + 1)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol de l'arête"""
        if not self.parent_edge.is_selected:
            # Retour au style normal
            pen = QPen(self.parent_edge.line_color, self.parent_edge.line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self.setPen(pen)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Gestion des clics sur l'arête"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_edge.toggle_selection()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Clic droit pour basculer en mode Bézier
            self.parent_edge.toggle_bezier_mode()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def itemChange(self, change, value):
        """Gestion des changements d'état"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Synchroniser avec l'état de sélection de l'arête parente
            if value != self.parent_edge.is_selected:
                # Éviter la récursion en mettant à jour directement
                self.parent_edge.is_selected = value
                self.parent_edge.update_selection_visual()
        
        return super().itemChange(change, value)

class InteractiveArrow(QGraphicsPolygonItem):
    """Flèche interactive déplaçable au simple clic"""
    
    def __init__(self, parent_edge, arrow_type: str = "end"):
        super().__init__()
        self.parent_edge = parent_edge
        self.arrow_type = arrow_type  # "start" ou "end"

        self.setZValue(3)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setAcceptHoverEvents(True)

        # Polygon par défaut (petit triangle) si parent ne fournit pas encore de forme
        try:
            poly = getattr(self.parent_edge, "_arrow_polygon", None)
            if callable(poly):
                self.setPolygon(poly() or QPolygonF([QPointF(0,0), QPointF(-8,3), QPointF(-8,-3)]))
            else:
                self.setPolygon(QPolygonF([QPointF(0,0), QPointF(-8,3), QPointF(-8,-3)]))
        except Exception:
            self.setPolygon(QPolygonF([QPointF(0,0), QPointF(-8,3), QPointF(-8,-3)]))

        self._dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.grabMouse()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            super().mouseMoveEvent(event)  # laisse ItemIsMovable déplacer l’item
            if hasattr(self.parent_edge, "update_position"):
                self.parent_edge.update_position()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.ungrabMouse()
            if hasattr(self.parent_edge, "_persist_edge_state"):
                self.parent_edge._persist_edge_state()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class InteractiveEdge:
    # Variable de classe pour gérer la sélection globale
    _selected_edges = set()
    
    def __init__(self, source_node, target_node, label: str = "", edge_type: str = "arrow"):
        self.source_node = source_node
        self.target_node = target_node
        self.label = label
        self.edge_type = edge_type
        
        # Composants graphiques
        self.path_item = None  # Utiliser un path personnalisé
        self.arrow_items = []
        self.label_item = None
        self.control_points = []
        
        # Points de contrôle pour la courbe de Bézier
        self.custom_start_offset = None  # Offset relatif au nœud source
        self.custom_end_offset = None    # Offset relatif au nœud cible
        self.control_point1 = None
        self.control_point2 = None
        self.use_bezier = False  # Basculer entre ligne droite et courbe
        
        # Style des arêtes
        self.line_color = QColor(52, 73, 94)
        self.line_width = 2
        self.is_selected = False
        
        # Enregistrer cette arête dans les nœuds
        source_node.add_edge(self)
        if target_node != source_node:
            target_node.add_edge(self)

    @classmethod
    def deselect_all_edges(cls):
        """Désélectionne toutes les arêtes"""
        for edge in list(cls._selected_edges):
            edge.set_selected(False)
        cls._selected_edges.clear()
    
    def set_custom_start_point(self, scene_pos: QPointF):
        """Définit un point de départ personnalisé en coordonnées relatives"""
        source_center = self.source_node.boundingRect().center() + self.source_node.pos()
        self.custom_start_offset = QPointF(
            scene_pos.x() - source_center.x(),
            scene_pos.y() - source_center.y()
        )
        self._persist_edge_state()
    
    def set_custom_end_point(self, scene_pos: QPointF):
        """Définit un point d'arrivée personnalisé en coordonnées relatives"""
        target_center = self.target_node.boundingRect().center() + self.target_node.pos()
        self.custom_end_offset = QPointF(
            scene_pos.x() - target_center.x(),
            scene_pos.y() - target_center.y()
        )
        self._persist_edge_state()
    
    def create_graphics_items(self, scene):
        """Crée les éléments graphiques de l'arête"""
        # Path principal personnalisé pour supporter les courbes et améliorer la sélection
        self.path_item = ClickablePathItem(self)
        pen = QPen(self.line_color, self.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.path_item.setPen(pen)
        self.path_item.setZValue(1)
        
        scene.addItem(self.path_item)
        
        # Flèches interactives
        if self.edge_type == "bidirectional":
            # Flèche de fin
            arrow_end = InteractiveArrow(self, "end")
            arrow_end.setBrush(QBrush(self.line_color))
            arrow_end.setPen(QPen(self.line_color))
            scene.addItem(arrow_end)
            self.arrow_items.append(arrow_end)
            
            # Flèche de début
            arrow_start = InteractiveArrow(self, "start")
            arrow_start.setBrush(QBrush(self.line_color))
            arrow_start.setPen(QPen(self.line_color))
            scene.addItem(arrow_start)
            self.arrow_items.append(arrow_start)
        else:
            # Une seule flèche à la fin
            arrow = InteractiveArrow(self, "end")
            arrow.setBrush(QBrush(self.line_color))
            arrow.setPen(QPen(self.line_color))
            scene.addItem(arrow)
            self.arrow_items.append(arrow)
        
        # Label
        if self.label:
            self.label_item = QGraphicsTextItem(self.label)
            font = QFont("Arial", 9)
            font.setWeight(QFont.Weight.Medium)
            self.label_item.setFont(font)
            self.label_item.setDefaultTextColor(self.line_color)
            self.label_item.setHtml(f'<div style="background-color: rgba(255,255,255,180); padding: 2px 4px; border-radius: 3px;">{self.label}</div>')
            self.label_item.setZValue(10)
            scene.addItem(self.label_item)
        
        # Points de contrôle
        self.create_control_points(scene)
        
        # NEW: installer le wrapper de clic une seule fois et corriger isinstance
        if not getattr(scene, "_manodiag_edge_click_wrapper_installed", False):
            original_mouse_press = scene.mousePressEvent

            def enhanced_mouse_press(event):
                view_transform = scene.views()[0].transform() if scene.views() else None
                item = scene.itemAt(event.scenePos(), view_transform)

                interactive_types = (ClickablePathItem, QGraphicsPolygonItem, QGraphicsTextItem, EdgeControlPoint, InteractiveArrow)
                if item is None or not isinstance(item, interactive_types):
                    try:
                        InteractiveEdge.deselect_all_edges()
                    except Exception:
                        pass
                original_mouse_press(event)

            scene.mousePressEvent = enhanced_mouse_press
            scene._manodiag_edge_click_wrapper_installed = True
        
        # Mise à jour initiale
        self.update_position()
        self.apply_saved_state()
        self.update_position()
    
    def create_control_points(self, scene):
        """Crée les points de contrôle"""
        point_types = ['start', 'end', 'control1', 'control2']
        
        for point_type in point_types:
            control_point = EdgeControlPoint(self, point_type)
            scene.addItem(control_point)
            self.control_points.append(control_point)
    
    def toggle_selection(self):
        """Bascule la sélection de l'arête"""
        # Désélectionner toutes les autres arêtes d'abord
        if not self.is_selected:
            self.deselect_all_edges()
        
        self.set_selected(not self.is_selected)
    
    def set_selected(self, selected: bool):
        """Définit l'état de sélection de l'arête"""
        if self.is_selected == selected:
            return
        
        self.is_selected = selected
        
        # Mettre à jour le registre global
        if selected:
            self._selected_edges.add(self)
        else:
            self._selected_edges.discard(self)
        
        # Mettre à jour l'affichage
        self.update_selection_visual()
        
        # Synchroniser avec le path item
        if self.path_item:
            self.path_item.setSelected(selected)
    
    def update_selection_visual(self):
        """Met à jour l'affichage visuel de la sélection"""
        if self.is_selected:
            # Style de sélection
            pen = QPen(QColor(231, 76, 60), self.line_width + 1)  # Rouge plus épais
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self.path_item.setPen(pen)
            
            # Mettre à jour les couleurs des flèches
            for arrow in self.arrow_items:
                arrow.setBrush(QBrush(QColor(231, 76, 60)))
                arrow.setPen(QPen(QColor(231, 76, 60)))
            
            # Afficher les points de contrôle
            self.show_control_points(True)
        else:
            # Style normal
            pen = QPen(self.line_color, self.line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            self.path_item.setPen(pen)
            
            # Restaurer les couleurs des flèches
            for arrow in self.arrow_items:
                arrow.setBrush(QBrush(self.line_color))
                arrow.setPen(QPen(self.line_color))
            
            # Cacher les points de contrôle
            self.show_control_points(False)
    
    def show_control_points(self, visible: bool):
        """Affiche ou cache les points de contrôle"""
        for point in self.control_points:
            point.setVisible(visible)
    
    def toggle_bezier_mode(self):
        """Bascule entre ligne droite et courbe de Bézier"""
        self.use_bezier = not self.use_bezier
        
        if self.use_bezier and (self.control_point1 is None or self.control_point2 is None):
            self.initialize_bezier_points()
        
        self._persist_edge_state()
        self.update_position()
        print(f"Mode Bézier: {'activé' if self.use_bezier else 'désactivé'}")

    def _persist_edge_state(self):
        """Sauvegarde l'état de l'arête dans le PositionManager (offsets/points/bézier)"""
        pm = PositionManager()
        src = self.source_node.node_id
        dst = self.target_node.node_id
        data = {
            "use_bezier": bool(self.use_bezier)
        }
        if self.custom_start_offset is not None:
            data["start_offset"] = [float(self.custom_start_offset.x()), float(self.custom_start_offset.y())]
        if self.custom_end_offset is not None:
            data["end_offset"] = [float(self.custom_end_offset.x()), float(self.custom_end_offset.y())]
        if self.control_point1 is not None:
            data["control1"] = [float(self.control_point1.x()), float(self.control_point1.y())]
        if self.control_point2 is not None:
            data["control2"] = [float(self.control_point2.x()), float(self.control_point2.y())]
        pm.set_edge_data(src, dst, self.label, self.edge_type, data)

    def apply_saved_state(self):
        """Recharge l'état sauvegardé de l'arête (offsets/points/bézier)"""
        pm = PositionManager()
        src = self.source_node.node_id
        dst = self.target_node.node_id
        data = pm.get_edge_data(src, dst, self.label, self.edge_type)
        if not data:
            return
        # Offsets (relatifs aux centres)
        so = data.get("start_offset")
        eo = data.get("end_offset")
        if isinstance(so, (list, tuple)) and len(so) == 2:
            self.custom_start_offset = QPointF(float(so[0]), float(so[1]))
        if isinstance(eo, (list, tuple)) and len(eo) == 2:
            self.custom_end_offset = QPointF(float(eo[0]), float(eo[1]))
        # Bézier
        self.use_bezier = bool(data.get("use_bezier", self.use_bezier))
        c1 = data.get("control1")
        c2 = data.get("control2")
        if isinstance(c1, (list, tuple)) and len(c1) == 2:
            self.control_point1 = QPointF(float(c1[0]), float(c1[1]))
        if isinstance(c2, (list, tuple)) and len(c2) == 2:
            self.control_point2 = QPointF(float(c2[0]), float(c2[1]))

    # ===== New methods =====

    def constrain_to_node_border(self, scene_pos: QPointF, node) -> QPointF:
        """Contraint un point à la bordure du nœud (utilise la logique du nœud)."""
        return node.get_connection_point(scene_pos)

    def _compute_centers(self):
        s_center = self.source_node.boundingRect().center() + self.source_node.pos()
        t_center = self.target_node.boundingRect().center() + self.target_node.pos()
        return s_center, t_center

    def _compute_endpoints(self):
        """Calcule les points de départ/fin sur la bordure (en tenant compte des offsets custom)."""
        s_center, t_center = self._compute_centers()

        if self.custom_start_offset is not None:
            start_pt = QPointF(s_center.x() + self.custom_start_offset.x(),
                               s_center.y() + self.custom_start_offset.y())
        else:
            start_pt = self.source_node.get_connection_point(t_center)

        if self.custom_end_offset is not None:
            end_pt = QPointF(t_center.x() + self.custom_end_offset.x(),
                             t_center.y() + self.custom_end_offset.y())
        else:
            end_pt = self.target_node.get_connection_point(s_center)

        return start_pt, end_pt

    def initialize_bezier_points(self):
        """Initialise des points de contrôle Bézier raisonnables autour de la ligne actuelle."""
        start_pt, end_pt = self._compute_endpoints()
        vx = end_pt.x() - start_pt.x()
        vy = end_pt.y() - start_pt.y()
        # Longueur
        length = math.hypot(vx, vy) or 1.0
        # Vecteur unitaire
        ux, uy = vx / length, vy / length
        # Normale
        nx, ny = -uy, ux
        # Décalages
        along = max(40.0, length * 0.25)
        normal = 40.0
        c1 = QPointF(start_pt.x() + ux * along + nx * normal,
                     start_pt.y() + uy * along + ny * normal)
        c2 = QPointF(end_pt.x() - ux * along + nx * normal,
                     end_pt.y() - uy * along + ny * normal)
        self.control_point1 = c1
        self.control_point2 = c2
        self._persist_edge_state()

    def _update_label_position(self, start_pt: QPointF, end_pt: QPointF):
        if not self.label_item:
            return
        if self.use_bezier and self.control_point1 and self.control_point2:
            # Point au milieu de la courbe (t=0.5)
            t = 0.5
            p0, p1, p2, p3 = start_pt, self.control_point1, self.control_point2, end_pt
            x = (1 - t)**3 * p0.x() + 3 * (1 - t)**2 * t * p1.x() + 3 * (1 - t) * t**2 * p2.x() + t**3 * p3.x()
            y = (1 - t)**3 * p0.y() + 3 * (1 - t)**2 * t * p1.y() + 3 * (1 - t) * t**2 * p2.y() + t**3 * p3.y()
            mid = QPointF(x, y)
        else:
            mid = QPointF((start_pt.x() + end_pt.x()) / 2.0, (start_pt.y() + end_pt.y()) / 2.0)

        br = self.label_item.boundingRect()
        self.label_item.setPos(mid.x() - br.width() / 2.0, mid.y() - br.height() / 2.0)

    def _arrow_polygon(self):
        """Triangle d'arrowhead ancré à l'origine, pointant le long de +X (rotation appliquée ensuite)."""
        length = 14.0
        half_w = 6.0
        return QPolygonF([QPointF(0, 0), QPointF(-length, -half_w), QPointF(-length, half_w)])

    def _update_arrows(self, start_pt: QPointF, end_pt: QPointF):
        if not self.arrow_items:
            return

        # Déterminer les angles (en degrés)
        if self.use_bezier and self.control_point1 and self.control_point2:
            # Tangente à t=1: end - c2 ; tangente à t=0: c1 - start
            end_dx = end_pt.x() - self.control_point2.x()
            end_dy = end_pt.y() - self.control_point2.y()
            start_dx = self.control_point1.x() - start_pt.x()
            start_dy = self.control_point1.y() - start_pt.y()
        else:
            end_dx = end_pt.x() - start_pt.x()
            end_dy = end_pt.y() - start_pt.y()
            start_dx = end_dx
            start_dy = end_dy

        end_angle = math.degrees(math.atan2(end_dy, end_dx))
        # IMPORTANT: la flèche au départ doit pointer dans le sens opposé
        start_angle = math.degrees(math.atan2(start_dy, start_dx)) + 180.0

        # Assurer le bon polygon
        poly = self._arrow_polygon()

        if self.edge_type == "bidirectional" and len(self.arrow_items) == 2:
            end_arrow = self.arrow_items[0]
            start_arrow = self.arrow_items[1]

            end_arrow.setPolygon(poly)
            end_arrow.setPos(end_pt)
            end_arrow.setRotation(end_angle)

            start_arrow.setPolygon(poly)
            start_arrow.setPos(start_pt)
            start_arrow.setRotation(start_angle)
        else:
            end_arrow = self.arrow_items[0]
            end_arrow.setPolygon(poly)
            end_arrow.setPos(end_pt)
            end_arrow.setRotation(end_angle)

    def _update_control_points_items(self, start_pt: QPointF, end_pt: QPointF):
        if not self.control_points:
            return

        # Map types to items in creation order: ['start', 'end', 'control1', 'control2']
        # Ensure the list length matches
        types = ['start', 'end', 'control1', 'control2']
        for i, point_item in enumerate(self.control_points):
            if i >= len(types):
                continue
            t = types[i]
            if t == 'start':
                point_item.setPos(start_pt)
            elif t == 'end':
                point_item.setPos(end_pt)
            elif t == 'control1':
                if self.control_point1 is None:
                    point_item.setPos(QPointF((start_pt.x()*2+end_pt.x())/3.0, (start_pt.y()*2+end_pt.y())/3.0))
                else:
                    point_item.setPos(self.control_point1)
            elif t == 'control2':
                if self.control_point2 is None:
                    point_item.setPos(QPointF((start_pt.x()+end_pt.x()*2)/3.0, (start_pt.y()+end_pt.y()*2)/3.0))
                else:
                    point_item.setPos(self.control_point2)

    def update_position(self):
        """Recalcule le path (ligne ou Bézier), la position des flèches, label et points de contrôle."""
        if not self.path_item:
            return

        start_pt, end_pt = self._compute_endpoints()

        path = QPainterPath()
        path.moveTo(start_pt)

        if self.use_bezier:
            # Initialiser si nécessaire
            if self.control_point1 is None or self.control_point2 is None:
                self.initialize_bezier_points()
            path.cubicTo(self.control_point1, self.control_point2, end_pt)
        else:
            path.lineTo(end_pt)

        self.path_item.setPath(path)

        # Mettre à jour flèches, label, points de contrôle
        self._update_arrows(start_pt, end_pt)
        self._update_label_position(start_pt, end_pt)
        self._update_control_points_items(start_pt, end_pt)

    def remove_from_scene(self, scene):
        """Supprime proprement tous les items graphiques de l'arête."""
        try:
            # Détacher des nœuds
            if self.source_node:
                self.source_node.remove_edge(self)
            if self.target_node and self.target_node is not self.source_node:
                self.target_node.remove_edge(self)

            # Path
            if self.path_item and self.path_item.scene() == scene:
                scene.removeItem(self.path_item)
            self.path_item = None

            # Flèches
            for arrow in self.arrow_items:
                try:
                    if arrow and arrow.scene() == scene:
                        scene.removeItem(arrow)
                except Exception:
                    pass
            self.arrow_items.clear()

            # Label
            if self.label_item and self.label_item.scene() == scene:
                try:
                    scene.removeItem(self.label_item)
                except Exception:
                    pass
            self.label_item = None

            # Points de contrôle
            for cp in self.control_points:
                try:
                    if cp and cp.scene() == scene:
                        scene.removeItem(cp)
                except Exception:
                    pass
            self.control_points.clear()
        except Exception as e:
            # Fallback silencieux
            try:
                self.arrow_items.clear()
                self.control_points.clear()
            except:
                pass
