import os
import json

from OSCR import OSCR
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QMessageBox

from .callbacks import switch_main_tab, switch_overview_tab, trim_logfile
from .datamodels import DamageTreeModel, HealTreeModel, TreeSelectionModel
from .displayer import create_overview
from .headers import get_heal_tree_headers, get_tree_headers
from .subwindows import log_size_warning, show_warning, split_dialog
from .textedit import format_damage_number, format_damage_tree_data, format_heal_tree_data


class CustomThread(QThread):
    """
    Subclass of QThread able to execute an arbitrary function in a seperate thread.
    """
    result = Signal(tuple)

    def __init__(self, parent, func) -> None:
        self._func = func
        super().__init__(parent)

    def run(self):
        r = self._func()
        self.result.emit((r,))


def init_parser(self):
    """
    Initializes Parser.
    """
    self.parser1 = OSCR(settings=self.parser_settings)
    # self.parser2 = OSCR()


def analyze_log_callback(
        self, translate, combat_id=None, path=None, parser_num: int = 1, hidden_path=False):
    """
    Wrapper function for retrieving and showing data. Callback of "Analyse" and "Refresh" button.

    Parameters:
    - :param combat_id: id of older combat (0 -> latest combat in the file;
    len(...) - 1 -> oldest combat)
    - :param path: path to combat log file
    - :param parser_num: 1 or 2; to select self.parser1 or self.parser2
    - :param hidden_path: True when settings should not be updated with log path
    """
    if combat_id == -1 or combat_id == self.current_combat_id:
        return
    if parser_num == 1:
        parser: OSCR = self.parser1
    elif parser_num == 2:
        parser: OSCR = self.parser2
    else:
        return

    if self._ is None:
        self._ = translate

    # initial run / click on the Analyze buttonQGuiApplication
    if combat_id is None:
        if not path or not os.path.isfile(path):
            show_warning(
                    self, self._('Invalid Logfile'),
                    self._('The Logfile you are trying to open does not exist.'))
            return
        if not hidden_path and path != self.settings.value('log_path'):
            self.settings.setValue('log_path', path)

        parser.log_path = path
        try:
            parser.analyze_log_file()
        except FileExistsError:
            if self.settings.value('log_size_warning', type=bool):
                action = log_size_warning(self, translate)
                if action == 'split dialog':
                    split_dialog(self)
                    return
                elif action == 'trim':
                    trim_logfile(self)
                    parser.analyze_log_file()
                elif action == 'continue':
                    parser.analyze_massive_log_file()
                elif action == 'cancel':
                    return

        except Exception as ex:
            error = QMessageBox()
            error.setWindowTitle("Open Source Combatlog Reader")
            try:
                print(ex)
                error_message = str(ex)[:60]
                message = (
                    f"{self._('Failed to analyze the log file.')}\n\n"
                    f"{self._('Reason:')}\n{error_message}\n\n"
                    f"{self._('Please report this issue to Discord OSCR-Support channel.')}"
                )
                error.setText(message)
            except Exception as ex:
                print(ex)
                error_message = str(ex)[:60]
                message = (
                    f"{self._('Failed to analyze the log file.')}\n\n"
                    f"{self._('Reason:')}\n{error_message}\n\n"
                    f"{self._('Please report this issue to Discord OSCR-Support channel.')}"
                )
                error.setText(message)

            error.setWindowTitle(self._("Open Source Combatlog Reader"))
            error.setIcon(QMessageBox.Critical)
            error.exec()

        self.current_combats.clear()
        self.current_combats.addItems(parser.analyzed_combats)
        self.current_combats.setCurrentRow(0)
        self.current_combat_id = 0
        self.current_combat_path = path
        self.widgets.navigate_up_button.setEnabled(parser.navigation_up)
        self.widgets.navigate_down_button.setEnabled(parser.navigation_down)

        analysis_thread = CustomThread(self.window, lambda: parser.full_combat_analysis(0))
        analysis_thread.result.connect(lambda result: analysis_data_slot(self, result))
        analysis_thread.start(QThread.Priority.IdlePriority)

    # subsequent run / click on older combat
    elif isinstance(combat_id, int):
        self.current_combat_id = combat_id
        analysis_thread = CustomThread(self.window, lambda: parser.full_combat_analysis(combat_id))
        analysis_thread.result.connect(lambda result: analysis_data_slot(self, result))
        analysis_thread.start(QThread.Priority.IdlePriority)

    # reset tabber
    switch_main_tab(self, 0)
    switch_overview_tab(self, self.settings.value('first_overview_tab', type=int))


def copy_summary_callback(self, translate, parser_num: int = 1):
    """
    Callback to set the combat summary of the active combat to the user's clippboard

    Parameters:
    - :param parser_num: which parser to take the data from
    """
    if parser_num == 2:
        parser = self.parser2
    else:
        parser = self.parser1

    if not parser.active_combat:
        return

    if self._ is None:
        self._ = translate

    duration = self.parser1.active_combat.duration.total_seconds()
    combat_time = f'{int(duration / 60):02}:{duration % 60:02.0f}'

    summary = f'{{ OSCR }} {parser.active_combat.map}'
    difficulty = parser.active_combat.difficulty
    if difficulty and isinstance(difficulty, str) and difficulty != 'Unknown':
        summary += f' ({difficulty}) - DPS / DMG [{combat_time}]: '
    else:
        summary += f' - DPS / DMG [{combat_time}]: '
    players = sorted(
        self.parser1.active_combat.player_dict.values(),
        reverse=True,
        key=lambda player: player.DPS,
    )
    parts = list()
    for player in players:
        parts.append(
                f"`{player.handle}` {player.DPS:,.0f} / "
                + format_damage_number(player.total_damage))
    summary += " | ".join(parts)

    self.app.clipboard().setText(summary)


def analysis_data_slot(self, item_tuple: tuple):
    """
    Inserts the data retrieved from the parser into the respective tables

    Parameters:
    - :param item_tuple: tuple containing only the root item of the data model
    """
    create_overview(self)
    populate_analysis(self, *item_tuple)
    self.widgets.main_menu_buttons[1].setDisabled(False)


def populate_analysis(self, root_items: tuple):
    """
    Populates the Analysis' treeview table.
    """
    damage_out_item, damage_in_item, heal_out_item, heal_in_item = root_items

    damage_out_table = self.widgets.analysis_table_dout
    damage_out_model = DamageTreeModel(
            damage_out_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']), get_tree_headers())
    damage_out_table.setModel(damage_out_model)
    damage_out_root_index = damage_out_model.createIndex(0, 0, damage_out_model._root)
    damage_out_table.expand(damage_out_model.index(0, 0, damage_out_root_index))
    damage_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    damage_out_table.setSelectionModel(TreeSelectionModel(damage_out_model))

    damage_in_table = self.widgets.analysis_table_dtaken
    damage_in_model = DamageTreeModel(
            damage_in_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']), get_tree_headers())
    damage_in_table.setModel(damage_in_model)
    damage_in_root_index = damage_in_model.createIndex(0, 0, damage_in_model._root)
    damage_in_table.expand(damage_in_model.index(0, 0, damage_in_root_index))
    damage_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    damage_in_table.setSelectionModel(TreeSelectionModel(damage_in_model))

    heal_out_table = self.widgets.analysis_table_hout
    heal_out_model = HealTreeModel(
            heal_out_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']),
            get_heal_tree_headers())
    heal_out_table.setModel(heal_out_model)
    heal_out_root_index = damage_in_model.createIndex(0, 0, heal_out_model._root)
    heal_out_table.expand(heal_out_model.index(0, 0, heal_out_root_index))
    heal_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    heal_out_table.setSelectionModel(TreeSelectionModel(heal_out_model))

    heal_in_table = self.widgets.analysis_table_hin
    heal_in_model = HealTreeModel(
            heal_in_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']),
            get_heal_tree_headers())
    heal_in_table.setModel(heal_in_model)
    heal_in_root_index = damage_in_model.createIndex(0, 0, heal_in_model._root)
    heal_in_table.expand(heal_in_model.index(0, 0, heal_in_root_index))
    heal_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    heal_in_table.setSelectionModel(TreeSelectionModel(heal_in_model))

    update_shown_columns_dmg(self)
    update_shown_columns_heal(self)


def update_shown_columns_dmg(self):
    """
    Hides / shows columns of the dmg analysis tables.
    """
    dout_table = self.widgets.analysis_table_dout
    dtaken_table = self.widgets.analysis_table_dtaken
    for i in range(self.settings.value('dmg_columns_length', type=int)):
        state = self.settings.value(f'dmg_columns|{i}', type=bool)
        if state:
            dout_table.showColumn(i + 1)
            dtaken_table.showColumn(i + 1)
        else:
            dout_table.hideColumn(i + 1)
            dtaken_table.hideColumn(i + 1)


def update_shown_columns_heal(self):
    """
    Hides / shows columns of the heal analysis tables.
    """
    hout_table = self.widgets.analysis_table_hout
    hin_table = self.widgets.analysis_table_hin
    for i in range(self.settings.value('heal_columns_length', type=int)):
        state = self.settings.value(f'heal_columns|{i}', type=bool)
        if state:
            hout_table.showColumn(i + 1)
            hin_table.showColumn(i + 1)
        else:
            hout_table.hideColumn(i + 1)
            hin_table.hideColumn(i + 1)


def resize_tree_table(tree):
    """
    Resizes the columns of the given tree table to fit its contents.

    Parameters:
    - :param tree: QTreeView -> tree to be resized
    """
    for col in range(tree.header().count()):
        width = max(tree.sizeHintForColumn(col), tree.header().sectionSizeHint(col)) + 5
        tree.header().resizeSection(col, width)


def copy_analysis_table_callback(self):
    """
    Copies the current selection of analysis table as tab-delimited table
    """
    print('Table COPY')
    if self.widgets.main_tabber.currentIndex() != 1:
        return
    current_tab = self.widgets.analysis_tabber.currentIndex()
    current_table = self.widgets.analysis_table[current_tab]
    if current_tab <= 1:
        format_function = format_damage_tree_data
    else:
        format_function = format_heal_tree_data
    selection: list = current_table.selectedIndexes()
    if selection:
        selection.sort(key=lambda index: (index.row(), index.column()))
        output = list()
        last_row = -1
        for cell_index in selection:
            col = cell_index.column()
            if cell_index.row() != last_row:
                output.append(list())
            output[-1].append(cell_index.internalPointer().get_data(col))
            last_row = cell_index.row()
        print(output)
        output_text = '\n'.join(map(lambda row: '\t'.join(map(str, row)), output))
        print(output_text)
        self.app.clipboard().setText(output_text)


def copy_analysis_callback(self):
    """
    Callback for copy button on analysis tab
    """
    current_tab = self.widgets.analysis_tabber.currentIndex()
    current_table = self.widgets.analysis_table[current_tab]
    copy_mode = self.widgets.analysis_copy_combobox.currentText()
    if copy_mode == self._('Selection'):
        if current_tab <= 1:
            current_header = get_tree_headers()
            format_function = format_damage_tree_data
        else:
            current_header = get_heal_tree_headers()
            format_function = format_heal_tree_data
        selection = current_table.selectedIndexes()
        if selection:
            selection_dict = dict()
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
                    formatted_row.append(f'[{current_header[col]}] {format_function(value, col)}')
                formatted_row_name = ''.join(row_name) if isinstance(row_name, tuple) else row_name
                output.append(f"`{formatted_row_name}`: {' | '.join(formatted_row)}")
            output_string = '\n'.join(output)
            self.app.clipboard().setText(output_string)
    elif copy_mode == self._('Global Max One Hit'):
        if current_tab <= 1:
            max_one_hit_col = 4
            prefix = self._('Max One Hit')
        else:
            max_one_hit_col = 7
            prefix = self._('Max One Heal')
        max_one_hits = []
        for player_item in current_table.model()._player._children:
            max_one_hits.append((player_item.get_data(max_one_hit_col), player_item))
        max_one_hit, max_one_hit_item = max(max_one_hits, key=lambda x: x[0])
        max_one_hit_ability = max(
                max_one_hit_item._children, key=lambda x: x.get_data(max_one_hit_col))
        max_one_hit_ability = max_one_hit_ability.get_data(0)
        if isinstance(max_one_hit_ability, tuple):
            max_one_hit_ability = ''.join(max_one_hit_ability)
        output_string = (f'{{ OSCR }} {prefix}: {max_one_hit:,.2f} '
                         f'(`{"".join(max_one_hit_item.get_data(0))}` – '
                         f'{max_one_hit_ability})')
        self.app.clipboard().setText(output_string)
    elif copy_mode == self._('Max One Hit'):
        if current_tab <= 1:
            max_one_hit_col = 4
            prefix = self._('Max One Hit')
        else:
            max_one_hit_col = 7
            prefix = self._('Max One Heal')
        selection = current_table.selectedIndexes()
        if selection:
            selected_row = selection[0].internalPointer()
            if selected_row._children:
                max_one_hit_item = max(
                        selected_row._children, key=lambda child: child.get_data(max_one_hit_col))
                max_one_hit = max_one_hit_item.get_data(max_one_hit_col)
                max_one_hit_ability = max_one_hit_item.get_data(0)
                if isinstance(max_one_hit_ability, tuple):
                    max_one_hit_ability = ''.join(max_one_hit_ability)
                output_string = (f'{{ OSCR }} {prefix}: {max_one_hit:,.2f} '
                                 f'(`{"".join(selected_row.get_data(0))}` – '
                                 f'{max_one_hit_ability})')
                self.app.clipboard().setText(output_string)
    elif copy_mode == self._('Magnitude'):
        if current_tab == 0:
            prefix = self._('Total Damage Out')
        elif current_tab == 1:
            prefix = self._('Total Damage Taken')
        elif current_tab == 2:
            prefix = self._('Total Heal Out')
        else:
            prefix = self._('Total Heal In')
        magnitudes = list()
        for player_item in current_table.model()._player._children:
            magnitudes.append((player_item.get_data(2), ''.join(player_item.get_data(0))))
        magnitudes.sort(key=lambda x: x[0], reverse=True)
        magnitudes = [f"`[{''.join(player)}]` {magnitude:,.2f}" for magnitude, player in magnitudes]
        output_string = (f'{{ OSCR }} {prefix}: {" | ".join(magnitudes)}')
        self.app.clipboard().setText(output_string)
    elif copy_mode == self._('Magnitude / s'):
        if current_tab == 0:
            prefix = self._('Total DPS Out')
        elif current_tab == 1:
            prefix = self._('Total DPS Taken')
        elif current_tab == 2:
            prefix = self._('Total HPS Out')
        else:
            prefix = self._('Total HPS In')
        magnitudes = list()
        for player_item in current_table.model()._player._children:
            magnitudes.append((player_item.get_data(1), ''.join(player_item.get_data(0))))
        magnitudes.sort(key=lambda x: x[0], reverse=True)
        magnitudes = [f"`[{''.join(player)}]` {magnitude:,.2f}" for magnitude, player in magnitudes]
        output_string = (f'{{ OSCR }} {prefix}: {" | ".join(magnitudes)}')
        self.app.clipboard().setText(output_string)
