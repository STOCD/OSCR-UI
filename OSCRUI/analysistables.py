from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication, QFrame, QTableView, QTreeView

from OSCR import HEAL_TREE_HEADER, TREE_HEADER

from .config import OSCRSettings
from .datamodels import TreeItem, TreeModel
from .textedit import format_damage_tree_data, format_heal_tree_data
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import RCONTENT, RFIXED, SMINMIN, SMPIXEL


class AnalysisTables():
    """
    Manages Overview and Analysis tab tables.
    """
    def __init__(self, theme: AppTheme, settings: OSCRSettings):
        self._theme: AppTheme = theme
        self._settings: OSCRSettings = settings

        self.overview_table: QTableView
        self.overview_table_frame: QFrame
        self.damage_out_table: QTreeView
        self.damage_in_table: QTreeView
        self.heal_out_table: QTreeView
        self.heal_in_table: QTreeView

    def get_analysis_table(self, index: int) -> QTreeView:
        """
        Returns analysis table by index (counted from left to right in the UI).

        Parameters:
        - :param index: index referring to the table
        """
        match index:
            case 0:
                return self.damage_out_table
            case 1:
                return self.damage_in_table
            case 2:
                return self.heal_out_table
            case 3:
                return self.heal_in_table

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

    def expand_overview_table(self):
        """
        Shows the overview table
        """
        self.overview_table_frame.show()

    def collapse_overview_table(self):
        """
        Hides the overview table
        """
        self.overview_table_frame.hide()

    def resize_tree_table(self, tree: QTreeView):
        """
        Resizes the columns of the given tree table to fit its contents

        Parameters:
        - :param tree: QTreeView -> tree to be resized
        """
        for col in range(tree.header().count()):
            width = max(tree.sizeHintForColumn(col), tree.header().sectionSizeHint(col)) + 5
            tree.header().resizeSection(col, width)

    def create_analysis_table(self, widget) -> QTreeView:
        """
        Creates and returns a QTreeView, styled according to widget.

        Parameters:
        - :param parent: parent of the table
        - :param widget: style key for the table

        :return: configured QTreeView
        """
        table = QTreeView()
        table.setStyleSheet(self._theme.get_style_class('QTreeView', widget))
        table.setSizePolicy(SMINMIN)
        table.setAlternatingRowColors(True)
        table.setHorizontalScrollMode(SMPIXEL)
        table.setVerticalScrollMode(SMPIXEL)
        table.setSortingEnabled(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.header().setStyleSheet(
            self._theme.get_style_class('QHeaderView', 'tree_table_header'))
        table.header().setSectionResizeMode(RFIXED)
        table.header().setMinimumSectionSize(1)
        table.header().setSectionsClickable(True)
        table.header().setStretchLastSection(False)
        table.header().setSortIndicatorShown(False)
        table.expanded.connect(lambda: self.resize_tree_table(table))
        table.collapsed.connect(lambda: self.resize_tree_table(table))
        return table

    def style_table(self, table: QTableView, style_override: dict = {}, single_row_selection=False):
        """
        Styles the given table.

        Parameters:
        - :param table: table to be styled
        - :param style_override: style override for table
        - :param single_row_selection: True when only one row should be selectable at once
        """
        table.setAlternatingRowColors(self._theme.opt.table_alternate)
        table.setShowGrid(self._theme.opt.table_gridline)
        table.setSortingEnabled(True)
        table.setWordWrap(False)
        table.setStyleSheet(self._theme.get_style_class('QTableView', 'table', style_override))
        table.setHorizontalScrollMode(SMPIXEL)
        table.setVerticalScrollMode(SMPIXEL)
        table.horizontalHeader().setStyleSheet(
            self._theme.get_style_class('QHeaderView', 'table_header'))
        table.verticalHeader().setStyleSheet(
            self._theme.get_style_class('QHeaderView', 'table_index'))
        table.verticalHeader().setMinimumHeight(1)
        table.verticalHeader().setDefaultSectionSize(1)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.horizontalHeader().setSortIndicatorShown(False)
        table.horizontalHeader().setSectionResizeMode(RFIXED)
        table.verticalHeader().setSectionResizeMode(RCONTENT)
        table.setSizePolicy(SMINMIN)
        if single_row_selection:
            table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    def copy_analysis_table(self, analysis_tab: int):
        """
        Copies the current selection of analysis table as tab-delimited table.

        Parameters:
        - :param analysis_tab: index of analysis tab to copy data from
        """
        selection = self.get_analysis_table(analysis_tab).selectedIndexes()
        if len(selection) > 0:
            selection.sort(key=lambda index: (index.row(), index.column()))
            output: list[list] = list()
            last_row = -1
            for cell_index in selection:
                if cell_index.row() != last_row:
                    output.append(list())
                tree_row: TreeItem = cell_index.internalPointer()
                output[-1].append(tree_row.get_data(cell_index.column()))
                last_row = cell_index.row()
            output_text = '\n'.join(map(lambda row: '\t'.join(map(str, row)), output))
            QApplication.clipboard().setText(output_text)

    def copy_analysis_data(self, analysis_tab: int, copy_mode: str):
        """
        Copies data from analysis table according to `copy_mode`.

        Parameters:
        - :param analysis_tab: index of analysis tab to copy data from
        - :param copy_mode: specifies what to copy from table
        """
        current_table = self.get_analysis_table(analysis_tab)
        if copy_mode == tr('Selection'):
            if analysis_tab <= 1:
                current_header = tr(TREE_HEADER)
                format_func = format_damage_tree_data
            else:
                current_header = tr(HEAL_TREE_HEADER)
                format_func = format_heal_tree_data
            selection = current_table.selectedIndexes()
            if selection:
                selection_dict: dict[str | tuple, dict] = dict()
                for selected_cell in selection:
                    column = selected_cell.column()
                    row_name = selected_cell.internalPointer().get_data(0)
                    if row_name not in selection_dict:
                        selection_dict[row_name] = dict()
                    if column != 0:
                        cell_data = selected_cell.internalPointer().get_data(column)
                        selection_dict[row_name][column] = cell_data
                output = ['{ OSCR }']
                for row_name, row_data in selection_dict.items():
                    formatted_row = list()
                    for col, value in row_data.items():
                        formatted_row.append(f'[{current_header[col]}] {format_func(value, col)}')
                    if isinstance(row_name, tuple):
                        row_name = row_name[0] + row_name[1]
                    output.append(f"`{row_name}`: {' | '.join(formatted_row)}")
                output_string = '\n'.join(output)
                QApplication.clipboard().setText(output_string)
        elif copy_mode == tr('Global Max One Hit'):
            if analysis_tab <= 1:
                max_one_hit_col = 4
                prefix = tr('Max One Hit')
            else:
                max_one_hit_col = 7
                prefix = tr('Max One Heal')
            max_one_hits: list[tuple[float, TreeItem]] = list()
            table_model: TreeModel = current_table.model()
            for player_item in table_model._player._children:
                max_one_hits.append((player_item.get_data(max_one_hit_col), player_item))
            max_one_hit, max_one_hit_item = max(max_one_hits, key=lambda x: x[0])
            max_one_hit_ability = max(
                max_one_hit_item._children, key=lambda x: x.get_data(max_one_hit_col))
            max_one_hit_ability = max_one_hit_ability.get_data(0)
            if isinstance(max_one_hit_ability, tuple):
                max_one_hit_ability = max_one_hit_ability[0] + max_one_hit_ability[1]
            output_string = (f'{{ OSCR }} {prefix}: {max_one_hit:,.2f} '
                             f'(`{"".join(max_one_hit_item.get_data(0)[:2])}` – '
                             f'{max_one_hit_ability})')
            QApplication.clipboard().setText(output_string)
        elif copy_mode == tr('Max One Hit'):
            if analysis_tab <= 1:
                max_one_hit_col = 4
                prefix = tr('Max One Hit')
            else:
                max_one_hit_col = 7
                prefix = tr('Max One Heal')
            selection = current_table.selectedIndexes()
            if selection:
                selected_row: TreeItem = selection[0].internalPointer()
                if selected_row._children:
                    max_one_hit_item = max(
                        selected_row._children, key=lambda child: child.get_data(max_one_hit_col))
                    max_one_hit = max_one_hit_item.get_data(max_one_hit_col)
                    max_one_hit_ability = max_one_hit_item.get_data(0)
                    if isinstance(max_one_hit_ability, tuple):
                        max_one_hit_ability = ''.join(max_one_hit_ability)
                    max_one_hit_source = selected_row.get_data(0)
                    if isinstance(max_one_hit_source, tuple):
                        max_one_hit_source = ''.join(max_one_hit_source[:2])
                    output_string = (f'{{ OSCR }} {prefix}: {max_one_hit:,.2f} '
                                     f'(`{max_one_hit_source}` – {max_one_hit_ability})')
                    QApplication.clipboard().setText(output_string)
        elif copy_mode == tr('Magnitude'):
            if analysis_tab == 0:
                prefix = tr('Total Damage Out')
            elif analysis_tab == 1:
                prefix = tr('Total Damage Taken')
            elif analysis_tab == 2:
                prefix = tr('Total Heal Out')
            else:
                prefix = tr('Total Heal In')
            magnitudes: list[tuple[float, str]] = list()
            table_model: TreeModel = current_table.model()
            for player_item in table_model._player._children:
                magnitudes.append((player_item.get_data(2), ''.join(player_item.get_data(0)[:2])))
            magnitudes.sort(key=lambda x: x[0], reverse=True)
            magnitudes = [f"`{player}` {magnitude:,.2f}" for magnitude, player in magnitudes]
            output_string = (f'{{ OSCR }} {prefix}: {" | ".join(magnitudes)}')
            QApplication.clipboard().setText(output_string)
        elif copy_mode == tr('Magnitude / s'):
            if analysis_tab == 0:
                prefix = tr('Total DPS Out')
            elif analysis_tab == 1:
                prefix = tr('Total DPS Taken')
            elif analysis_tab == 2:
                prefix = tr('Total HPS Out')
            else:
                prefix = tr('Total HPS In')
            magnitudes: list[tuple[float, str]] = list()
            table_model: TreeModel = current_table.model()
            for player_item in table_model._player._children:
                magnitudes.append((player_item.get_data(1), ''.join(player_item.get_data(0)[:2])))
            magnitudes.sort(key=lambda x: x[0], reverse=True)
            magnitudes = [f"`{player}` {magnitude:,.2f}" for magnitude, player in magnitudes]
            output_string = (f'{{ OSCR }} {prefix}: {" | ".join(magnitudes)}')
            QApplication.clipboard().setText(output_string)
