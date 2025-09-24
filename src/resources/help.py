"""
Ressource: contenu HTML du guide utilisateur (affiché dans la boîte d'aide).
Le style privilégie la lisibilité (contraste élevé, police standard).
"""

HELP_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>ManoDiag – Guide Utilisateur</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
    :root {
        --bg: #ffffff;
        --fg: #111111;
        --fg-soft:#2c3e50;
        --accent:#0d47a1;
        --border:#d0d4d9;
        --note:#fff8d2;
        --note-border:#c49b00;
        --warn:#fff3e0;
        --warn-border:#e07a00;
        --good:#e8f5e9;
        --good-border:#2e7d32;
        --code-bg:#f5f7fa;
    }
    * { box-sizing: border-box; }
    html,body { margin:0; padding:0; background:var(--bg); color:var(--fg); font: 14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; }
    body { padding: 18px 26px 60px; }
    h1,h2,h3 { color: var(--accent); margin: 1.6em 0 .6em; line-height:1.25; font-weight:600; }
    h1 { margin-top:0; font-size: 1.95em; }
    h2 { font-size: 1.35em; }
    h3 { font-size: 1.08em; }
    p { margin: .7em 0; }
    ul,ol { padding-left: 22px; margin: .4em 0 1em; }
    li { margin: .25em 0; }
    code, pre, kbd {
        font-family: ui-monospace,Consolas,"Courier New",monospace;
        font-size: 13px;
    }
    code, kbd {
        background: var(--code-bg);
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #e1e6eb;
    }
    pre {
        background: var(--code-bg);
        padding: 10px 14px;
        border: 1px solid #e1e6eb;
        border-radius: 6px;
        overflow:auto;
        margin: .8em 0 1.2em;
    }
    pre code { background: transparent; padding:0; border:none; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    hr { border: none; border-top:1px solid var(--border); margin: 2em 0; }
    .note, .warn, .good {
        border-left: 5px solid;
        padding: 10px 14px;
        border-radius: 4px;
        margin: 14px 0 18px;
    }
    .note { background: var(--note); border-color: var(--note-border); }
    .warn { background: var(--warn); border-color: var(--warn-border); }
    .good { background: var(--good); border-color: var(--good-border); }
    .toc a { display:block; padding:4px 0; }
    .kbd-list kbd { margin-right:6px; display:inline-block; min-width:42px; text-align:center; }
    table.shortcuts { border-collapse: collapse; width:100%; margin:14px 0 20px; }
    table.shortcuts th, table.shortcuts td { border:1px solid #d9dde2; padding:6px 10px; text-align:left; vertical-align:top; }
    table.shortcuts th { background:#f0f2f5; font-weight:600; }
    small { color:#5b6a73; }
    .pill { display:inline-block; background:#eef2f7; border:1px solid #ccd2d8; padding:2px 8px; border-radius:12px; font-size:12px; margin:2px 4px 2px 0; }
    .grid { display:grid; gap:10px; }
    .mono { font-family: ui-monospace,Consolas,monospace; }
    .section { margin-top:28px; }
    .top-link { position:fixed; right:18px; bottom:18px; background:#0d47a1; color:#fff; padding:8px 14px; text-decoration:none; border-radius:20px; font-size:13px; box-shadow:0 2px 6px rgba(0,0,0,.18); }
    .top-link:hover { background:#0b3a84; }
</style>
</head>
<body>
<a id="top"></a>
<h1>ManoDiag – Guide Utilisateur</h1>
<p>ManoDiag est un outil local (PyQt6) pour créer, manipuler et exporter des diagrammes interactifs <b>flowchart</b> et <b>sequence</b>, avec persistance des positions, édition directe et export PNG haute qualité.</p>

<div class="section">
<h2>Sommaire</h2>
<div class="toc">
  <a href="#presentation">1. Présentation rapide</a>
  <a href="#interface">2. Interface & zones</a>
  <a href="#types">3. Types de diagrammes</a>
  <a href="#flowchart">4. Syntaxe Flowchart</a>
  <a href="#sequence">5. Syntaxe Séquence</a>
  <a href="#yaml">6. Bloc YAML & configuration</a>
  <a href="#interaction">7. Interaction générale</a>
  <a href="#edges-advanced">8. Arêtes avancées (Bézier)</a>
  <a href="#normalisation">9. Normalisation & layout</a>
  <a href="#persistance">10. Persistance & fichiers</a>
  <a href="#export">11. Export PNG</a>
  <a href="#shortcuts">12. Raccourcis & gestes</a>
  <a href="#display">13. Paramètres d’affichage</a>
  <a href="#astuces">14. Astuces & bonnes pratiques</a>
  <a href="#limitations">15. Limitations connues</a>
  <a href="#about">16. À propos</a>
</div>
</div>

<hr>

<h2 id="presentation">1. Présentation rapide</h2>
<ul>
  <li><b>Création locale</b> sans serveur.</li>
  <li><b>Édition duale</b> : texte (syntax Mermaid-like) + rendu interactif.</li>
  <li><b>Manipulation directe</b> : déplacement, redimensionnement, arêtes modifiables.</li>
  <li><b>Persistance</b> automatique des positions dans un JSON interne.</li>
  <li><b>Export PNG</b> propre (marges + suppression des poignées).</li>
</ul>
<div class="good"><b>Gain:</b> Itérations très rapides — modifier, ajuster visuellement, exporter.</div>

<h2 id="interface">2. Interface & zones</h2>
<ul>
  <li><b>Panneau gauche</b> : éditeur texte (diagramme source).</li>
  <li><b>Panneau droit</b> : zone graphique interactive (QGraphicsView).</li>
  <li><b>Menus</b> : Fichier, Vue, Éditer, Help.</li>
  <li><b>Barre de statut</b> : messages (rendu, export, erreurs).</li>
</ul>

<h2 id="types">3. Types de diagrammes</h2>
<ul>
  <li><b>flowchart</b> : blocs/nœuds + arêtes directionnelles.</li>
  <li><b>sequence</b> : participants, messages horizontaux, notes, titre.</li>
</ul>
<p>La première ligne (hors YAML) détermine le type. Exemple:</p>
<pre><code>flowchart TD
A[Start] --> B[Action]</code></pre>
<pre><code>sequence
title Auth
participant U as User
participant S as Service
U ->> S: Request</code></pre>

<h2 id="flowchart">4. Syntaxe Flowchart (base)</h2>
<pre><code>flowchart LR
A["Entrée"] --> B{Décision}
B -->|Oui| C[Suite]
B -->|Non| D[Alternative]
A --> E & F & G
A <--> H
classDef ok fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
C:::ok
</code></pre>
<ul>
  <li><b>Directions</b> : TD, TB, BT, LR, RL.</li>
  <li><b>Nœud</b> : <code>ID[Label]</code> ou <code>ID["Label &lt;b&gt;HTML&lt;/b&gt;"]</code>.</li>
  <li><b>Arête simple</b> : <code>A --> B</code>.</li>
  <li><b>Arête avec label</b> : <code>A -- texte --> B</code>.</li>
  <li><b>Arête bidirectionnelle</b> : <code>A &lt;--&gt; B</code>.</li>
  <li><b>Cibles multiples</b> : <code>A --> B &amp; C &amp; D</code>.</li>
  <li><b>Classes</b> :
<pre><code>classDef warn fill:#fff8e1,stroke:#f57f17,stroke-width:2px
N:::warn
</code></pre></li>
</ul>

<h2 id="sequence">5. Syntaxe Diagramme de séquence</h2>
<pre><code>sequence
title Processus d'inscription
participant U as Utilisateur
participant S as Système
U ->> S: Demande
S --> U: Confirmation
note over U,S: Délai possible
</code></pre>
<ul>
  <li><b>participant</b> : déclaration (option <code>as</code> pour alias affiché).</li>
  <li><b>Message</b> :
    <ul>
      <li><code>--> / --></code> : style normal (ligne éventuellement réinterprétée).</li>
      <li><code>--></code> (dans ManoDiag, interprété solide/dashed selon forme simplifiée).</li>
      <li><code>->></code> : asynchrone (marqueur visuel distinct).</li>
    </ul>
  </li>
  <li><b>Note</b> : <code>note over U,S: Texte</code>.</li>
  <li><b>Titre</b> : <code>title ...</code>.</li>
  <li><b>Déplacement participants</b> : drag horizontal (X uniquement).</li>
</ul>

<h2 id="yaml">6. Bloc YAML & configuration</h2>
<p>Placer en tête (facultatif) :</p>
<pre><code>---
layout: fixed
---
flowchart TD
...</code></pre>
<ul>
  <li><code>layout: fixed</code> : conserve les positions personnalisées.</li>
  <li>Injecté automatiquement après un déplacement de nœud (flowchart).</li>
  <li>Ignoré pour <code>sequence</code>.</li>
</ul>

<h2 id="interaction">7. Interaction générale</h2>
<ul>
  <li><b>Déplacement nœud</b> : clic-gauche + glisser (multi-sélection supportée).</li>
  <li><b>Redimensionnement</b> : poignées bleues (8 directions).</li>
  <li><b>Sélection multiple</b> : <kbd>Ctrl</kbd> + clic ou rectangle (glisser en zone vide).</li>
  <li><b>Désélection</b> : clic zone vide ou <kbd>Echap</kbd>.</li>
  <li><b>Zoom</b> : <kbd>Ctrl</kbd> + molette.</li>
  <li><b>Panoramique</b> : bouton droit (drag) en zone vide.</li>
</ul>

<h2 id="edges-advanced">8. Arêtes avancées (Bézier & contrôle)</h2>
<ul>
  <li><b>Sélection</b> : clic sur la ligne (zone de capture élargie).</li>
  <li><b>Bascule Bézier</b> : clic droit sur l’arête.</li>
  <li><b>Points d’ancrage</b> (verts) : repositionnent l’entrée/sortie (magnétisme sur la bordure).</li>
  <li><b>Points de contrôle</b> (bleus) : ajustent la courbe.</li>
  <li><b>Flèche</b> : draggable (position recalculée).</li>
  <li><b>Sauvegarde</b> : offsets & courbe persistés.</li>
</ul>
<div class="note">Cliquez en zone vide pour masquer les points (dès que l’arête est désélectionnée).</div>

<h2 id="normalisation">9. Normalisation & layout</h2>
<ul>
  <li><b>Normaliser</b> (menu Éditer) : ajuste chaque nœud à son contenu + aligne sur grille (20px).</li>
  <li><b>Layout auto</b> (par défaut) : placement simple en grille.</li>
  <li><b>Layout fixed</b> : privilégie les positions sauvegardées.</li>
</ul>

<h2 id="persistance">10. Persistance & fichiers</h2>
<ul>
  <li><b>PositionManager</b> : enregistre positions & états d’arêtes dans <code>node_positions.json</code>.</li>
  <li><b>Format ManoDiag</b> : <code>.manodiag.json</code> (texte + nodes + edges + settings).</li>
  <li><b>Sauvegarder / Ouvrir</b> via menu Fichier.</li>
  <li><b>Clé arête</b> : <code>source|target|label|edge_type</code>.</li>
</ul>

<h2 id="export">11. Export PNG</h2>
<ul>
  <li>Menu Fichier → Exporter en PNG.</li>
  <li>Calcule le rectangle englobant, ajoute marge (24px + pad).</li>
  <li>Fond blanc opaque, poignées masquées.</li>
</ul>
<div class="good">Utiliser après un zoom adapté (indépendant de l’export pixel).</div>

<h2 id="shortcuts">12. Raccourcis & gestes</h2>
<table class="shortcuts">
<thead><tr><th>Action</th><th>Raccourci / Geste</th></tr></thead>
<tbody>
<tr><td>Nouveau</td><td><kbd>Ctrl</kbd>+<kbd>N</kbd></td></tr>
<tr><td>Ouvrir</td><td><kbd>Ctrl</kbd>+<kbd>O</kbd></td></tr>
<tr><td>Sauvegarder</td><td><kbd>Ctrl</kbd>+<kbd>S</kbd></td></tr>
<tr><td>Zoom + / -</td><td><kbd>Ctrl</kbd>+<kbd>+</kbd> / <kbd>Ctrl</kbd>+<kbd>-</kbd></td></tr>
<tr><td>Tout sélectionner (nœuds)</td><td><kbd>Ctrl</kbd>+<kbd>A</kbd></td></tr>
<tr><td>Supprimer sélection</td><td><kbd>Suppr</kbd></td></tr>
<tr><td>Désélection</td><td><kbd>Echap</kbd></td></tr>
<tr><td>Aide</td><td><kbd>F1</kbd></td></tr>
<tr><td>Zoom (molette)</td><td><kbd>Ctrl</kbd> + Molette</td></tr>
<tr><td>Panoramique</td><td>Clic droit + glisser</td></tr>
<tr><td>Bascule Bézier</td><td>Clic droit sur arête</td></tr>
</tbody>
</table>

<h2 id="display">13. Paramètres d’affichage</h2>
<ul>
  <li><b>Grille</b> : affichage / masquage (repères).</li>
  <li><b>Anticrénelage</b> : lissage (recommandé).</li>
  <li><b>Couleur des nœuds / bordures</b> : thème de base (classe CSS spécifique conserve ses propriétés personnalisées).</li>
  <li><b>Réinitialiser la vue</b> : recentre + reset zoom.</li>
  <li><b>Réinitialiser positions</b> : efface persistance + relayout.</li>
</ul>

<h2 id="astuces">14. Astuces & bonnes pratiques</h2>
<ul>
  <li>Déplacer plusieurs nœuds avant d’exporter pour un flux visuel cohérent.</li>
  <li>Éviter des labels trop longs : préférer des sauts de ligne <code>\\n</code>.</li>
  <li>Utiliser des <code>classDef</code> pour harmoniser la palette.</li>
  <li>Après de nombreux ajustements, lancer <b>Normaliser</b> pour homogénéiser.</li>
</ul>

<h2 id="limitations">15. Limitations connues</h2>
<ul>
  <li>Layout automatique simplifié (pas de moteur de graphe avancé).</li>
  <li>Pas encore d’undo/redo (suggesté via QUndoStack futur).</li>
  <li>Pas d’export SVG natif (extension prévue).</li>
  <li>Pas de groupes / conteneurs hiérarchiques.</li>
</ul>

<h2 id="about">16. À propos</h2>
<p><b>ManoDiag</b> – application locale de diagrammes interactive.<br>
© 2025 ManoDiag. Technologies : PyQt6, PyYAML, platformdirs.</p>
<small>Les noms, formats et fonctionnalités peuvent évoluer dans de futures versions.</small>

<a class="top-link" href="#top" title="Retour haut">↑ Haut</a>
</body>
</html>
"""