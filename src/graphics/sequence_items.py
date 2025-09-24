from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QRectF

from ..core.position_manager import PositionManager

class SequenceParticipantItem(QGraphicsRectItem):
    def __init__(self, participant_id: str, label: str, x: float, width: int = 140, header_height: int = 42, lifeline_height: int = 800):
        super().__init__(0, 0, width, header_height)
        self.participant_id = participant_id
        self.label = label
        self.header_height = header_height
        self.lifeline_height = lifeline_height
        self.width = width
        self.setPos(x, 0)
        self.setZValue(5)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setBrush(QBrush(QColor("#f0f6ff")))
        self.setPen(QPen(QColor("#1d5fa2"), 2))
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setDefaultTextColor(QColor("#1d3447"))
        f = QFont("Segoe UI", 9)
        f.setBold(True)
        self.text_item.setFont(f)
        self.text_item.setHtml(f"<div style='text-align:center;padding:4px'>{label}</div>")
        br = self.text_item.boundingRect()
        self.text_item.setPos((self.width - br.width())/2, (self.header_height - br.height())/2)

        # Dépendants (messages / notes) à notifier sur déplacement
        self._dependents: list['SequenceDependentItem'] = []

    def attach_dependent(self, item: 'SequenceDependentItem'):
        if item not in self._dependents:
            self._dependents.append(item)

    def detach_dependent(self, item: 'SequenceDependentItem'):
        if item in self._dependents:
            self._dependents.remove(item)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if isinstance(value, QPointF):
                # Bloquer Y
                if abs(value.y()) > 0.1:
                    return QPointF(value.x(), 0)
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Mise à jour incrémentale des éléments liés
            for dep in self._dependents:
                try:
                    dep.update_geometry()
                except Exception:
                    pass
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Sauvegarde position (X)
            pm = PositionManager()
            pm.update_node_position(self.participant_id, self.pos().x(), 0, self.width, self.header_height)
        super().mouseReleaseEvent(event)

    # --- AJOUT: corriger la zone de mise à jour pour inclure la ligne de vie ---
    def boundingRect(self) -> QRectF:
        # Étend le rect pour couvrir la ligne verticale (évite artefacts / disparition)
        return QRectF(0, 0, self.width, float(self.lifeline_height))

    def shape(self):
        # Zone interactive limitée au header (évite sélection sur toute la hauteur)
        path = QPainterPath()
        path.addRect(0, 0, self.width, self.header_height)
        return path

    def paint(self, painter, option, widget=None):
        # Dessin standard de l’en-tête
        super().paint(painter, option, widget)
        painter.save()
        pen = QPen(QColor("#1d5fa2"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        x_mid = self.width / 2
        # Ligne de vie entière (dans boundingRect désormais)
        painter.drawLine(QPointF(x_mid, self.header_height), QPointF(x_mid, self.lifeline_height))
        painter.restore()


class SequenceDependentItem(QGraphicsItem):
    """
    Interface de base pour messages / notes pour unifier update_geometry().
    (Pas abstraite strictement, mais convention.)
    """
    def update_geometry(self):
        pass


class SequenceMessageItem(SequenceDependentItem):
    def __init__(self, source_item: SequenceParticipantItem, target_item: SequenceParticipantItem, text: str, style: str, y: float):
        super().__init__()
        self.source_item = source_item
        self.target_item = target_item
        self.text = text
        self.style = style  # 'solid', 'dashed', 'async'
        self.y = y
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setDefaultTextColor(QColor("#2c3e50"))
        f = QFont("Segoe UI", 8)
        self.text_item.setFont(f)
        self.text_item.setHtml(f"<div style='background:#ffffffcc;padding:2px 4px;border:1px solid #c9d6e2;border-radius:3px;'>{text}</div>")
        self.setZValue(6)
        self._rect = QRectF(0, 0, 10, 10)
        # Attacher aux participants
        self.source_item.attach_dependent(self)
        self.target_item.attach_dependent(self)
        self.update_geometry()

    def source_center(self) -> QPointF:
        p = self.source_item
        return QPointF(p.pos().x() + p.width/2, p.header_height + 10)

    def target_center(self) -> QPointF:
        p = self.target_item
        return QPointF(p.pos().x() + p.width/2, p.header_height + 10)

    def update_geometry(self):
        old = self._rect
        x1 = self.source_center().x()
        x2 = self.target_center().x()
        if x1 > x2:
            x1, x2 = x2, x1
        new_rect = QRectF(x1 - 40, self.y - 30, (x2 - x1) + 80, 60)
        # Prévenir Qt si changement (évite artefacts)
        if (abs(new_rect.x() - old.x()) > 0.1 or
            abs(new_rect.y() - old.y()) > 0.1 or
            abs(new_rect.width() - old.width()) > 0.1 or
            abs(new_rect.height() - old.height()) > 0.1):
            self.prepareGeometryChange()
            self._rect = new_rect
        # Repositionner le label
        br = self.text_item.boundingRect()
        mid_x = (self.source_center().x() + self.target_center().x())/2 - br.width()/2
        self.text_item.setPos(mid_x, self.y - br.height() - 4)
        self.update()

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter, option, widget=None):
        painter.save()
        x1 = self.source_center().x()
        x2 = self.target_center().x()
        y = self.y
        pen = QPen(QColor("#2d4250"), 2)
        if self.style == 'dashed':
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))

        direction = 1 if x2 >= x1 else -1
        arrow_len = 12
        arrow_w = 6
        # Arrow head
        painter.drawLine(QPointF(x2, y), QPointF(x2 - direction * arrow_len, y - arrow_w))
        painter.drawLine(QPointF(x2, y), QPointF(x2 - direction * arrow_len, y + arrow_w))
        if self.style == 'async':
            painter.drawLine(QPointF(x2 - direction * (arrow_len/2), y),
                             QPointF(x2 - direction * (arrow_len/2) - direction * arrow_len, y - arrow_w))
            painter.drawLine(QPointF(x2 - direction * (arrow_len/2), y),
                             QPointF(x2 - direction * (arrow_len/2) - direction * arrow_len, y + arrow_w))
        painter.restore()

    def remove(self):
        self.source_item.detach_dependent(self)
        self.target_item.detach_dependent(self)
        scene = self.scene()
        if scene:
            scene.removeItem(self)


class SequenceNoteItem(SequenceDependentItem):
    def __init__(self, participant_items: list[SequenceParticipantItem], text: str, y: float):
        super().__init__()
        self.participant_items = participant_items
        self.text = text
        self.y = y
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setDefaultTextColor(QColor("#4a3b00"))
        f = QFont("Segoe UI", 8)
        self.text_item.setFont(f)
        self.text_item.setHtml(f"<div style='padding:4px 6px;'>{text}</div>")
        self.setZValue(4)
        self._rect = QRectF(0, 0, 10, 10)
        for p in self.participant_items:
            p.attach_dependent(self)
        self.update_geometry()

    def _x_span(self):
        xs = [p.pos().x() + p.width/2 for p in self.participant_items]
        if not xs:
            return 0, 0
        return min(xs), max(xs)

    def update_geometry(self):
        old = self._rect
        x1, x2 = self._x_span()
        br = self.text_item.boundingRect()
        w = max(120, (x2 - x1) + 140)
        new_rect = QRectF((x1 + x2)/2 - w/2, self.y, w, br.height() + 14)
        if (abs(new_rect.x() - old.x()) > 0.1 or
            abs(new_rect.y() - old.y()) > 0.1 or
            abs(new_rect.width() - old.width()) > 0.1 or
            abs(new_rect.height() - old.height()) > 0.1):
            self.prepareGeometryChange()
            self._rect = new_rect
        self.text_item.setPos(self._rect.x() + (self._rect.width() - br.width())/2,
                              self._rect.y() + (self._rect.height() - br.height())/2)
        self.update()

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter, option, widget=None):
        painter.save()
        rect = self._rect
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        painter.setBrush(QBrush(QColor("#fff8d2")))
        painter.setPen(QPen(QColor("#c49b00"), 2))
        painter.drawPath(path)
        painter.restore()

    def remove(self):
        for p in self.participant_items:
            p.detach_dependent(self)
        scene = self.scene()
        if scene:
            scene.removeItem(self)