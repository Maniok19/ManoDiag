"""
DiagramParser : Analyseur avancé pour la syntaxe Mermaid (flowchart et séquence).
- Prend en charge la configuration YAML en tête de fichier.
- Gère les nœuds, arêtes, classes, et diagrammes de séquence.
- Retourne une structure de données prête pour le rendu graphique.
"""

import re
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Node:
    """
    Représente un nœud du diagramme.
    - id : identifiant unique
    - label : texte affiché
    - node_type : type graphique (ex: 'rect')
    - properties : propriétés additionnelles
    - css_class : classe CSS optionnelle
    """
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    css_class: Optional[str] = None

@dataclass
class Edge:
    """
    Représente une arête entre deux nœuds.
    - source : id du nœud source
    - target : id du nœud cible
    - label : texte de l’arête
    - edge_type : type ('arrow', 'bidirectional')
    - style : style graphique ('solid', ...)
    """
    source: str
    target: str
    label: str = ""
    edge_type: str = "arrow"
    style: str = "solid"

@dataclass
class SequenceParticipant:
    """
    Participant d’un diagramme de séquence.
    - id : identifiant
    - label : affichage
    """
    id: str
    label: str

@dataclass
class SequenceMessage:
    """
    Message échangé dans une séquence.
    - source : participant émetteur
    - target : participant destinataire
    - text : contenu du message
    - style : type de flèche ('solid', 'dashed', 'async')
    """
    source: str
    target: str
    text: str
    style: str  # solid | dashed | async

@dataclass
class SequenceNote:
    """
    Note associée à un ou plusieurs participants.
    - participants : liste d’identifiants
    - text : contenu de la note
    """
    participants: list[str]
    text: str

class DiagramParser:
    """
    Analyseur principal pour les diagrammes Mermaid-like.
    - Détecte et extrait la configuration YAML.
    - Identifie le type de diagramme (flowchart ou séquence).
    - Parse les nœuds, arêtes, classes, participants, messages et notes.
    - Retourne une structure dict prête à être exploitée par le renderer.
    """
    def __init__(self):
        # Expressions régulières pour la détection des éléments Mermaid
        self.patterns = {
            'config_block': re.compile(r'---\s*\n(.*?)\n---', re.DOTALL),
            'flowchart_direction': re.compile(r'flowchart\s+(TD|TB|BT|RL|LR)'),
            'node_with_quotes': re.compile(r'(\w+)\["([^"]+)"\]'),
            'node_with_brackets': re.compile(r'(\w+)\[([^\]]+)\]'),
            'edge_bidirectional': re.compile(r'(\w+)\s*<-->\s*(\w+)'),
            'edge_with_label': re.compile(r'(\w+)\s*--\s*([^-]+)\s*-->\s*(\w+)'),
            'edge_simple': re.compile(r'(\w+)\s*-->\s*(\w+)'),
            'edge_multiple': re.compile(r'(\w+)\s*-->\s*([^&\n]+(?:\s*&\s*[^&\n]+)+)'),
            'class_def': re.compile(r'classDef\s+(\w+)\s+(.+)'),
            'class_assign': re.compile(r'(\w+):::(\w+)'),
        }
        self.sequence_patterns = {
            'title': re.compile(r'^title\s+(.+)$', re.IGNORECASE),
            'participant': re.compile(r'^participant\s+(\w+)(?:\s+as\s+(.+))?$', re.IGNORECASE),
            'message': re.compile(r'^(\w+)\s*([-]{1,2}>{1,2})\s*(\w+)\s*:\s*(.+)$'),
            'note_over': re.compile(r'^note\s+over\s+([\w,\s]+):\s*(.+)$', re.IGNORECASE),
        }
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Point d’entrée principal.
        - Extrait la configuration YAML.
        - Détermine le type de diagramme.
        - Retourne la structure du diagramme.
        """
        config, diagram_text = self.extract_config(text)
        lines = [line.strip() for line in diagram_text.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        stripped = [l for l in diagram_text.splitlines() if l.strip()]
        if stripped and stripped[0].strip().lower().startswith("sequence"):
            return self.parse_sequence(stripped[1:], config)
        return self.parse_flowchart(lines, config)
    
    def extract_config(self, text: str) -> tuple:
        """
        Extrait le bloc YAML de configuration en tête de fichier.
        Retourne (config: dict, diagram_text: str).
        """
        config = {}
        diagram_text = text
        config_match = self.patterns['config_block'].search(text)
        if config_match:
            try:
                config = yaml.safe_load(config_match.group(1)) or {}
                diagram_text = text[config_match.end():]
            except yaml.YAMLError as e:
                print(f"Erreur YAML: {e}")
        return config, diagram_text
    
    def parse_flowchart(self, lines: List[str], config: Dict) -> Dict[str, Any]:
        """
        Analyse un diagramme de type flowchart.
        - Détecte direction, nœuds, arêtes, classes.
        - Retourne la structure complète.
        """
        nodes = {}
        edges = []
        class_defs = {}
        node_classes = {}
        direction = 'TD'
        
        # Première passe : extraction des définitions de classes et direction
        for line in lines:
            dir_match = self.patterns['flowchart_direction'].search(line)
            if dir_match:
                direction = dir_match.group(1)
                continue
            class_def_match = self.patterns['class_def'].search(line)
            if class_def_match:
                class_name, properties = class_def_match.groups()
                class_defs[class_name] = self.parse_css_properties(properties)
                continue
            class_assign_match = self.patterns['class_assign'].search(line)
            if class_assign_match:
                node_id, class_name = class_assign_match.groups()
                node_classes[node_id] = class_name
                continue
        
        # Deuxième passe : extraction des nœuds et arêtes
        for line in lines:
            if any(pattern in line for pattern in ['classDef', ':::', 'flowchart']):
                continue
            multi_match = self.patterns['edge_multiple'].search(line)
            if multi_match:
                source = multi_match.group(1).strip()
                targets_str = multi_match.group(2)
                targets = [t.strip().strip('"[]') for t in targets_str.split('&')]
                for target in targets:
                    if target:
                        edges.append(Edge(source, target))
                        if source not in nodes:
                            nodes[source] = Node(source, source, 'rect')
                        if target not in nodes:
                            nodes[target] = Node(target, target, 'rect')
                continue
            bi_match = self.patterns['edge_bidirectional'].search(line)
            if bi_match:
                source, target = bi_match.groups()
                edges.append(Edge(source.strip(), target.strip(), edge_type="bidirectional"))
                continue
            label_match = self.patterns['edge_with_label'].search(line)
            if label_match:
                source, label, target = label_match.groups()
                edges.append(Edge(source.strip(), target.strip(), label.strip()))
                continue
            simple_match = self.patterns['edge_simple'].search(line)
            if simple_match:
                source, target = simple_match.groups()
                edges.append(Edge(source.strip(), target.strip()))
                continue
            quote_match = self.patterns['node_with_quotes'].search(line)
            if quote_match:
                node_id, label = quote_match.groups()
                nodes[node_id] = Node(node_id, label, 'rect')
                continue
            bracket_match = self.patterns['node_with_brackets'].search(line)
            if bracket_match:
                node_id, label = bracket_match.groups()
                label = label.strip('"')
                nodes[node_id] = Node(node_id, label, 'rect')
                continue
        
        # Création des nœuds manquants référencés dans les arêtes
        all_node_ids = set()
        for edge in edges:
            all_node_ids.add(edge.source)
            all_node_ids.add(edge.target)
        for node_id in all_node_ids:
            if node_id not in nodes:
                nodes[node_id] = Node(node_id, node_id, 'rect')
        
        # Assignation des classes CSS aux nœuds
        for node_id, class_name in node_classes.items():
            if node_id in nodes:
                nodes[node_id].css_class = class_name
        
        return {
            'type': 'flowchart',
            'direction': direction,
            'nodes': list(nodes.values()),
            'edges': edges,
            'class_defs': class_defs,
            'config': config
        }
    
    def parse_sequence(self, lines: List[str], config: Dict) -> Dict[str, Any]:
        """
        Analyse un diagramme de séquence.
        - Détecte participants, messages, notes, titre.
        - Retourne la structure complète.
        """
        participants: dict[str, SequenceParticipant] = {}
        order: list[str] = []
        messages: list[SequenceMessage] = []
        notes: list[SequenceNote] = []
        title = ""

        def ensure_part(pid: str, label: str | None = None):
            if pid not in participants:
                participants[pid] = SequenceParticipant(pid, label or pid)
                order.append(pid)
            elif label:
                participants[pid].label = label

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            m_title = self.sequence_patterns['title'].match(line)
            if m_title:
                title = m_title.group(1).strip()
                continue
            m_part = self.sequence_patterns['participant'].match(line)
            if m_part:
                pid = m_part.group(1)
                label = m_part.group(2).strip() if m_part.group(2) else pid
                ensure_part(pid, label)
                continue
            m_note = self.sequence_patterns['note_over'].match(line)
            if m_note:
                plist = [p.strip() for p in m_note.group(1).split(',') if p.strip()]
                for pid in plist:
                    ensure_part(pid)
                notes.append(SequenceNote(plist, m_note.group(2).strip()))
                continue
            m_msg = self.sequence_patterns['message'].match(line)
            if m_msg:
                src, arrow, tgt, text = m_msg.groups()
                ensure_part(src)
                ensure_part(tgt)
                style = 'solid'
                if '-->' in arrow and '>>' not in arrow:
                    style = 'dashed'
                if '>>' in arrow:
                    style = 'async'
                messages.append(SequenceMessage(src, tgt, text.strip(), style))
                continue
            # Ligne ignorée si non reconnue

        return {
            'type': 'sequence',
            'participants': [participants[p] for p in order],
            'messages': messages,
            'notes': notes,
            'title': title,
            'config': config
        }
    
    def parse_css_properties(self, properties_str: str) -> Dict[str, str]:
        """
        Analyse les propriétés CSS d’une définition de classe.
        Retourne un dictionnaire clé/valeur.
        """
        properties = {}
        for prop in properties_str.split(','):
            prop = prop.strip()
            if ':' in prop:
                key, value = prop.split(':', 1)
                properties[key.strip()] = value.strip()
        return properties