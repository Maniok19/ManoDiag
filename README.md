# ManoDiag

Outil de création de diagrammes interactifs (flowchart & sequence) basé sur PyQt6.  
Objectif: fournir une alternative locale, légère et productive à la génération de diagrammes type Mermaid, avec édition directe, déplacement, redimensionnement, personnalisation et export.

---

## Sommaire
1. Caractéristiques principales  
2. Installation  
3. Lancement rapide  
4. Syntaxe des diagrammes  
5. Bloc YAML & configuration  
6. Interaction (nœuds, arêtes, séquence)  
7. Sauvegarde / ouverture (.manodiag.json)  
8. Export PNG  
9. Raccourcis & gestes souris  
10. Paramètres d’affichage  
11. Architecture technique  
12. Persistance (PositionManager)  
13. Extensibilité  
14. Licence & crédits

---

## 1. Caractéristiques principales

- Flowcharts dynamiques (syntaxe proche Mermaid).
- Diagrammes de séquence (participants, messages, notes, titre).
- Déplacement multi‑sélection des nœuds.
- Redimensionnement précis via poignées (8 directions).
- Arêtes interactives:
  - Sélection + surbrillance.
  - Mode Bézier (clic droit).
  - Points d’ancrage ajustables (alignés intelligemment sur la bordure).
  - Points de contrôle de courbe (drag & persistants).
  - Flèches bidirectionnelles.
- Layout automatique ou positions figées (layout: fixed).
- Persistance des tailles, positions et états d’arêtes (offsets, bézier, contrôles).
- Sauvegarde / ouverture au format JSON enrichi (.manodiag.json).
- Export PNG haute résolution avec marges propres.
- Palette configurable (couleur nœuds / bordures).
- Grille optionnelle + anticrénelage.
- Normalisation automatique (ajustement taille au contenu + alignement grille).
- Rendu incrémental (n’affecte pas les éléments inchangés).
- Mode séquence optimisé (recyclage des items, signature des participants).
- Fonctionnement 100% local (pas de dépendance réseau).

---

## 2. Installation

Prérequis:
- Python >= 3.11
- Windows (testé), Linux & macOS possibles.


Création exécutable PyInstaller:
```bash
py -3 -m PyInstaller --noconsole --windowed --name ManoDiag --icon app.ico --add-data "logo_ManoDiag.png;." --add-data "exemple.manodiag.json;." main.py
```

---

## 3. Lancement rapide

```bash
python main.py
```

Au premier démarrage: un exemple flowchart est chargé automatiquement.

---

## 4. Syntaxe des diagrammes

### Flowchart minimal
```
flowchart TD
    A["Début"] --> B[Action]
    B -->|Oui| C[Fin]
    B -->|Non| D[Alternative]
    A --> E & F & G
```

Éléments:
- Directions: TD, TB, BT, LR, RL.
- Nœuds: `ID[Label]` ou `ID["Label <b>HTML</b>"]`.
- Arêtes simples: `A --> B`
- Arêtes avec label: `A -- texte --> B`
- Arêtes multiples: `A --> B & C & D`
- Bidirectionnelles: `A <--> B`
- Classes:
  ```
  classDef primary fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
  A:::primary
  ```

### Diagramme de séquence
```
sequence
title Processus d'inscription
participant U as Utilisateur
participant S as Système
U ->> S: Demande
S --> U: Confirmation
note over U,S: Délai possible
```

Styles de messages:
- `-->` flèche solide (dashed implicite si pattern Mermaid simplifié).
- `->>` asynchrone (style interne 'async').

Notes:
```
note over U,S: Texte note
```

---

## 5. Bloc YAML & configuration

Placé en tête:
```yaml
---
layout: fixed
---
```
- `layout: fixed` fige les positions (après déplacement ou redimensionnement).
- Le moteur injecte automatiquement ce bloc si des nœuds sont déplacés (flowchart uniquement).
- Sur les diagrammes de séquence: non injecté (layout géré différemment).

---

## 6. Interaction

### Nœuds (flowchart)
- Déplacer: clic gauche + glisser (multi-sélection conservée).
- Redimensionner: poignées bleues (affichées au survol ou sélection).
- Mise à l’échelle dynamique du texte centrée.
- Normalisation: Menu Éditer → Normaliser (ajuste au contenu + aligne sur grille 20px).
- Positions persistées entre rendus/sessions (si layout: fixed ou après mouvement).

### Arêtes
- Sélection: clic direct (zone de clic élargie).
- Mode Bézier: clic droit (active/désactive).
- Points:
  - Start / End: Carrés verts (accrochent la bordure optimale).
  - Control1 / Control2: Cercles bleus.
- Flèches: Drag possible (recalcule trajectoire).
- État sauvegardé (offsets + contrôles + mode Bézier).

### Séquence
- Participants: repositionnement horizontal (X uniquement).
- Messages: recalcul automatique sur mise à jour participants.
- Notes: centrées sur l’intervalle des participants impliqués.
- Titre: centré dynamiquement.
- Persistance: largeur/position participants.

---

## 7. Sauvegarde / ouverture (.manodiag.json)

Structure:
```json
{
  "format": "manodiag",
  "version": 1,
  "diagram": { "text": "..." },
  "nodes": { "A": {"x":0,"y":0,"width":160,"height":60}, ... },
  "edges": {
    "A|B||arrow": {
      "use_bezier": true,
      "start_offset": [..],
      "end_offset": [..],
      "control1": [..],
      "control2": [..]
    }
  },
  "settings": {
    "show_grid": true,
    "antialiasing": true,
    "node_color": "#dcddff",
    "border_color": "#6464c8"
  }
}
```
Utilisation:
- Fichier → Sauvegarder…
- Fichier → Ouvrir…

---

## 8. Export PNG

Fichier → Exporter en PNG:
- Calcule le boundingRect des items visibles.
- Ajoute marge de sécurité (24px + pad).
- Fond blanc opaque.
- Poignées / états interactifs non intrusifs dans le rendu final.

---

## 9. Raccourcis & gestes

Clavier:
- Ctrl+N: Nouveau
- Ctrl+O: Ouvrir
- Ctrl+S: Sauvegarder
- Ctrl++ / Ctrl+=: Zoom +
- Ctrl+-: Zoom -
- Suppr: Supprimer éléments sélectionnés
- Ctrl+A: Sélectionner tous les nœuds
- Échap: Désélection
- F1: Aide

Souris:
- Drag gauche: déplacer nœud / rectangle sélection
- Drag droit (zone vide): panoramique
- Ctrl + molette: zoom
- Clic droit sur arête: bascule Bézier
- Clic sur flèche: déplacer tête de flèche
- Poignée bleue: redimensionner

---

## 10. Paramètres d’affichage

Menu Vue:
- Afficher la grille (toggle)
- Anticrénelage
- Couleur des nœuds
- Couleur bordure
- Réinitialiser la vue (reset transform)
- Réinitialiser positions (efface persistance + retire YAML)

---

## 11. Architecture technique

Packages:
- `src/core/diagram_engine.py`: Orchestration parse + render.
- `src/parser/diagram_parser.py`: Analyse syntaxe (flowchart + sequence + YAML).
- `src/renderer/diagram_renderer.py`: Rendu incrémental (modes flowchart / sequence).
- `src/graphics/interactive_node.py`: Nœud interactif (drag, resize, style).
- `src/graphics/interactive_edge.py`: Arête interactive (sélection, Bézier, contrôle).
- `src/graphics/sequence_items.py`: Items spécialisés (participants, messages, notes).
- `src/core/position_manager.py`: Singleton persistance positions/états arêtes (JSON).
- `src/ui/*`: Couche interface (MainWindow, éditeur, vue graphique).
- `src/resources/*`: Aide HTML, assets (logo).

Flux:
Texte → Parser → dict structuré → Renderer (mode) → QGraphicsScene (items persistants) → Interactions (signals) → PositionManager.

Rendu incrémental:
- Supprime uniquement les items obsolètes.
- Réutilise nœuds/participants existants (évite scintillements).
- Met à jour style sans reconstruire.

---

## 12. Persistance (PositionManager)

- Singleton (partagé partout).
- Fichier: `node_positions.json` (racine projet ou dossier utilisateur en mode packagé).
- Sauvegarde immédiate sur:
  - Déplacement nœud
  - Redimensionnement
  - Manipulation arête (points, Bézier)
- Clé arête: `source|target|label|edge_type`.

---

## 13. Extensibilité

Points d’extension suggérés:
- Ajouter nouveaux types de diagrammes (ajouter route dans `DiagramEngine.render_to_scene`).
- Support de styles globaux via un thème JSON.
- Export SVG (utiliser QPainter sur QSvgGenerator).
- Groupes / conteneurs (nouvel item QGraphicsItem).
- Alignement intelligent (guides magnétiques).
- Historique undo/redo (QUndoStack).

---


## 14. Licence & crédits

© 2025 ManoDiag.  
Utilise: PyQt6, PyYAML, platformdirs.  
---

## Exemples rapides

Flowchart avec classes:
```
---
layout: fixed
---
flowchart LR
classDef warn fill:#fff8e1,stroke:#f57f17,stroke-width:2px
classDef ok fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px

A["Entrée"] --> B[Validation]
B -->|OK| C[Suite]
B -->|Erreur| D[Journal]
C:::ok
D:::warn
```

Séquence:
```
sequence
title Authentification
participant U as User
participant S as Service
participant DB
U ->> S: POST /login
S --> DB: Query user
DB --> S: Row
S --> U: Token
note over S,DB: Latence acceptable
```

---

## Résumé

ManoDiag fournit un environnement local robuste pour créer, manipuler et exporter des diagrammes interactifs avec une persistance fine et une architecture extensible.

---
