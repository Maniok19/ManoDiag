"""
Moteur principal pour orchestrer parsing et rendu
"""

from ..parser.diagram_parser import DiagramParser
from ..renderer.diagram_renderer import DiagramRenderer

class DiagramEngine:
    def __init__(self):
        self.parser = DiagramParser()
        self.renderer = DiagramRenderer()
    
    def render_to_scene(self, text: str, scene):
        """Parse le texte et rend le diagramme dans la scène"""
        try:
            diagram_data = self.parser.parse(text)
            dtype = diagram_data.get('type')
            if dtype == 'flowchart':
                self.renderer.render_flowchart(diagram_data, scene)
            elif dtype == 'sequence':
                self.renderer.render_sequence(diagram_data, scene)
            # Ajouter d'autres types ici
        except Exception as e:
            print(f"Erreur dans le moteur: {e}")
            raise