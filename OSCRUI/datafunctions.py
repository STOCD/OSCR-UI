import os
from threading import Thread

from PySide6.QtCore import Qt, QThread, Signal, Slot

from OSCR import HEAL_TREE_HEADER, TREE_HEADER
from OSCR.combat import Combat

from .callbacks import switch_main_tab, switch_overview_tab
from .datamodels import DamageTreeModel, HealTreeModel, TreeSelectionModel
from .dialogs import show_message
from .displayer import create_overview
from .textedit import format_damage_number, format_damage_tree_data, format_heal_tree_data
from .translation import tr


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


@Slot()
def analyze_log_callback(self, path=None, hidden_path=False):
    """
    Callback of "Analyze" button.

    Parameters:
    - :param path: path to combat log file
    - :param hidden_path: True when settings should not be updated with log path
    """
    if path == '' or not os.path.isfile(path):
        show_message(
                self, tr('Invalid Logfile'),
                tr('The Logfile you are trying to open does not exist.'), 'warning')
        return

    if self.thread is not None and self.thread.is_alive():
        return

    if not hidden_path and path != self.settings.value('log_path'):
        self.settings.setValue('log_path', path)

    self.parser.reset_parser()
    self.current_combats.model().clear()
    self.parser.log_path = path
    self.thread = Thread(target=self.parser.analyze_log_file, kwargs={'max_combats': 1})
    self.thread.start()

    # reset tabber
    switch_main_tab(self, 0)
    switch_overview_tab(self, self.settings.value('first_overview_tab', type=int))


def analyze_log_background(self, amount: int):
    """
    Analyzes older combats from current combatlog in the background.

    Parameters:
    - :param amount: amount of combats to analyze
    """
    if self.parser.bytes_consumed > 0 and self.thread is not None and not self.thread.is_alive():
        self.thread = Thread(target=self.parser.analyze_log_file_mp, kwargs={'max_combats': amount})
        self.thread.start()

def copy_summary_compact(self, combat_time, current_combat):
    parts = [ "OSCR (DPS)", current_combat.map ]
    difficulty = current_combat.difficulty
    if difficulty != 'Unknown':
        parts.append(difficulty)
    parts.append(combat_time)
    players = sorted(
        current_combat.players.values(),
        reverse=True,
        key=lambda player: player.DPS,
    )
    for player in players:
        parts.append(f'{player.handle} - {player.DPS:,.0f}')
    return " | ".join(parts)

def copy_summary_verbose(self, combat_time, current_combat):
    summary = f'{{ OSCR }} {current_combat.map}'
    difficulty = current_combat.difficulty
    if difficulty and isinstance(difficulty, str) and difficulty != 'Unknown':
        summary += f' ({difficulty}) - DPS / DMG [{combat_time}]: '
    else:
        summary += f' - DPS / DMG [{combat_time}]: '
    players = sorted(
        current_combat.players.values(),
        reverse=True,
        key=lambda player: player.DPS,
    )
    parts = list()
    for player in players:
        parts.append(
                f"`{player.handle}` {player.DPS:,.0f} / "
                + format_damage_number(player.total_damage))
    return summary + " | ".join(parts)

def copy_summary_csv(self, combat_time, current_combat):
    parts = [ "OSCR", "DPS", current_combat.map, current_combat.difficulty, combat_time ]
    players = sorted(
        current_combat.players.values(),
        reverse=True,
        key=lambda player: player.DPS,
    )
    for player in players:
        parts.append(player.handle)
        parts.append(f'{player.DPS:.0f}')
    return ', '.join(parts)

def copy_summary_callback(self):
    """
    Callback to set the combat summary of the active combat to the user's clipboard

    Parameters:
    - :param parser_num: which parser to take the data from
    """
    if self.current_combat_id < 0:
        return
    current_combat: Combat = self.parser.combats[self.current_combat_id]

    duration = current_combat.duration.total_seconds()
    combat_time = f'{int(duration / 60):02}:{duration % 60:02.0f}'

    copy_dispatch = {
        'Compact': copy_summary_compact,
        'Verbose': copy_summary_verbose,
        'CSV': copy_summary_csv,
    }

    summary = copy_dispatch.get(
        self.settings.value("result_format", type=str), "Compact"
    )(self, combat_time, current_combat)

    self.app.clipboard().setText(summary)


def insert_combat(self, combat: Combat):
    """
    Called by parser as soon as combat has been analyzed. Inserts combat into UI.

    Parameters:
    - :param combat: analyzed combat
    """
    difficulty = combat.difficulty if combat.difficulty is not None else ''
    dt = combat.start_time
    date = f'{dt.year}-{dt.month:02d}-{dt.day:02d}'
    time = f'{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
    self.current_combats.model().insert_item((combat.id, combat.map, date, time, difficulty))
    if combat.id == 0:
        self.current_combats.setCurrentIndex(self.current_combats.model().createIndex(0, 0, 0))
        create_overview(self, combat)
        populate_analysis(self, combat)
        self.current_combat_id = 0
        analyze_log_background(self, self.settings.value('combats_to_parse', type=int) - 1)


def analysis_data_slot(self, index: int):
    """
    Shows analyzed combat

    Parameters:
    - :param index: index of the combat in the parsers combat list
    """
    combat = self.parser.combats[index]
    create_overview(self, combat)
    populate_analysis(self, combat)
    self.current_combat_id = combat.id


def populate_analysis(self, combat: Combat):
    """
    Populates the Analysis' treeview table.

    Parameters:
    - :param combat: combat containing the data to show
    """
    damage_out_item, damage_in_item, heal_out_item, heal_in_item = combat.root_items

    damage_out_table = self.widgets.analysis_table_dout
    damage_out_model = DamageTreeModel(
            damage_out_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']), tr(TREE_HEADER))
    damage_out_table.setModel(damage_out_model)
    damage_out_root_index = damage_out_model.createIndex(0, 0, damage_out_model._root)
    damage_out_table.expand(damage_out_model.index(0, 0, damage_out_root_index))
    damage_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    damage_out_table.setSelectionModel(TreeSelectionModel(damage_out_model))

    damage_in_table = self.widgets.analysis_table_dtaken
    damage_in_model = DamageTreeModel(
            damage_in_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']), tr(TREE_HEADER))
    damage_in_table.setModel(damage_in_model)
    damage_in_root_index = damage_in_model.createIndex(0, 0, damage_in_model._root)
    damage_in_table.expand(damage_in_model.index(0, 0, damage_in_root_index))
    damage_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    damage_in_table.setSelectionModel(TreeSelectionModel(damage_in_model))

    heal_out_table = self.widgets.analysis_table_hout
    heal_out_model = HealTreeModel(
            heal_out_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']),
            tr(HEAL_TREE_HEADER))
    heal_out_table.setModel(heal_out_model)
    heal_out_root_index = damage_in_model.createIndex(0, 0, heal_out_model._root)
    heal_out_table.expand(heal_out_model.index(0, 0, heal_out_root_index))
    heal_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    heal_out_table.setSelectionModel(TreeSelectionModel(heal_out_model))

    heal_in_table = self.widgets.analysis_table_hin
    heal_in_model = HealTreeModel(
            heal_in_item, self.theme_font('tree_table_header'), self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']),
            tr(HEAL_TREE_HEADER))
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
    if self.widgets.main_tabber.currentIndex() != 1:
        return
    current_tab = self.widgets.analysis_tree_tabber.currentIndex()
    current_table = self.widgets.analysis_table[current_tab]
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
        output_text = '\n'.join(map(lambda row: '\t'.join(map(str, row)), output))
        self.app.clipboard().setText(output_text)


def copy_analysis_callback(self):
    """
    Callback for copy button on analysis tab
    """
    current_tab = self.widgets.analysis_tree_tabber.currentIndex()
    current_table = self.widgets.analysis_table[current_tab]
    copy_mode = self.widgets.analysis_copy_combobox.currentText()
    if copy_mode == tr('Selection'):
        if current_tab <= 1:
            current_header = tr(HEAL_TREE_HEADER)
            format_function = format_damage_tree_data
        else:
            current_header = tr(HEAL_TREE_HEADER)
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
    elif copy_mode == tr('Global Max One Hit'):
        if current_tab <= 1:
            max_one_hit_col = 4
            prefix = tr('Max One Hit')
        else:
            max_one_hit_col = 7
            prefix = tr('Max One Heal')
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
    elif copy_mode == tr('Max One Hit'):
        if current_tab <= 1:
            max_one_hit_col = 4
            prefix = tr('Max One Hit')
        else:
            max_one_hit_col = 7
            prefix = tr('Max One Heal')
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
                                 f'(`{"".join(selected_row.get_data(0)[0:2])}` – '
                                 f'{max_one_hit_ability})')
                self.app.clipboard().setText(output_string)
    elif copy_mode == tr('Magnitude'):
        if current_tab == 0:
            prefix = tr('Total Damage Out')
        elif current_tab == 1:
            prefix = tr('Total Damage Taken')
        elif current_tab == 2:
            prefix = tr('Total Heal Out')
        else:
            prefix = tr('Total Heal In')
        magnitudes = list()
        for player_item in current_table.model()._player._children:
            magnitudes.append((player_item.get_data(2), ''.join(player_item.get_data(0)[:2])))
        magnitudes.sort(key=lambda x: x[0], reverse=True)
        magnitudes = [f"`[{player}]` {magnitude:,.2f}" for magnitude, player in magnitudes]
        output_string = (f'{{ OSCR }} {prefix}: {" | ".join(magnitudes)}')
        self.app.clipboard().setText(output_string)
    elif copy_mode == tr('Magnitude / s'):
        if current_tab == 0:
            prefix = tr('Total DPS Out')
        elif current_tab == 1:
            prefix = tr('Total DPS Taken')
        elif current_tab == 2:
            prefix = tr('Total HPS Out')
        else:
            prefix = tr('Total HPS In')
        magnitudes = list()
        for player_item in current_table.model()._player._children:
            magnitudes.append((player_item.get_data(1), ''.join(player_item.get_data(0)[:2])))
        magnitudes.sort(key=lambda x: x[0], reverse=True)
        magnitudes = [f"`[{player}]` {magnitude:,.2f}" for magnitude, player in magnitudes]
        output_string = (f'{{ OSCR }} {prefix}: {" | ".join(magnitudes)}')
        self.app.clipboard().setText(output_string)
