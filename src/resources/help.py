"""
Ressource: contenu HTML du guide utilisateur.
"""

HELP_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>ManoDiag – Guide Utilisateur</title>
<style>
body { font-family: Arial, sans-serif; color:#2c3e50; line-height:1.5; }
h1, h2, h3 { color:#1b3a57; }
code, pre { background:#f5f7fa; padding:2px 6px; border-radius:4px; }
kbd { background:#eee; border:1px solid #ccc; border-bottom-width:2px; border-radius:3px; padding:1px 5px; }
.section { margin: 18px 0; }
ul { margin-top: 6px; }
.note { background:#fff8e1; border-left:4px solid #ffb300; padding:10px; border-radius:4px;}
.good { background:#e8f5e9; border-left:4px solid #2e7d32; padding:10px; border-radius:4px;}
.warn { background:#fff3e0; border-left:4px solid #fb8c00; padding:10px; border-radius:4px;}
hr { border:none; border-top:1px solid #e0e0e0; margin:16px 0; }
small { color:#607d8b; }
</style>
</head>
<body>
<h1>ManoDiag – Guide Utilisateur</h1>
<p>Bienvenue dans ManoDiag, un outil local de création de diagrammes inspiré de la syntaxe Mermaid avec interaction directe sur les nœuds et arêtes.</p>
<hr>
<h2>1. Interface</h2>
<ul>
  <li>Éditeur (à gauche) : saisissez votre diagramme (syntaxe Mermaid “flowchart”).</li>
  <li>Vue graphique (à droite) : rendu interactif avec sélection, déplacement, redimensionnement et export.</li>
  <li>Menus principaux : Fichier, Vue, Help.</li>
</ul>
<h2>2. Démarrage rapide</h2>
<ol>
  <li>Saisissez (ou gardez) l’exemple “flowchart” dans l’éditeur.</li>
  <li>Le rendu se met à jour automatiquement (légère temporisation).</li>
  <li>Déplacez les nœuds à la souris, redimensionnez-les via les poignées bleues.</li>
  <li>Sélectionnez une arête en cliquant sur la ligne; clic droit bascule le mode Bézier.</li>
  <li>Exportez en PNG via Fichier → Exporter en PNG.</li>
</ol>
<h2>3. Syntaxe de base (flowchart)</h2>
<div class="section">
<pre>flowchart TD
    A["Titre"] --> B[Etape]
    B -->|Oui| C[Fin]
    B -->|Non| D[Alternative]
</pre>
<ul>
  <li>Directions: TD, TB, BT, RL, LR.</li>
  <li>Nœuds: <code>A["Label"]</code> ou <code>A[Label]</code>.</li>
  <li>Arêtes: <code>A --&gt; B</code>, avec label <code>A -- Texte --&gt; B</code>, bidirectionnelles <code>A &lt;--&gt; B</code>.</li>
  <li>Multiples cibles: <code>A --&gt; B &amp; C &amp; D</code>.</li>
</ul>
</div>
<h2>4. Mise en page et positions</h2>
<ul>
  <li>Par défaut: layout automatique simple.</li>
  <li>Layout fixe: ajoutez un bloc YAML en tête pour préserver les positions personnalisées.</li>
</ul>
<pre>---
layout: fixed
---
flowchart TD
...</pre>
<div class="note">
Lorsque vous déplacez/manipulez des nœuds, ManoDiag ajoute automatiquement <code>layout: fixed</code> si nécessaire pour conserver vos positions.
</div>
<h2>5. Nœuds interactifs</h2>
<ul>
  <li>Déplacement: clic-gauche + glisser. Déplacement groupé si plusieurs nœuds sont sélectionnés.</li>
  <li>Redimensionnement: poignées bleues (apparition au survol/selection). Huit poignées cardinales.</li>
  <li>Sélection multiple: maintenez <kbd>Ctrl</kbd> lors des clics; rectangle de sélection disponible.</li>
  <li>Style: couleurs de base définies via le menu Vue (et classDef Mermaid si utilisé).</li>
</ul>
<h2>6. Arêtes interactives</h2>
<ul>
  <li>Sélection: clic sur la ligne (zone de clic élargie). L’arête sélectionnée est surlignée en rouge.</li>
  <li>Mode Bézier: clic droit sur l’arête pour activer/désactiver. Des points de contrôle (bleus) apparaissent.</li>
  <li>Points d’ancrage (verts) aux extrémités: déplacez-les; ils s’aimantent intelligemment à la bordure des nœuds.</li>
  <li>Points de contrôle (bleus): déformez la courbe librement.</li>
  <li>Flèches: orientées automatiquement aux extrémités; elles suivent la géométrie de l’arête.</li>
</ul>
<div class="warn">
Astuce: cliquez en zone vide pour désélectionner l’arête et masquer ses points de contrôle.
</div>
<h2>7. Couleurs et affichage</h2>
<ul>
  <li>Vue → Afficher la grille: affiche/masque la grille de fond.</li>
  <li>Vue → Anticrénelage: adoucit le rendu (recommandé).</li>
  <li>Vue → Couleur des nœuds / Couleur de la bordure: applique les couleurs de base aux nœuds existants et futurs (compatible avec classDef).</li>
</ul>
<h2>8. Export, sauvegarde et ouverture</h2>
<ul>
  <li>Fichier → Exporter en PNG: export net avec marges de sécurité, poignées/états interactifs masqués.</li>
  <li>F# filepath: /home/t0321943/manodiag/src/resources/help.py
"""