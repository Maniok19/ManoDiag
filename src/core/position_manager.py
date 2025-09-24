"""
Gestionnaire des positions personnalisées des nœuds et des arêtes
"""

import json
import os
from typing import Dict, Any, Tuple
import sys
try:
    from platformdirs import user_data_dir
except Exception:
    user_data_dir = None

class PositionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Singleton pour partager l'état entre MainWindow, Renderer, etc.
        if cls._instance is None:
            cls._instance = super(PositionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # Dossier de données (écrivable) : en binaire -> AppData, en dev -> racine projet
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        is_frozen = bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")
        if is_frozen and user_data_dir:
            app_dir = user_data_dir("ManoDiag", "ManoDiag")
            os.makedirs(app_dir, exist_ok=True)
            self.positions_file = os.path.join(app_dir, "node_positions.json")
        else:
            self.positions_file = os.path.join(project_root, "node_positions.json")
        # Nodes: { nodeId: {x,y,width,height} }
        self.custom_positions: Dict[str, Dict[str, float]] = {}
        # Edges: { edgeKey: { use_bezier, start_offset, end_offset, control1, control2 } }
        self.edge_data: Dict[str, Dict[str, Any]] = {}
        self.load_positions()
        self._initialized = True
    
    # ---------- Helpers ----------
    @staticmethod
    def make_edge_key(source: str, target: str, label: str = "", edge_type: str = "arrow") -> str:
        lbl = label or ""
        et = edge_type or "arrow"
        return f"{source}|{target}|{lbl}|{et}"

    # ---------- Persistence ----------
    def save_positions(self):
        try:
            payload = {
                "nodes": self.custom_positions,
                "edges": self.edge_data
            }
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde positions: {e}")
    
    def load_positions(self):
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and "nodes" not in data and "edges" not in data:
                    self.custom_positions = data
                    self.edge_data = {}
                else:
                    self.custom_positions = data.get("nodes", {}) or {}
                    self.edge_data = data.get("edges", {}) or {}
        except Exception as e:
            print(f"Erreur chargement positions: {e}")
            self.custom_positions = {}
            self.edge_data = {}
    
    # ---------- Nodes ----------
    def update_node_position(self, node_id: str, x: float, y: float, width: float, height: float):
        self.custom_positions[node_id] = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        self.save_positions()
    
    def get_node_position(self, node_id: str) -> Dict[str, float]:
        return self.custom_positions.get(node_id, {})
    
    def has_custom_layout(self) -> bool:
        return len(self.custom_positions) > 0
    
    def clear_positions(self):
        self.custom_positions = {}
        self.edge_data = {}
        self.save_positions()

    # ---------- Edges ----------
    def get_edge_data(self, source: str, target: str, label: str = "", edge_type: str = "arrow") -> Dict[str, Any]:
        key = self.make_edge_key(source, target, label, edge_type)
        return self.edge_data.get(key, {}).copy()

    def set_edge_data(self, source: str, target: str, label: str, edge_type: str, data: Dict[str, Any]):
        key = self.make_edge_key(source, target, label, edge_type)
        current = self.edge_data.get(key, {})
        current.update(data or {})
        self.edge_data[key] = current
        self.save_positions()