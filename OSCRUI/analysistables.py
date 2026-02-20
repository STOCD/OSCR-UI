from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QFrame, QTableView, QTreeView

from .config import OSCRSettings
from .theme import AppTheme


class AnalysisTables():
    """
    Manages Overview and Analysis tab tables.
    """
    def __init__(self, theme: AppTheme, settings: OSCRSettings):
        self._theme: AppTheme = theme
        self._settings: OSCRSettings = settings

        self.overview_table: QTableView
        self.overview_table_frame: QFrame
        self.analysis_tree_frames: list[QFrame] = list()
        self.damage_out_table: QTreeView
        self.damage_in_table: QTreeView
        self.heal_out_table: QTreeView
        self.heal_in_table: QTreeView

    def refresh_tables(
            self, damage_out_player: QModelIndex, damage_in_player: QModelIndex,
            heal_out_player: QModelIndex, heal_in_player: QModelIndex):
        """
        Adjusts view of overview and analysis tables to fit newly inserted data.

        Parameters:
        - :param damage_out_player: model index pointing to the "player" row for pre-expansion
        - :param damage_in_player: model index pointing to the "player" row for pre-expansion
        - :param heal_out_player: model index pointing to the "player" row for pre-expansion
        - :param heal_in_player: model index pointing to the "player" row for pre-expansion
        """
        if self._settings.overview_sort_order == 'Descending':
            sort_order = Qt.SortOrder.AscendingOrder
        else:
            sort_order = Qt.SortOrder.DescendingOrder
        self.overview_table.sortByColumn(self._settings.overview_sort_column, sort_order)
        self.overview_table.resizeColumnsToContents()

        self.damage_out_table.expand(damage_out_player)
        self.damage_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.damage_in_table.expand(damage_in_player)
        self.damage_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.heal_out_table.expand(heal_out_player)
        self.heal_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.heal_in_table.expand(heal_in_player)
        self.heal_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)

        self.update_shown_damage_columns()
        self.update_shown_heal_columns()

    def update_shown_damage_columns(self):
        """
        Hides / shows columns of the dmg analysis tables according to the current settings.
        """
        for i, state in enumerate(self._settings.dmg_columns):
            if state:
                self.damage_out_table.showColumn(i + 1)
                self.damage_in_table.showColumn(i + 1)
            else:
                self.damage_out_table.hideColumn(i + 1)
                self.damage_in_table.hideColumn(i + 1)

    def update_shown_heal_columns(self):
        """
        Hides / shows columns of the heal analysis tables according to the current settings.
        """
        for i, state in enumerate(self._settings.heal_columns):
            if state:
                self.heal_out_table.showColumn(i + 1)
                self.heal_in_table.showColumn(i + 1)
            else:
                self.heal_out_table.hideColumn(i + 1)
                self.heal_in_table.hideColumn(i + 1)
