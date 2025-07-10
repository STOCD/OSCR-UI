import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLineEdit, QListWidgetItem

from OSCR import (
    compose_logfile, repair_logfile as oscr_repair_logfile, extract_bytes)

from .dialogs import confirmation_dialog, show_message
from .iofunctions import browse_path
from .textedit import format_path
from .translation import tr


def browse_log(self, entry: QLineEdit):
    """
    Callback for browse button.

    Parameters:
    - :param entry: QLineEdit -> path entry line widget
    """
    current_path = entry.text()
    if current_path != '':
        current_path = os.path.dirname(current_path)
    path = self.browse_path(current_path, 'Logfile (*.log);;Any File (*.*)')
    if path != '':
        entry.setText(format_path(path))
        if self.settings.value('auto_scan', type=bool):
            self.analyze_log_callback(path=path, parser_num=1)


def save_combat(self, combat_num: int):
    """
    Callback for save button.

    Parameters:
    - :param combat_num: number of combat in self.combats
    """
    combat = self.parser.combats[combat_num]
    if not combat:
        return
    filename = combat.map
    if combat.difficulty is not None and combat.difficulty != '':
        filename += ' ' + combat.difficulty
    filename += f' {combat.start_time.strftime("%Y-%m-%d %H.%M")}.log'
    base_dir = f'{os.path.dirname(self.entry.text())}/{filename}'
    path = browse_path(self, base_dir, 'Logfile (*.log);;Any File (*.*)', save=True)
    if path:
        self.parser.export_combat(combat_num, path)


def switch_analysis_tab(self, tab_index: int):
    """
    Callback for tab switch buttons; switches tab and sets active button.

    Parameters:
    - :param tab_index: index of the tab to switch to
    """
    self.widgets.analysis_graph_tabber.setCurrentIndex(tab_index)
    self.widgets.analysis_tree_tabber.setCurrentIndex(tab_index)
    for index, button in enumerate(self.widgets.analysis_menu_buttons):
        if not index == tab_index:
            button.setChecked(False)
        else:
            button.setChecked(True)


def switch_overview_tab(self, tab_index: int):
    """
    Callback for tab switch buttons; switches tab and sets active button.

    Parameters:
    - :param tab_index: index of the tab to switch to
    """
    self.widgets.overview_tabber.setCurrentIndex(tab_index)
    for index, button in enumerate(self.widgets.overview_menu_buttons):
        if not index == tab_index:
            button.setChecked(False)
        else:
            button.setChecked(True)


def switch_main_tab(self, tab_index: int):
    """
    Callback for main tab switch buttons. Switches main and sidebar tabs.

    Parameters:
    - :param tab_index: index of the tab to switch to
    """
    SIDEBAR_TAB_CONVERSION = {
        0: 0,
        1: 0,
        2: 1,
        3: 2
    }
    self.widgets.main_tabber.setCurrentIndex(tab_index)
    self.widgets.sidebar_tabber.setCurrentIndex(SIDEBAR_TAB_CONVERSION[tab_index])
    if tab_index == 0:
        self.widgets.overview_table_button.show()
    else:
        self.widgets.overview_table_button.hide()
    if tab_index == 1:
        self.widgets.analysis_graph_button.show()
    else:
        self.widgets.analysis_graph_button.hide()


def add_favorite_ladder(self):
    """
    Adds a latter to favorites list. Updates settings
    """
    current_item = self.widgets.ladder_selector.currentItem()
    if current_item is not None:
        current_ladder_key = f'{current_item.text()}|{current_item.difficulty}'
        favorite_ladders = self.settings.value('favorite_ladders', type=list)
        if current_ladder_key not in favorite_ladders:
            favorite_ladders.append(current_ladder_key)
            self.settings.setValue('favorite_ladders', favorite_ladders)
            ladder_text, difficulty = current_ladder_key.split('|')
            if difficulty == 'None':
                difficulty = None
            item = QListWidgetItem(ladder_text)
            item.difficulty = difficulty
            if difficulty != 'Any' and difficulty is not None:
                icon = self.icons[f'TFO-{difficulty.lower()}']
                icon.addPixmap(icon.pixmap(18, 24), QIcon.Mode.Selected)
                item.setIcon(icon)
            self.widgets.favorite_ladder_selector.addItem(item)


def remove_favorite_ladder(self):
    """
    Adds a latter to favorites list. Updates settings
    """
    current_item = self.widgets.favorite_ladder_selector.currentItem()
    if current_item is not None:
        current_ladder_key = f'{current_item.text()}|{current_item.difficulty}'
        favorite_ladders = self.settings.value('favorite_ladders', type=list)
        if current_ladder_key in favorite_ladders:
            favorite_ladders.remove(current_ladder_key)
            self.settings.setValue('favorite_ladders', favorite_ladders)
            row = self.widgets.favorite_ladder_selector.row(current_item)
            self.widgets.favorite_ladder_selector.takeItem(row)


def set_graph_resolution_setting(self, new_value: int):
    """
    Calculates new_value / 10 and stores it to settings.

    Parameters:
    - :param new_value: data points per second
    """
    try:
        setting_value = round(new_value / 10, 1)
        self.settings.setValue('graph_resolution', setting_value)
        return setting_value
    except (ValueError, ZeroDivisionError):
        return


def set_parser_opacity_setting(self, new_value: int):
    """
    Calculates new_value / 10 and stores it to settings.

    Parameters:
    - :param new_value: 20 times the opacity percentage
    """
    setting_value = f'{new_value / 20:.2f}'
    self.settings.setValue('live_parser_opacity', setting_value)
    return setting_value


def set_ui_scale_setting(self, new_value: int):
    """
    Calculates new_value / 50 and stores it to settings.

    Parameters:
    - :param new_value: 50 times the ui scale percentage
    """
    setting_value = f'{new_value / 50:.2f}'
    self.settings.setValue('ui_scale', setting_value)
    return setting_value


def set_live_scale_setting(self, new_value: int):
    """
    Calculates new_value / 50 and stores it to settings.

    Parameters:
    - :param new_value: 50 times the live scale percentage
    """
    setting_value = f'{new_value / 50:.2f}'
    self.settings.setValue('live_scale', setting_value)
    return setting_value


def set_sto_logpath_setting(self, entry: QLineEdit):
    """
    Formats and stores new logpath to settings.

    Parameters:
    - :param entry: the entry that holds the path
    """
    formatted_path = format_path(entry.text())
    self.settings.setValue('sto_log_path', formatted_path)
    entry.setText(formatted_path)


def browse_sto_logpath(self, entry: QLineEdit):
    """
    Opens prompt to select new logpath and stores it to settings.

    Parameters:
    - :param entry: the entry that holds the path
    """
    current_path = entry.text()
    if not current_path:
        current_path = self.app_dir
    new_path = self.browse_path(os.path.dirname(current_path), 'Logfile (*.log);;Any File (*.*)')
    if new_path:
        formatted_path = format_path(new_path)
        self.settings.setValue('sto_log_path', formatted_path)
        entry.setText(formatted_path)


def copy_live_data_callback(self):
    """
    Copies the data from the live parser table.
    """
    data_model = self.widgets.live_parser_table.model()
    cell_data = data_model._data
    output = list()
    for row in cell_data:
        output.append(f"`{row[0][0]}{row[0][1]}`: {row[1]:,.2f} ({row[2]:.1f}s)")
    output = '{ OSCR } DPS (Combat time): ' + ' | '.join(output)
    self.app.clipboard().setText(output)


def expand_overview_table(self):
    """
    Shows the overview table
    """
    self.widgets.overview_table_frame.show()


def collapse_overview_table(self):
    """
    Hides the overview table
    """
    self.widgets.overview_table_frame.hide()


def expand_analysis_graph(self):
    """
    Shows the analysis graph
    """
    self.widgets.analysis_graph_tabber.show()
    self.settings.setValue('analysis_graph', True)


def collapse_analysis_graph(self):
    """
    Hides the analysis graph
    """
    self.widgets.analysis_graph_tabber.hide()
    self.settings.setValue('analysis_graph', False)


def confirm_trim_logfile(self):
    """
    Prompts the user to confirm whether the logfile should be trimmed
    """
    title = tr('Trim Logfile')
    text = tr(
            'Trimming the logfile will delete all combats except for the most recent combat. '
            'Continue?')
    if confirmation_dialog(self, title, text):
        success = trim_logfile(self)
        if success:
            show_message(self, title, tr('Logfile has been trimmed.'))
        else:
            show_message(self, title, tr('Trimming the logfile failed.'), 'error')


def trim_logfile(self) -> bool:
    """
    Removes all combats but the most recent one from a logfile

    :return: True if successful, False if not
    """
    log_path = os.path.abspath(self.entry.text())
    if self.parser.log_path == log_path:
        self.parser.export_combat(0, log_path)
    else:
        combats = self.parser.isolate_combats(log_path, 1)
        if len(combats) < 1:
            return False
        combat = combats[0]
        extract_bytes(log_path, log_path, combat[5], combat[6])
    return True


def repair_logfile(self):
    """
    Repairs current logfile.
    """
    log_path = os.path.abspath(self.entry.text())
    if os.path.isfile(log_path):
        res = oscr_repair_logfile(log_path, self.config['templog_folder_path'])
        if res == '':
            show_message(self, tr('Repair Logfile'), tr('The Logfile has been repaired.'))
        elif res == 'PermissionError':
            error_message = ('The Logfile could not be repaired due to a permission error. '
                             'Make sure the selected logfile can be overwritten without elevated '
                             'permissions.')
            show_message(self, tr('Permission Error'), tr(error_message), 'error')
    else:
        show_message(
                self, tr('Repair Logfile'),
                tr('The Logfile you are trying to open does not exist.'), 'warning')


def extract_combats(self, selected_indices: list):
    """
    Extracts combats in `selected_indices` from current logfile and prompts the user to select a
    file to write them to.

    Parameters:
    - :param selected_indices: list of model indices refering to the selected combats
    """
    combat_intervals = list()
    for index in selected_indices:
        data = index.data()
        combat_intervals.append((data[5], data[6]))
    combat_intervals.sort(key=lambda element: element[0])
    source_path = self.entry.text()
    target_path = browse_path(
            self, os.path.dirname(source_path), 'Logfile (*.log);;Any File (*.*)', save=True)
    if target_path != '':
        compose_logfile(
                source_path, target_path, combat_intervals, self.config['templog_folder_path'])
        show_message(self, tr('Split Logfile'), tr('Logfile has been saved.'))


def populate_split_combats_list(self, combat_list):
    """
    Isolates all combats in the current logfile and inserts them into `combat_list`

    Parameters:
    - :param combat_list: QListView with CombatModel to insert the isolated combats into
    """
    combats = self.parser.isolate_combats(self.entry.text())
    combat_list.model().set_items(combats)
