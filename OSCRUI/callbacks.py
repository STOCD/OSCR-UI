import os

from PySide6.QtWidgets import QFileDialog, QLineEdit

from OSCR import split_log_by_combat, split_log_by_lines
from .iofunctions import browse_path
from .textedit import format_path


def browse_log(self, entry: QLineEdit):
    """
    Callback for browse button.

    Parameters:
    - :param entry: QLineEdit -> path entry line widget
    """
    current_path = entry.text()
    if current_path != '':
        path = self.browse_path(
                os.path.dirname(current_path), 'Logfile (*.log);;Any File (*.*)')
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
    if not self.parser1.active_combat:
        return
    base_dir = os.path.dirname(self.entry.text())
    if not base_dir:
        base_dir = self.app_dir
    path = self.browse_path(base_dir, 'Logfile (*.log);;Any File (*.*)', save=True)
    if path:
        self.parser1.export_combat(combat_num, path)


def navigate_log(self, direction: str):
    """
    Load older or newer combats.

    Parameters:
    - :param direction: "up" -> load newer combats; "down" -> load older combats
    """
    logfile_changed = self.parser1.navigate_log(direction)
    selected_row = self.current_combats.currentRow()
    self.current_combats.clear()
    self.current_combats.addItems(self.parser1.analyzed_combats)
    if logfile_changed:
        self.current_combats.setCurrentRow(0)
        self.current_combat_id = None
        self.analyze_log_callback(0, parser_num=1)
    else:
        self.current_combats.setCurrentRow(selected_row)
    self.widgets.navigate_up_button.setEnabled(self.parser1.navigation_up)
    self.widgets.navigate_down_button.setEnabled(self.parser1.navigation_down)


def switch_analysis_tab(self, tab_index: int):
    """
    Callback for tab switch buttons; switches tab and sets active button.

    Parameters:
    - :param tab_index: index of the tab to switch to
    """
    self.widgets.analysis_tabber.setCurrentIndex(tab_index)
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


def switch_map_tab(self, tab_index: int):
    """
    Callback for tab switch buttons; switches tab and sets active button.

    Parameters:
    - :param tab_index: index of the tab to switch to
    """
    self.widgets.map_tabber.setCurrentIndex(tab_index)
    for index, button in enumerate(self.widgets.map_menu_buttons):
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


def favorite_button_callback(self):
    """
    Adds ladder to / removes ladder from favorites list. Updates settings.
    """
    # Add current ladder to favorites
    if self.widgets.map_tabber.currentIndex() == 0:
        current_ladder = self.widgets.ladder_selector.currentItem().text()
        favorite_ladders = self.settings.value('favorite_ladders', type=list)
        if current_ladder not in favorite_ladders:
            favorite_ladders.append(current_ladder)
            self.settings.setValue('favorite_ladders', favorite_ladders)
            self.widgets.favorite_ladder_selector.addItem(current_ladder)
    # Remove current ladder from favorites
    else:
        current_item = self.widgets.favorite_ladder_selector.currentItem()
        current_ladder = current_item.text()
        favorite_ladders = self.settings.value('favorite_ladders', type=list)
        if current_ladder in favorite_ladders:
            favorite_ladders.remove(current_ladder)
            self.settings.setValue('favorite_ladders', favorite_ladders)
            row = self.widgets.favorite_ladder_selector.row(current_item)
            self.widgets.favorite_ladder_selector.takeItem(row)


def set_graph_resolution_setting(self, setting_text: str):
    """
    Calculates inverse of setting_text and stores it to settings.

    Parameters:
    - :param setting_text: data points per second
    """
    try:
        value = round(1 / int(setting_text), 1)
        self.settings.setValue('graph_resolution', value)
    except (ValueError, ZeroDivisionError):
        return


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


def auto_split_callback(self, path: str):
    """
    Callback for auto split button
    """
    folder_path = QFileDialog.getExistingDirectory(
            self.window, 'Select Folder', os.path.dirname(path))
    if folder_path:
        split_log_by_lines(
                path, folder_path, self.settings.value('split_log_after', type=int),
                self.settings.value('combat_distance', type=int))


def combat_split_callback(self, path: str, first_num: str, last_num: str):
    """
    Callback for combat split button
    """
    target_path = browse_path(self, path, 'Logfile (*.log);;Any File (*.*)', True)
    if target_path:
        split_log_by_combat(
                path, target_path, int(first_num), int(last_num),
                self.settings.value('seconds_between_combats', type=int),
                self.settings.value('excluded_event_ids', type=list))
