"""
Gestion centralisée de la persistance des positions des nœuds et des états des arêtes.
Permet le partage des données entre les différentes couches de l’application (UI, rendu, etc.).
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
        # Implémentation du pattern Singleton pour garantir une instance unique.
        if cls._instance is None:
            cls._instance = super(PositionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # Détermination du dossier de stockage des données :
        # - En mode packagé (PyInstaller) : dossier utilisateur (AppData).
        # - En développement : racine du projet.
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        is_frozen = bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")
        if is_frozen and user_data_dir:
            app_dir = user_data_dir("ManoDiag", "ManoDiag")
            os.makedirs(app_dir, exist_ok=True)
            self.positions_file = os.path.join(app_dir, "node_positions.json")
        else:
            self.positions_file = os.path.join(project_root, "node_positions.json")
        # Positions des nœuds : { nodeId: {x, y, width, height} }
        self.custom_positions: Dict[str, Dict[str, float]] = {}
        # États des arêtes : { edgeKey: { use_bezier, start_offset, end_offset, control1, control2 } }
        self.edge_data: Dict[str, Dict[str, Any]] = {}
        self.load_positions()
        self._initialized = True
    
    # ---------- Utilitaires ----------
    @staticmethod
    def make_edge_key(source: str, target: str, label: str = "", edge_type: str = "arrow") -> str:
        """
        Génère une clé unique pour identifier une arête selon ses paramètres.
        """
        lbl = label or ""
        et = edge_type or "arrow"
        return f"{source}|{target}|{lbl}|{et}"

    # ---------- Persistance ----------
    def save_positions(self):
        """
        Sauvegarde les positions des nœuds et les états des arêtes dans un fichier JSON.
        """
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
        """
        Charge les positions des nœuds et les états des arêtes depuis le fichier JSON.
        """
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
    
    # ---------- Gestion des nœuds ----------
    def update_node_position(self, node_id: str, x: float, y: float, width: float, height: float):
        """
        Met à jour et persiste la position et la taille d’un nœud.
        """
        self.custom_positions[node_id] = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        self.save_positions()
    
    def get_node_position(self, node_id: str) -> Dict[str, float]:
        """
        Retourne la position et la taille d’un nœud donné.
        """
        return self.custom_positions.get(node_id, {})
    
    def has_custom_layout(self) -> bool:
        """
        Indique si un layout personnalisé existe (positions sauvegardées).
        """
        return len(self.custom_positions) > 0
    
    def clear_positions(self):
        """
        Réinitialise toutes les positions des nœuds et états des arêtes.
        """
        self.custom_positions = {}
        self.edge_data = {}
        self.save_positions()

    # ---------- Gestion des arêtes ----------
    def get_edge_data(self, source: str, target: str, label: str = "", edge_type: str = "arrow") -> Dict[str, Any]:
        """
        Retourne l’état persistant d’une arête (Bézier, points de contrôle, etc.).
        """
        key = self.make_edge_key(source, target, label, edge_type)
        return self.edge_data.get(key, {}).copy()

    def set_edge_data(self, source: str, target: str, label: str, edge_type: str, data: Dict[str, Any]):
        """
        Met à jour et persiste l’état d’une arête.
        """
        key = self.make_edge_key(source, target, label, edge_type)
        current = self.edge_data.get(key, {})
        current.update(data or {})
        self.edge_data[key] = current
        self.save_positions()