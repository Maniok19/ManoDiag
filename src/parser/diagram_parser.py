"""
Parseur amélioré pour la syntaxe Mermaid
"""

import re
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Node:
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    css_class: Optional[str] = None

@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    edge_type: str = "arrow"
    style: str = "solid"

@dataclass
class SequenceParticipant:
    id: str
    label: str

@dataclass
class SequenceMessage:
    source: str
    target: str
    text: str
    style: str  # solid | dashed | async

@dataclass
class SequenceNote:
    participants: list[str]
    text: str

class DiagramParser:
    def __init__(self):
        # Patterns améliorés
        self.patterns = {
            'config_block': re.compile(r'---\s*\n(.*?)\n---', re.DOTALL),
            'flowchart_direction': re.compile(r'flowchart\s+(TD|TB|BT|RL|LR)'),
            
            # Nœuds avec différents formats
            'node_with_quotes': re.compile(r'(\w+)\["([^"]+)"\]'),
            'node_with_brackets': re.compile(r'(\w+)\[([^\]]+)\]'),
            
            # Arêtes
            'edge_bidirectional': re.compile(r'(\w+)\s*<-->\s*(\w+)'),
            'edge_with_label': re.compile(r'(\w+)\s*--\s*([^-]+)\s*-->\s*(\w+)'),
            'edge_simple': re.compile(r'(\w+)\s*-->\s*(\w+)'),
            'edge_multiple': re.compile(r'(\w+)\s*-->\s*([^&\n]+(?:\s*&\s*[^&\n]+)+)'),
            
            # Classes
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
        """Parse le texte et retourne la structure du diagramme"""
        # Extraire la config YAML
        config, diagram_text = self.extract_config(text)
        
        # Nettoyer le texte
        lines = [line.strip() for line in diagram_text.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        # Détection sequence
        stripped = [l for l in diagram_text.splitlines() if l.strip()]
        if stripped and stripped[0].strip().lower().startswith("sequence"):
            return self.parse_sequence(stripped[1:], config)
        return self.parse_flowchart(lines, config)
    
    def extract_config(self, text: str) -> tuple:
        """Extrait la configuration YAML"""
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
        """Parse un diagramme flowchart"""
        nodes = {}
        edges = []
        class_defs = {}
        node_classes = {}
        direction = 'TD'
        
        # Première passe: extraire les définitions
        for line in lines:
            # Direction
            dir_match = self.patterns['flowchart_direction'].search(line)
            if dir_match:
                direction = dir_match.group(1)
                continue
            
            # Définitions de classes
            class_def_match = self.patterns['class_def'].search(line)
            if class_def_match:
                class_name, properties = class_def_match.groups()
                class_defs[class_name] = self.parse_css_properties(properties)
                continue
            
            # Assignations de classes
            class_assign_match = self.patterns['class_assign'].search(line)
            if class_assign_match:
                node_id, class_name = class_assign_match.groups()
                node_classes[node_id] = class_name
                continue
        
        # Deuxième passe: nœuds et arêtes
        for line in lines:
            if any(pattern in line for pattern in ['classDef', ':::', 'flowchart']):
                continue
            
            # Arêtes avec cibles multiples
            multi_match = self.patterns['edge_multiple'].search(line)
            if multi_match:
                source = multi_match.group(1).strip()
                targets_str = multi_match.group(2)
                targets = [t.strip().strip('"[]') for t in targets_str.split('&')]
                
                for target in targets:
                    if target:
                        edges.append(Edge(source, target))
                        # Créer les nœuds si nécessaire
                        if source not in nodes:
                            nodes[source] = Node(source, source, 'rect')
                        if target not in nodes:
                            nodes[target] = Node(target, target, 'rect')
                continue
            
            # Arêtes bidirectionnelles
            bi_match = self.patterns['edge_bidirectional'].search(line)
            if bi_match:
                source, target = bi_match.groups()
                edges.append(Edge(source.strip(), target.strip(), edge_type="bidirectional"))
                continue
            
            # Arêtes avec label
            label_match = self.patterns['edge_with_label'].search(line)
            if label_match:
                source, label, target = label_match.groups()
                edges.append(Edge(source.strip(), target.strip(), label.strip()))
                continue
            
            # Arêtes simples
            simple_match = self.patterns['edge_simple'].search(line)
            if simple_match:
                source, target = simple_match.groups()
                edges.append(Edge(source.strip(), target.strip()))
                continue
            
            # Nœuds avec guillemets
            quote_match = self.patterns['node_with_quotes'].search(line)
            if quote_match:
                node_id, label = quote_match.groups()
                nodes[node_id] = Node(node_id, label, 'rect')
                continue
            
            # Nœuds avec crochets
            bracket_match = self.patterns['node_with_brackets'].search(line)
            if bracket_match:
                node_id, label = bracket_match.groups()
                # Nettoyer le label
                label = label.strip('"')
                nodes[node_id] = Node(node_id, label, 'rect')
                continue
        
        # Créer les nœuds manquants référencés dans les arêtes
        all_node_ids = set()
        for edge in edges:
            all_node_ids.add(edge.source)
            all_node_ids.add(edge.target)
        
        for node_id in all_node_ids:
            if node_id not in nodes:
                nodes[node_id] = Node(node_id, node_id, 'rect')
        
        # Assigner les classes
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
            # fallback: ignorer

        return {
            'type': 'sequence',
            'participants': [participants[p] for p in order],
            'messages': messages,
            'notes': notes,
            'title': title,
            'config': config
        }
    
    def parse_css_properties(self, properties_str: str) -> Dict[str, str]:
        """Parse les propriétés CSS"""
        properties = {}
        
        # Diviser par les virgules puis par les deux-points
        for prop in properties_str.split(','):
            prop = prop.strip()
            if ':' in prop:
                key, value = prop.split(':', 1)
                properties[key.strip()] = value.strip()
        
        return properties