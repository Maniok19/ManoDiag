from PyQt6.QtGui import QAction, QKeySequence, QColor
from PyQt6.QtWidgets import QMessageBox

class MenuMixin:
    def _setup_menu_bar(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Fichier")
        act_new = QAction("Nouveau", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self._new_diagram)
        file_menu.addAction(act_new)

        act_open = QAction("Ouvrir…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._open_diagram)
        file_menu.addAction(act_open)

        act_save = QAction("Sauvegarder…", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_diagram)
        file_menu.addAction(act_save)

        act_export = QAction("Exporter en PNG", self)
        act_export.triggered.connect(self._export_png)
        file_menu.addAction(act_export)

        view_menu = menubar.addMenu("Vue")
        zin = QAction("Zoom +", self); zin.setShortcut(QKeySequence.StandardKey.ZoomIn); zin.triggered.connect(self._zoom_in)
        zout = QAction("Zoom -", self); zout.setShortcut(QKeySequence.StandardKey.ZoomOut); zout.triggered.connect(self._zoom_out)
        fit = QAction("Ajuster à la fenêtre", self); fit.triggered.connect(self._fit_in_view)
        view_menu.addActions([zin, zout, fit])
        view_menu.addSeparator()

        self.action_show_grid = QAction("Afficher la grille", self, checkable=True)
        self.action_show_grid.setChecked(True)
        self.action_show_grid.toggled.connect(self._update_settings_from_menu)
        view_menu.addAction(self.action_show_grid)

        self.action_antialiasing = QAction("Anticrénelage", self, checkable=True)
        self.action_antialiasing.setChecked(True)
        self.action_antialiasing.toggled.connect(self._update_settings_from_menu)
        view_menu.addAction(self.action_antialiasing)

        view_menu.addSeparator()
        act_reset_view = QAction("Réinitialiser la vue", self); act_reset_view.triggered.connect(self._reset_view)
        act_reset_pos = QAction("Réinitialiser les positions", self); act_reset_pos.triggered.connect(self._confirm_reset_positions)
        view_menu.addActions([act_reset_view, act_reset_pos])

        edit_menu = menubar.addMenu("Éditer")
        norm = QAction("Normaliser", self)
        norm.setToolTip("Ajuste la taille des nœuds et aligne sur la grille")
        norm.triggered.connect(self._normalize_layout)
        edit_menu.addAction(norm)
        edit_menu.addSeparator()
        ex_flow = QAction("Charger l'exemple de flowchart", self); ex_flow.triggered.connect(self._load_flowchart_example)
        ex_seq = QAction("Charger l'exemple de sequence", self); ex_seq.triggered.connect(self._load_sequence_example)
        edit_menu.addActions([ex_flow, ex_seq])

        help_menu = menubar.addMenu("Help")
        act_help = QAction("User Guide…", self); act_help.setShortcut("F1"); act_help.triggered.connect(self._show_help_dialog)
        act_about = QAction("About ManoDiag", self); act_about.triggered.connect(self._show_about_dialog)
        help_menu.addActions([act_help, act_about])

    def _update_settings_from_menu(self) -> None:
        self.current_settings = {
            "show_grid": self.action_show_grid.isChecked(),
            "antialiasing": self.action_antialiasing.isChecked(),
            "node_color": self.current_settings.get("node_color", QColor(220, 221, 255)),
            "border_color": self.current_settings.get("border_color", QColor(100, 100, 200)),
        }
        self._apply_settings(self.current_settings)

    def _confirm_reset_positions(self) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Confirmer la réinitialisation")
        box.setText("Réinitialiser les positions des éléments ?")
        box.setInformativeText("Toutes les positions personnalisées seront perdues.")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        res = box.exec()
        if res == QMessageBox.StandardButton.Yes:
            self._reset_positions()