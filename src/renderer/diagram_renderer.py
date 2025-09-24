"""
Moteur de rendu graphique pour diagrammes interactifs (flowchart et séquence).
- Gère l'affichage, la mise à jour et l'interaction des éléments du diagramme.
- Prend en charge la persistance des positions et des styles.
- Optimise le recyclage des items pour un rendu fluide et incrémental.
"""

from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import QRectF, QPointF, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
from typing import Dict, List, Any, Tuple
import math

from ..parser.diagram_parser import Node, Edge
from ..graphics.interactive_node import InteractiveNode, NodeSignalEmitter
from ..graphics.interactive_edge import InteractiveEdge
from ..core.position_manager import PositionManager
from ..graphics.sequence_items import SequenceParticipantItem, SequenceMessageItem, SequenceNoteItem

class DiagramRenderer(QObject):
    """
    Moteur de rendu principal pour les diagrammes.
    - Supporte les signaux pour interaction et mise à jour.
    - Gère les paramètres de style et de layout.
    - Optimise la réutilisation des items graphiques.
    """
    
    def __init__(self):
        super().__init__()
        # Paramètres de style par défaut
        self.node_color = QColor(220, 221, 255)
        self.border_color = QColor(100, 100, 200)
        
        # Paramètres de layout
        self.node_width = 160
        self.node_height = 60
        self.node_spacing_x = 220
        self.node_spacing_y = 120
        self.layout_type = 'auto'
        self.direction = 'TD'
        
        # Gestion des signaux pour les nœuds interactifs
        self.signal_emitter = NodeSignalEmitter()
        self.signal_emitter.position_changed.connect(self.on_node_position_changed)
        
        # Caches pour les items graphiques existants
        self.existing_nodes = {}
        self.existing_edges = []
        self.all_control_points = []
        self.last_class_defs = {}
        self._current_mode = 'flowchart'
        self.sequence_participants_items = {}
        self.sequence_message_items = []
        self.sequence_note_items = []
        self._seq_messages_by_key = {}
        self._seq_notes_by_key = {}
        self._sequence_title_item = None
        self._last_sequence_sig: tuple[str, ...] = ()
    
    def clear_scene_completely(self, scene: QGraphicsScene):
        """
        Nettoie intégralement la scène graphique et réinitialise les caches.
        """
        try:
            scene.clear()
            self.existing_nodes = {}
            self.existing_edges = []
            self.all_control_points = []
            self.sequence_participants_items = {}
            self.sequence_message_items = []
            self.sequence_note_items = []
            self._current_mode = 'flowchart'
        except Exception as e:
            print(f"[Renderer] clear_scene_completely error: {e}")
    
    def update_settings(self, settings: Dict[str, Any]):
        """
        Met à jour les paramètres de style du rendu.
        - Applique les nouveaux styles aux nœuds existants.
        - Nettoie les références obsolètes.
        """
        self.node_color = settings.get('node_color', QColor(220, 221, 255))
        self.border_color = settings.get('border_color', QColor(100, 100, 200))
        for nid, node in list(self.existing_nodes.items()):
            try:
                if node.scene() is None:
                    self.existing_nodes.pop(nid, None)
                    continue
                base = {'fill': self.node_color.name(), 'stroke': self.border_color.name()}
                css_class = getattr(node, 'css_class', None)
                styled = {**base, **self.last_class_defs.get(css_class, {})} if css_class else base
                if hasattr(node, 'update_style'):
                    node.update_style(styled)
            except RuntimeError:
                self.existing_nodes.pop(nid, None)
            except Exception:
                pass
        
    def render_sequence(self, data: Dict[str, Any], scene: QGraphicsScene):
        """
        Rendu incrémental d'un diagramme de séquence.
        - Gère participants, messages, notes et titre.
        - Optimise la réutilisation des items pour éviter les scintillements.
        - Persiste les positions des participants.
        """
        participants = data.get('participants', [])
        new_sig = tuple(p.id for p in participants)

        if self._current_mode != 'sequence' or (self._current_mode == 'sequence' and self._last_sequence_sig and self._last_sequence_sig != new_sig):
            try:
                scene.clear()
            except Exception:
                pass
            self.existing_nodes.clear()
            self.existing_edges.clear()
            self.all_control_points.clear()
            self.sequence_participants_items = {}
            self._seq_messages_by_key = {}
            self._seq_notes_by_key = {}
            self._sequence_title_item = None
            self._current_mode = 'sequence'

        self._current_mode = 'sequence'

        messages = data.get('messages', [])
        notes = data.get('notes', [])
        title = data.get('title', "")
        cfg = data.get('config', {}) or {}

        spacing_x = cfg.get('participant_spacing', 220)
        header_h = 42
        lifeline_h = 1000
        pm = PositionManager()

        # Participants : création et mise à jour
        wanted_ids = [p.id for p in participants]
        for pid in list(self.sequence_participants_items.keys()):
            if pid not in wanted_ids:
                try:
                    scene.removeItem(self.sequence_participants_items[pid])
                except Exception:
                    pass
                self.sequence_participants_items.pop(pid, None)

        for idx, p in enumerate(participants):
            saved = pm.get_node_position(p.id)
            x = saved.get('x', idx * spacing_x)
            w = int(saved.get('width', 140))
            if p.id in self.sequence_participants_items:
                item = self.sequence_participants_items[p.id]
                if abs(item.pos().x() - x) > 0.1:
                    item.setPos(float(x), 0.0)
                if item.label != p.label:
                    item.label = p.label
                    item.text_item.setHtml(f"<div style='text-align:center;padding:4px'>{p.label}</div>")
                if w != item.width:
                    item.width = w
                    item.setRect(0, 0, w, header_h)
            else:
                item = SequenceParticipantItem(
                    p.id,
                    p.label,
                    float(x),
                    width=w,
                    header_height=header_h,
                    lifeline_height=lifeline_h
                )
                scene.addItem(item)
                self.sequence_participants_items[p.id] = item

        # Messages : création, mise à jour et suppression
        used_message_keys = set()
        base_y = 120
        step_y = 70
        for i, msg in enumerate(messages):
            s_item = self.sequence_participants_items.get(msg.source)
            t_item = self.sequence_participants_items.get(msg.target)
            if not s_item or not t_item:
                continue
            y = base_y + i * step_y
            key = f"{i}|{msg.source}|{msg.target}|{msg.text}|{msg.style}"
            used_message_keys.add(key)
            if key in self._seq_messages_by_key:
                mi = self._seq_messages_by_key[key]
                if mi.text != msg.text or mi.style != msg.style or abs(mi.y - y) > 0.1:
                    mi.text = msg.text
                    mi.style = msg.style
                    mi.y = y
                    mi.text_item.setHtml(f"<div style='background:#ffffffcc;padding:2px 4px;border:1px solid #c9d6e2;border-radius:3px;'>{msg.text}</div>")
                    mi.update_geometry()
                else:
                    mi.update_geometry()
            else:
                mi = SequenceMessageItem(s_item, t_item, msg.text, msg.style, y)
                scene.addItem(mi)
                self._seq_messages_by_key[key] = mi

        for k in list(self._seq_messages_by_key.keys()):
            if k not in used_message_keys:
                try:
                    self._seq_messages_by_key[k].remove()
                except Exception:
                    pass
                self._seq_messages_by_key.pop(k, None)

        # Notes : création, mise à jour et suppression
        used_note_keys = set()
        if notes:
            y_notes_start = base_y + len(messages) * step_y + 50
            for j, note in enumerate(notes):
                parts_items = [self.sequence_participants_items.get(pid) for pid in note.participants if self.sequence_participants_items.get(pid)]
                if not parts_items:
                    continue
                y = y_notes_start + j * 80
                key = f"{j}|{'&'.join(sorted(note.participants))}|{note.text}"
                used_note_keys.add(key)
                if key in self._seq_notes_by_key:
                    ni = self._seq_notes_by_key[key]
                    if ni.text != note.text or abs(ni.y - y) > 0.1:
                        ni.text = note.text
                        ni.y = y
                        ni.text_item.setHtml(f"<div style='padding:4px 6px;'>{note.text}</div>")
                        ni.update_geometry()
                    else:
                        ni.update_geometry()
                else:
                    ni = SequenceNoteItem(parts_items, note.text, y)
                    scene.addItem(ni)
                    self._seq_notes_by_key[key] = ni

        for k in list(self._seq_notes_by_key.keys()):
            if k not in used_note_keys:
                try:
                    self._seq_notes_by_key[k].remove()
                except Exception:
                    pass
                self._seq_notes_by_key.pop(k, None)

        # Titre du diagramme : création, mise à jour ou suppression
        if title:
            if not self._sequence_title_item:
                from PyQt6.QtWidgets import QGraphicsTextItem
                self._sequence_title_item = QGraphicsTextItem()
                self._sequence_title_item.setZValue(20)
                scene.addItem(self._sequence_title_item)
            self._sequence_title_item.setHtml(
                f"<div style='font-size:18px;font-weight:600;color:#1d3447;font-family:Segoe UI;'>{title}</div>"
            )
            br = self._sequence_title_item.boundingRect()
            xs = [it.pos().x() + it.width/2 for it in self.sequence_participants_items.values()]
            cx = (min(xs) + max(xs))/2 if xs else 0
            self._sequence_title_item.setPos(cx - br.width()/2, 8)
        else:
            if self._sequence_title_item:
                try:
                    scene.removeItem(self._sequence_title_item)
                except Exception:
                    pass
                self._sequence_title_item = None

        # Persistance des positions des participants
        try:
            for pid, it in self.sequence_participants_items.items():
                pm.custom_positions[pid] = {
                    'x': float(it.pos().x()),
                    'y': 0.0,
                    'width': float(it.width),
                    'height': float(it.header_height)
                }
            pm.save_positions()
        except Exception:
            pass

        scene._sequence_message_items = list(self._seq_messages_by_key.values())
        scene._sequence_note_items = list(self._seq_notes_by_key.values())

        self._last_sequence_sig = new_sig
    
    def on_node_position_changed(self, node_id: str, x: float, y: float, w: float, h: float):
        """
        Callback appelé lors du déplacement ou redimensionnement d'un nœud interactif.
        - Met à jour la position dans PositionManager.
        - Met à jour les arêtes connectées.
        """
        try:
            pm = PositionManager()
            pm.update_node_position(node_id, x, y, w, h)
        except Exception as e:
            print(f"[Renderer] on_node_position_changed error: {e}")
        try:
            node = self.existing_nodes.get(node_id)
            if node:
                for edge in getattr(node, "connected_edges", []) or []:
                    try:
                        edge.update_position()
                    except Exception:
                        pass
        except Exception:
            pass

    def render_flowchart(self, data: Dict[str, Any], scene: QGraphicsScene):
        """
        Rendu incrémental d’un diagramme de type flowchart.
        - Réutilise les nœuds et arêtes existants.
        - Respecte les positions sauvegardées si layout: fixed.
        - Applique les styles classDef.
        """
        from ..graphics.interactive_node import InteractiveNode
        from ..graphics.interactive_edge import InteractiveEdge
        from ..core.position_manager import PositionManager

        if self._current_mode != 'flowchart':
            self.clear_scene_completely(scene)
            self._current_mode = 'flowchart'

        pm = PositionManager()
        config = data.get('config', {}) or {}
        class_defs = data.get('class_defs', {}) or {}
        nodes_spec = data.get('nodes', []) or []
        edges_spec = data.get('edges', []) or []
        direction = data.get('direction', 'TD')
        self.direction = direction
        self.last_class_defs = class_defs

        layout_fixed = str(config.get('layout', '')).lower() == 'fixed'
        auto_layout = not layout_fixed

        # Gestion des nœuds : création, mise à jour, suppression
        wanted_ids = [n.id for n in nodes_spec]
        for nid in list(self.existing_nodes.keys()):
            if nid not in wanted_ids:
                try:
                    node = self.existing_nodes[nid]
                    for edge in list(getattr(node, 'connected_edges', [])):
                        try:
                            edge.remove_from_scene(scene)
                            if edge in self.existing_edges:
                                self.existing_edges.remove(edge)
                        except Exception:
                            pass
                    if node.scene() == scene:
                        scene.removeItem(node)
                except Exception:
                    pass
                self.existing_nodes.pop(nid, None)

        base_x = 0
        base_y = 0
        col = 0
        row = 0
        max_per_row = 4
        spacing_x = self.node_spacing_x
        spacing_y = self.node_spacing_y

        def next_auto_pos(index: int) -> Tuple[float, float]:
            nonlocal col, row
            if direction in ('LR', 'RL'):
                x = base_x + index * spacing_x
                y = base_y
            else:
                if col >= max_per_row:
                    col = 0
                    row += 1
                x = base_x + col * spacing_x
                y = base_y + row * spacing_y
                col += 1
            return (x, y)

        for idx, spec in enumerate(nodes_spec):
            nid = spec.id
            label = spec.label
            css_class = getattr(spec, 'css_class', None)

            node_item = self.existing_nodes.get(nid)
            if node_item is None:
                saved = pm.get_node_position(nid)
                if saved:
                    x = saved.get('x', 0)
                    y = saved.get('y', 0)
                    w = int(saved.get('width', self.node_width))
                    h = int(saved.get('height', self.node_height))
                else:
                    if auto_layout:
                        x, y = next_auto_pos(idx)
                    else:
                        x, y = next_auto_pos(idx)
                    w = self.node_width
                    h = self.node_height

                style_base = {
                    'fill': self.node_color.name(),
                    'stroke': self.border_color.name()
                }
                if css_class and css_class in class_defs:
                    style_base.update(class_defs[css_class])

                node_item = InteractiveNode(
                    nid,
                    label,
                    w,
                    h,
                    style=style_base,
                    signal_emitter=self.signal_emitter,
                    css_class=css_class
                )
                scene.addItem(node_item)
                node_item.setPos(x, y)
                self.existing_nodes[nid] = node_item
            else:
                if node_item.label != label:
                    node_item.update_label(label)
                if css_class != getattr(node_item, 'css_class', None):
                    node_item.css_class = css_class
                style_base = {
                    'fill': self.node_color.name(),
                    'stroke': self.border_color.name()
                }
                if node_item.css_class and node_item.css_class in class_defs:
                    style_base.update(class_defs[node_item.css_class])
                node_item.update_style(style_base)

        # Gestion des arêtes : création, mise à jour, suppression
        edge_map = {}
        for e in self.existing_edges:
            key = (e.source_node.node_id, e.target_node.node_id, getattr(e, 'label', ''), getattr(e, 'edge_type', 'arrow'))
            edge_map[key] = e

        needed_keys = set()
        new_edge_objects = []

        for es in edges_spec:
            key = (es.source, es.target, es.label, es.edge_type)
            needed_keys.add(key)
            if key in edge_map:
                continue
            src_node = self.existing_nodes.get(es.source)
            tgt_node = self.existing_nodes.get(es.target)
            if not src_node or not tgt_node:
                continue
            edge_item = InteractiveEdge(src_node, tgt_node, es.label, es.edge_type)
            edge_item.create_graphics_items(scene)
            new_edge_objects.append(edge_item)

        for key, edge_item in list(edge_map.items()):
            if key not in needed_keys:
                try:
                    edge_item.remove_from_scene(scene)
                except Exception:
                    pass
                if edge_item in self.existing_edges:
                    self.existing_edges.remove(edge_item)

        self.existing_edges.extend(new_edge_objects)

        for e in new_edge_objects:
            try:
                e.update_position()
            except Exception:
                pass

    def normalize_layout(self, scene: QGraphicsScene, direction: str | None = None):
        """
        Ajuste la taille des nœuds à leur contenu et aligne leur position sur une grille.
        - Met à jour la position et la taille de chaque nœud.
        - Met à jour la position des arêtes associées.
        """
        grid = 20
        for node in self.existing_nodes.values():
            try:
                w, h = node.size_to_fit_content()
                node.set_size(w, h)
                p = node.pos()
                gx = round(p.x() / grid) * grid
                gy = round(p.y() / grid) * grid
                if abs(gx - p.x()) > 0.1 or abs(gy - p.y()) > 0.1:
                    node.setPos(gx, gy)
            except Exception:
                pass
        for edge in self.existing_edges:
            try:
                edge.update_position()
            except Exception:
                pass