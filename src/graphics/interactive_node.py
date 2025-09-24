"""
Nœuds interactifs avec support du drag & drop et redimensionnement
"""

from PyQt6.QtWidgets import (QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, 
                             QInputDialog, QApplication, QGraphicsEllipseItem)
from PyQt6.QtCore import QRectF, QPointF, Qt, QObject, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QCursor
from typing import Optional

class NodeSignalEmitter(QObject):
    """Émetteur de signaux pour les nœuds (séparé car QGraphicsItem ne peut pas émettre de signaux)"""
    position_changed = pyqtSignal(str, float, float, float, float)  # id, x, y, width, height

class ResizeHandle(QGraphicsEllipseItem):
    """Poignée de redimensionnement circulaire professionnelle"""
    def __init__(self, parent_node, handle_type):
        super().__init__(-6, -6, 12, 12)  # Cercle de 12px de diamètre centré
        self.parent_node = parent_node
        self.handle_type = handle_type  # 'se', 'sw', 'ne', 'nw', 'e', 'w', 's', 'n'
        
        # Style professionnel - cercle bleu avec bordure
        self.setBrush(QBrush(QColor(52, 152, 219)))  # Bleu professionnel
        self.setPen(QPen(QColor(41, 128, 185), 2))  # Bordure plus foncée
        
        # IMPORTANT: lier la poignée en tant qu'ENFANT du nœud pour capter le clic immédiatement
        self.setParentItem(self.parent_node)

        # Flags: ignorer les transformations, PAS derrière le parent, pas besoin d'envoyer les changements géométriques
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
        )
        # Capturer explicitement le bouton gauche
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        
        self.setCursor(self.get_cursor())
        
        # Les enfants sont dessinés au-dessus du parent; zValue élevé par sécurité
        self.setZValue(self.parent_node.zValue() + 1)
        
        # Effet de survol
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
        
        # Variables pour le redimensionnement - simplifiées
        self.resize_active = False
        self.last_scene_pos = None
        
        # Initialement caché
        self.setVisible(False)
        
    def get_cursor(self):
        """Retourne le curseur approprié selon le type de poignée"""
        cursors = {
            'se': Qt.CursorShape.SizeFDiagCursor,
            'nw': Qt.CursorShape.SizeFDiagCursor,
            'sw': Qt.CursorShape.SizeBDiagCursor,
            'ne': Qt.CursorShape.SizeBDiagCursor,
            'e': Qt.CursorShape.SizeHorCursor,
            'w': Qt.CursorShape.SizeHorCursor,
            's': Qt.CursorShape.SizeVerCursor,
            'n': Qt.CursorShape.SizeVerCursor
        }
        return cursors.get(self.handle_type, Qt.CursorShape.ArrowCursor)
    
    def hoverEnterEvent(self, event):
        """Effet de survol - agrandir légèrement"""
        self.is_hovered = True
        self.setScale(1.3)
        self.setBrush(QBrush(QColor(52, 152, 219, 220)))  # Plus opaque
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Fin de survol"""
        self.is_hovered = False
        if not self.resize_active:
            self.setScale(1.0)
            self.setBrush(QBrush(QColor(52, 152, 219)))
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Début du redimensionnement - VERSION ULTRA-SIMPLIFIÉE"""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"🎯 Clic sur poignée {self.handle_type}")
            
            # DÉMARRAGE IMMÉDIAT ET FORCÉ
            self.resize_active = True
            self.last_scene_pos = event.scenePos()
            
            # Bloquer IMMÉDIATEMENT la propagation
            event.accept()
            
            # Notifier le parent IMMÉDIATEMENT
            self.parent_node.handle_resize_start(self.handle_type)
            
            # Capturer les événements souris
            self.grabMouse()
            
            print(f"✅ Redimensionnement ACTIVÉ: {self.handle_type}")
            return
        
        # Ignorer tous les autres boutons
        event.ignore()
    
    def mouseMoveEvent(self, event):
        """Redimensionnement en cours - ULTRA-DIRECT"""
        if self.resize_active and self.last_scene_pos is not None:
            current_pos = event.scenePos()
            delta = current_pos - self.last_scene_pos
            
            # Application IMMÉDIATE du redimensionnement
            self.parent_node.handle_resize_move(self.handle_type, delta)
            
            # Mise à jour position de référence
            self.last_scene_pos = current_pos
            
            event.accept()
            return
        
        event.ignore()
    
    def mouseReleaseEvent(self, event):
        """Fin du redimensionnement - NETTOYAGE"""
        if event.button() == Qt.MouseButton.LeftButton and self.resize_active:
            print(f"🔚 Fin redimensionnement {self.handle_type}")
            
            # Arrêt du redimensionnement
            self.resize_active = False
            self.last_scene_pos = None
            
            # Libérer la souris
            self.ungrabMouse()
            
            # Notifier le parent
            self.parent_node.handle_resize_end()
            
            # Restaurer l'apparence
            if not self.is_hovered:
                self.setScale(1.0)
                self.setBrush(QBrush(QColor(52, 152, 219)))
            
            event.accept()
            return
        
        event.ignore()

class InteractiveNode(QGraphicsRectItem):
    def __init__(self, node_id: str, label: str, width: int, height: int, style: dict = None, signal_emitter=None, css_class: Optional[str] = None):
        super().__init__(0, 0, width, height)
        
        self.node_id = node_id
        self.label = label
        self.width = width
        self.height = height
        self.connected_edges = []
        self.signal_emitter = signal_emitter or NodeSignalEmitter()
        self.resize_handles = []
        self.handles_visible = False
        # NEW: mémoriser la classe CSS pour réappliquer les styles
        self.css_class = css_class
        
        # États de redimensionnement et déplacement
        self.resize_in_progress = False
        self.current_resize_handle = None
        self.is_hovered = False
        
        # Variables pour le déplacement groupé
        self.drag_in_progress = False
        self.drag_start_pos = None
        self.selected_nodes_start_positions = {}
        
        # Configuration par défaut - Z-VALUE IMPORTANT
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                     QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                     QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.setZValue(1)  # Nœuds à Z=1, poignées à Z=300
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        
        # Style par défaut
        self.default_style = {
            'fill': '#dcddff',
            'stroke': '#6464c8'
        }
        if style:
            self.default_style.update(style)
        
        self.apply_style(self.default_style)
        
        # Effet de survol
        self.setAcceptHoverEvents(True)
        
        # Texte du nœud
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setZValue(2)  # Texte au-dessus du nœud
        self.update_text()
        
    def apply_style(self, style):
        """Applique le style au nœud en gérant correctement les couleurs"""
        fill_color = QColor(style.get('fill', '#dcddff'))
        stroke_color = QColor(style.get('stroke', '#6464c8'))
        stroke_width = 2
        
        # Parser stroke-width si présent
        if 'stroke-width' in style:
            try:
                stroke_width = int(style['stroke-width'].replace('px', ''))
            except:
                stroke_width = 2
        
        self.setBrush(QBrush(fill_color))
        self.setPen(QPen(stroke_color, stroke_width))
        
        # Sauvegarder pour les effets de survol
        self.default_pen = QPen(stroke_color, stroke_width)
        self.hover_pen = QPen(stroke_color.lighter(120), stroke_width + 1)
    
    def update_style(self, style):
        """Met à jour le style du nœud"""
        self.default_style.update(style)
        self.apply_style(self.default_style)
    
    def update_label(self, new_label):
        """Met à jour le label du nœud"""
        self.label = new_label
        self.update_text()
    
    def create_resize_handles(self):
        """Crée les poignées de redimensionnement - AVEC Z-VALUE CORRIGÉ"""
        if not self.scene() or self.resize_handles:
            return
            
        handle_types = ['se', 'sw', 'ne', 'nw', 'e', 'w', 's', 'n']
        for handle_type in handle_types:
            handle = ResizeHandle(self, handle_type)
            # NE PAS ajouter à la scène: enfant du nœud => ajouté automatiquement
            handle.setZValue(self.zValue() + 1)
            self.resize_handles.append(handle)
            print(f"Poignée créée: {handle_type}, Z-value: {handle.zValue()}")
            
        self.update_handle_positions()
        self.set_handles_visible(False)

    def update_handle_positions(self):
        """Met à jour les positions des poignées"""
        if not self.resize_handles:
            return
            
        rect = self.boundingRect()
        
        # Positions en coordonnées LOCALES (enfant du nœud)
        positions = {
            'nw': (0, 0),
            'n': (rect.width()/2, 0),
            'ne': (rect.width(), 0),
            'e': (rect.width(), rect.height()/2),
            'se': (rect.width(), rect.height()),
            's': (rect.width()/2, rect.height()),
            'sw': (0, rect.height()),
            'w': (0, rect.height()/2)
        }
        
        handle_types = ['se', 'sw', 'ne', 'nw', 'e', 'w', 's', 'n']
        for i, handle in enumerate(self.resize_handles):
            if i < len(handle_types):
                handle_type = handle_types[i]
                if handle_type in positions:
                    handle.setPos(positions[handle_type][0], positions[handle_type][1])
                    handle.setZValue(self.zValue() + 1)

    def set_handles_visible(self, visible):
        """Affiche ou cache les poignées"""
        self.handles_visible = visible
        for handle in self.resize_handles:
            handle.setVisible(visible)
            if visible:
                handle.setZValue(self.zValue() + 1)
    
    def should_show_handles(self):
        """Détermine si les poignées doivent être visibles"""
        return self.isSelected() or self.is_hovered or self.resize_in_progress
    
    def hoverEnterEvent(self, event):
        """Effet de survol"""
        self.is_hovered = True
        if not self.resize_in_progress:
            self.setPen(self.hover_pen)
            # Créer les poignées si elles n'existent pas encore
            if not self.resize_handles:
                self.create_resize_handles()
            self.set_handles_visible(True)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Fin de survol"""
        self.is_hovered = False
        if not self.resize_in_progress:
            self.setPen(self.default_pen)
            # Cacher les poignées seulement si le nœud n'est pas sélectionné
            if not self.should_show_handles():
                self.set_handles_visible(False)
        super().hoverLeaveEvent(event)
    
    def get_selected_nodes(self):
        """Retourne tous les nœuds sélectionnés dans la scène"""
        selected_nodes = []
        if self.scene():
            for item in self.scene().selectedItems():
                if isinstance(item, InteractiveNode):
                    selected_nodes.append(item)
        return selected_nodes

    def mousePressEvent(self, event):
        """Gestion du clic sur le nœud - PROTECTION CONTRE LE REDIMENSIONNEMENT"""
        # Si une poignée gère déjà le redimensionnement, ignorer
        if self.resize_in_progress:
            print("❌ Clic sur nœud ignoré - redimensionnement en cours")
            event.ignore()
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"👆 Clic sur nœud {self.node_id}")
            
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.drag_in_progress = True
            self.drag_start_pos = event.scenePos()
            
            # Gestion de la sélection
            if not self.isSelected() and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.scene().clearSelection()
                self.setSelected(True)
            elif not self.isSelected() and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.setSelected(True)
            
            # Sauvegarder les positions de départ
            self.selected_nodes_start_positions = {}
            selected_nodes = self.get_selected_nodes()
            
            for node in selected_nodes:
                self.selected_nodes_start_positions[node] = node.pos()
                node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
            
            print(f"Début déplacement: {len(selected_nodes)} nœud(s)")
            event.accept()
            
        elif event.button() == Qt.MouseButton.RightButton:
            event.ignore()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Gestion du déplacement - PROTECTION REDIMENSIONNEMENT"""
        # PROTECTION: Si on redimensionne, ne PAS déplacer
        if self.resize_in_progress:
            event.ignore()
            return
            
        if self.drag_in_progress and event.buttons() == Qt.MouseButton.LeftButton:
            current_pos = event.scenePos()
            delta = current_pos - self.drag_start_pos
            
            # Déplacer tous les nœuds sélectionnés
            selected_nodes = self.get_selected_nodes()
            
            for node in selected_nodes:
                if node in self.selected_nodes_start_positions:
                    original_pos = self.selected_nodes_start_positions[node]
                    new_pos = original_pos + delta
                    node.setPos(new_pos)
                    
                    node.update_handle_positions()
                    
                    for edge in node.connected_edges:
                        edge.update_position()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Gestion du relâchement - PROTECTION REDIMENSIONNEMENT"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            
            if self.drag_in_progress:
                self.drag_in_progress = False
                
                # Réactiver les signaux
                selected_nodes = self.get_selected_nodes()
                
                for node in selected_nodes:
                    node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
                    
                    if node.signal_emitter:
                        pos = node.pos()
                        node.signal_emitter.position_changed.emit(
                            node.node_id, pos.x(), pos.y(), node.width, node.height
                        )
                
                print(f"Fin déplacement: {len(selected_nodes)} nœud(s)")
                self.selected_nodes_start_positions = {}
            
            # Réévaluer la visibilité des poignées
            if not self.should_show_handles():
                self.set_handles_visible(False)
            
            super().mouseReleaseEvent(event)
            
        elif event.button() == Qt.MouseButton.RightButton:
            event.ignore()
        else:
            super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """Gère les changements de sélection et position"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if not self.resize_handles:
                self.create_resize_handles()
            
            should_show = self.should_show_handles() if value else self.is_hovered
            self.set_handles_visible(should_show)
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if not self.drag_in_progress and not self.resize_in_progress:
                self.update_handle_positions()
                for edge in self.connected_edges:
                    edge.update_position()
                
                pos = self.pos()
                if self.signal_emitter:
                    self.signal_emitter.position_changed.emit(self.node_id, pos.x(), pos.y(), self.width, self.height)
        
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            if self.scene() and not self.resize_handles:
                self.create_resize_handles()
        
        return super().itemChange(change, value)
    
    # NOUVELLES MÉTHODES POUR GÉRER LE REDIMENSIONNEMENT
    def handle_resize_start(self, handle_type):
        """Démarre le redimensionnement depuis une poignée"""
        print(f"🔧 REDIMENSIONNEMENT DÉMARRÉ: {self.node_id} via {handle_type}")
        self.resize_in_progress = True
        self.current_resize_handle = handle_type
        
        # DÉSACTIVER le déplacement du nœud
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
        # Forcer l'affichage des poignées
        self.set_handles_visible(True)
    
    def handle_resize_move(self, handle_type, delta):
        """Redimensionnement en cours depuis une poignée"""
        if not self.resize_in_progress or handle_type != self.current_resize_handle:
            return
            
        min_size = 50
        
        new_width = self.width
        new_height = self.height
        new_x = self.pos().x()
        new_y = self.pos().y()
        
        # Appliquer le redimensionnement selon la poignée
        if 'e' in handle_type:  # Poignées contenant 'e' (est)
            new_width = max(min_size, self.width + delta.x())
        elif 'w' in handle_type:  # Poignées contenant 'w' (ouest)
            potential_width = self.width - delta.x()
            if potential_width >= min_size:
                new_width = potential_width
                new_x = self.pos().x() + delta.x()
        
        if 's' in handle_type:  # Poignées contenant 's' (sud)
            new_height = max(min_size, self.height + delta.y())
        elif 'n' in handle_type:  # Poignées contenant 'n' (nord)
            potential_height = self.height - delta.y()
            if potential_height >= min_size:
                new_height = potential_height
                new_y = self.pos().y() + delta.y()
        
        # Appliquer les changements
        self.width = new_width
        self.height = new_height
        self.setRect(0, 0, new_width, new_height)
        self.setPos(new_x, new_y)
        
        # Mettre à jour
        self.update_text()
        self.update_handle_positions()
        
        # Mettre à jour les arêtes connectées
        for edge in self.connected_edges:
            edge.update_position()
        
        # Émettre le signal de changement
        if self.signal_emitter:
            self.signal_emitter.position_changed.emit(self.node_id, new_x, new_y, new_width, new_height)
    
    def handle_resize_end(self):
        """Termine le redimensionnement"""
        print(f"✅ REDIMENSIONNEMENT TERMINÉ: {self.node_id}")
        self.resize_in_progress = False
        self.current_resize_handle = None
        
        # RÉACTIVER le déplacement du nœud
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        
        # Réévaluer la visibilité des poignées
        if not self.should_show_handles():
            self.set_handles_visible(False)
        
    def update_text(self):
        """Met à jour le texte du nœud"""
        html_text = self.convert_to_html(self.label)
        self.text_item.setHtml(html_text)
        
        text_rect = self.text_item.boundingRect()
        text_x = (self.width - text_rect.width()) / 2
        text_y = (self.height - text_rect.height()) / 2
        self.text_item.setPos(text_x, text_y)
        
        self.text_item.setZValue(2)  # Texte au-dessus du nœud
    
    def convert_to_html(self, text: str) -> str:
        """Convertit le texte avec marquage Mermaid en HTML"""
        text = text.strip('"')
        text = text.replace('<b>', '<b>').replace('</b>', '</b>')
        text = text.replace('\\n', '<br>')
        return f'<div style="text-align: center; font-size: 10pt; color: #2c3e50; font-weight: 500;">{text}</div>'
    
    def get_connection_point(self, target_pos: QPointF) -> QPointF:
        """Retourne le point de connexion optimal vers une position cible"""
        center = self.boundingRect().center() + self.pos()
        
        dx = target_pos.x() - center.x()
        dy = target_pos.y() - center.y()
        
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            return center
        
        half_width = self.width / 2
        half_height = self.height / 2
        
        if abs(dx) > abs(dy):  # Connexion horizontale dominante
            if dx > 0:  # Droite
                if dy != 0:
                    y_intersect = center.y() + (half_width / dx) * dy
                    if abs(y_intersect - center.y()) <= half_height:
                        return QPointF(self.pos().x() + self.width, y_intersect)
                
                return QPointF(self.pos().x() + self.width, 
                              center.y() + (half_height if dy > 0 else -half_height))
            else:  # Gauche
                if dy != 0:
                    y_intersect = center.y() + (-half_width / dx) * dy
                    if abs(y_intersect - center.y()) <= half_height:
                        return QPointF(self.pos().x(), y_intersect)
                
                return QPointF(self.pos().x(), 
                              center.y() + (half_height if dy > 0 else -half_height))
        else:  # Connexion verticale dominante
            if dy > 0:  # Bas
                if dx != 0:
                    x_intersect = center.x() + (half_height / dy) * dx
                    if abs(x_intersect - center.x()) <= half_width:
                        return QPointF(x_intersect, self.pos().y() + self.height)
                
                return QPointF(center.x() + (half_width if dx > 0 else -half_width),
                              self.pos().y() + self.height)
            else:  # Haut
                if dx != 0:
                    x_intersect = center.x() + (-half_height / dy) * dx
                    if abs(x_intersect - center.x()) <= half_width:
                        return QPointF(x_intersect, self.pos().y())
                
                return QPointF(center.x() + (half_width if dx > 0 else -half_width),
                              self.pos().y())
        
        return center

    def add_edge(self, edge):
        """Ajoute une arête connectée à ce nœud"""
        if edge not in self.connected_edges:
            self.connected_edges.append(edge)
    
    def remove_edge(self, edge):
        """Supprime une arête connectée à ce nœud"""
        if edge in self.connected_edges:
            self.connected_edges.remove(edge)
    
    def paint(self, painter, option, widget):
        """Rendu personnalisé du nœud avec bordures arrondies"""
        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        
        rect = self.boundingRect()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, 8, 8)
        
        painter.restore()

    def set_size(self, width: int, height: int):
        """Change la taille du nœud et met à jour le contenu/poignées/arrêtes/sauvegarde."""
        try:
            width = max(1, int(width))
            height = max(1, int(height))
        except Exception:
            pass
        self.width = width
        self.height = height
        self.setRect(0, 0, width, height)
        # Recentrer le texte/rafraîchir
        self.update_text()
        # Mettre à jour les poignées (si existantes)
        try:
            self.update_handle_positions()
        except Exception:
            pass
        # Mettre à jour les arêtes connectées
        for edge in getattr(self, "connected_edges", []) or []:
            try:
                edge.update_position()
            except Exception:
                pass
        # Émettre la position/taille courante
        if self.signal_emitter:
            p = self.pos()
            self.signal_emitter.position_changed.emit(self.node_id, p.x(), p.y(), self.width, self.height)

    def size_to_fit_content(self, padding: int = 16, min_size: tuple[int, int] = (80, 48)) -> tuple[int, int]:
        """Calcule une taille qui enveloppe le texte avec un padding, sans appliquer."""
        try:
            # Forcer une mise à jour du texte pour avoir un boundingRect à jour
            self.update_text()
            br = self.text_item.boundingRect()
            pad = max(0, int(padding))
            w = int(br.width()) + pad * 2
            h = int(br.height()) + pad * 2
            w = max(int(min_size[0]), w)
            h = max(int(min_size[1]), h)
            return (w, h)
        except Exception:
            # Valeur sûre
            return (max(int(min_size[0]), self.width), max(int(min_size[1]), self.height))