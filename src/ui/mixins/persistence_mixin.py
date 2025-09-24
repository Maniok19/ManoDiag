import json
import os
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtCore import QRectF, QMarginsF
from src.core.position_manager import PositionManager

class PersistenceMixin:
    def _qcolor_to_hex(self, color: QColor) -> str:
        return color.name()

    def _ensure_fixed_layout_config(self, text: str) -> str:
        stripped = text.lstrip()
        if stripped.lower().startswith("sequence"):
            return text
        if "layout: fixed" in text:
            return text
        if stripped.startswith('---'):
            # Un bloc YAML existe déjà: on l'insère si absent
            parts = stripped.split('---')
            if len(parts) >= 3 and "layout:" not in parts[1]:
                parts[1] = parts[1].strip() + "\nlayout: fixed\n"
                return '---'.join(parts)
            return text
        return """---
layout: fixed
---

""" + text

    def _remove_top_yaml_block(self, text: str) -> str:
        lines = text.splitlines()
        if len(lines) < 3:
            return text
        if lines[0].strip() == '---':
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    return '\n'.join(lines[i+1:])
        return text

    def _save_diagram(self) -> None:
        pm = PositionManager()
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder", "", "ManoDiag (*.manodiag.json)")
        if not path:
            return
        payload = {
            "text": self.text_editor.toPlainText(),
            "nodes": pm.custom_positions,
            "edges": pm.edge_data,
            "settings": {
                "show_grid": bool(self.current_settings.get("show_grid", True)),
                "antialiasing": bool(self.current_settings.get("antialiasing", True)),
                "node_color": self._qcolor_to_hex(self.current_settings.get("node_color")),
                "border_color": self._qcolor_to_hex(self.current_settings.get("border_color")),
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        self.status_bar.showMessage("Diagramme sauvegardé")

    def _open_diagram(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir", "", "ManoDiag (*.manodiag.json)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("text", "")
        self.text_editor.setPlainText(text)
        pm = PositionManager()
        pm.custom_positions = data.get("nodes", {}) or {}
        pm.edge_data = data.get("edges", {}) or {}
        pm.save_positions()
        st = data.get("settings", {}) or {}
        from PyQt6.QtGui import QColor
        self.current_settings = {
            "show_grid": st.get("show_grid", True),
            "antialiasing": st.get("antialiasing", True),
            "node_color": QColor(st.get("node_color", "#dcddff")),
            "border_color": QColor(st.get("border_color", "#6464c8")),
        }
        self._apply_settings(self.current_settings)
        self._render_diagram()
        self.status_bar.showMessage("Diagramme chargé")

    def _export_png(self) -> None:
        items = self.graphics_scene.items()
        if not items:
            self.status_bar.showMessage("Rien à exporter")
            return
        rect = self._items_bounding_rect()
        margin = 24
        target = rect.marginsAdded(QMarginsF(margin, margin, margin, margin))
        img = QImage(int(target.width()), int(target.height()), QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)
        self.graphics_view.render(painter, target=QRectF(0, 0, target.width(), target.height()),
                                  source=target)
        painter.end()
        path, _ = QFileDialog.getSaveFileName(self, "Exporter en PNG", "", "Images (*.png)")
        if not path:
            return
        img.save(path, "PNG")
        self.status_bar.showMessage("Export PNG terminé")

    def _reset_positions(self) -> None:
        pm = PositionManager()
        pm.clear_positions()
        self._render_diagram()
        self.status_bar.showMessage("Positions réinitialisées")