from multiprocessing import Pipe, Process
import os

from PySide6.QtCore import QThread, Signal, Qt

from OSCR import OSCR

from .datamodels import DamageTreeModel, HealTreeModel
from .displayer import create_overview
from .widgetbuilder import show_warning


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
    self.parser1 = OSCR()
    # self.parser2 = OSCR()

def analyze_log_callback(self, combat_id=None, path=None, parser_num: int = 1):
    """
    Wrapper function for retrieving and showing data. Callback of "Analyse" and "Refresh" button.
    
    Parameters:
    - :param combat_id: id of older combat (0 -> latest combat in the file; len(...) - 1 -> oldest combat)
    - :param path: path to combat log file
    """
    if parser_num == 1:
        parser: OSCR = self.parser1
    elif parser_num == 2:
        parser: OSCR = self.parser2
    else:
        return
    
    # initial run / click on the Analyze buttonQGuiApplication
    if combat_id is None:
        if not path or not os.path.isfile(path):
            show_warning(self, 'Invalid Logfile', 'The Logfile you are trying to open does not exist.')
            return
        if path != self.settings.value('log_path'):
            self.settings.setValue('log_path', path)

        get_data(self, combat=None, path=path)
        self.current_combats.clear()
        self.current_combats.addItems(parser.analyzed_combats)
        self.current_combats.setCurrentRow(0)
        self.current_combat_id = 0
        self.current_combat_path = path
        analysis_thread = CustomThread(self.window, lambda: parser.full_combat_analysis(0))
        analysis_thread.result.connect(lambda result: analysis_data_slot(self, result))
        analysis_thread.start(QThread.Priority.IdlePriority)

    # subsequent run / click on older combat
    elif isinstance(combat_id, int) and combat_id != self.current_combat_id:
        if combat_id == -1: return
        get_data(self, combat_id)
        self.current_combat_id = combat_id
        analysis_thread = CustomThread(self.window, lambda: parser.full_combat_analysis(combat_id))
        analysis_thread.result.connect(lambda result: analysis_data_slot(self, result))
        analysis_thread.start(QThread.Priority.IdlePriority)

    create_overview(self)

    # reset tabber
    self.widgets.main_tabber.setCurrentIndex(0)
    self.widgets.overview_tabber.setCurrentIndex(0)

def copy_summary_callback(self):
    """
    Callback to set the combat summary of the active combat to the user's clippboard
    """

    if not self.parser1.active_combat:
        return

    parts = [
        "OSCR",
        f"{self.parser1.active_combat.map}",
        f"{self.parser1.active_combat.difficulty}",
        "DPS",
    ]
    players = sorted(
        self.parser1.active_combat.player_dict.items(),
        reverse=True,
        key=lambda player: player[1].DPS,
    )
    for player in players:
        parts.append(f"{player[1].handle} {player[1].DPS:,.0f}")
    summary = " | ".join(parts)

    self.app.clipboard().setText(summary)


def get_data(self, combat: int | None = None, path: str | None = None):
    """Interface between OSCRUI and OSCR. 
    Uses OSCR class to analyze log at path"""

    # new log file
    if combat is None:
        self.parser1.log_path = path
        try:
            self.parser1.analyze_log_file()
        except FileExistsError:
            # TODO show annoying message prompting to split the logfile
            self.parser1.analyze_massive_log_file()
        self.parser1.shallow_combat_analysis(0)
        
    # same log file, old combat
    else:
        self.parser1.shallow_combat_analysis(combat)

def analysis_data_slot(self, item_tuple: tuple):
    """
    Inserts the data retrieved from the parser into the respective tables

    Parameters:
    - :param item_tuple: tuple containing only the root item of the data model
    """
    populate_analysis(self, *item_tuple)
    self.widgets.main_menu_buttons[1].setDisabled(False)

def populate_analysis(self, root_items: tuple):
    """
    Populates the Analysis' treeview table.
    """
    damage_out_item, damage_in_item, heal_out_item, heal_in_item = root_items

    damage_out_table = self.widgets.analysis_table_dout
    damage_out_model = DamageTreeModel(damage_out_item, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    damage_out_table.setModel(damage_out_model)
    damage_out_table.expand(damage_out_model.index(0, 0, 
            damage_out_model.createIndex(0, 0, damage_out_model._root)))
    damage_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)

    damage_in_table = self.widgets.analysis_table_dtaken
    damage_in_model = DamageTreeModel(damage_in_item, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    damage_in_table.setModel(damage_in_model)
    damage_in_table.expand(damage_in_model.index(0, 0, 
            damage_in_model.createIndex(0, 0, damage_in_model._root)))
    damage_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)

    heal_out_table = self.widgets.analysis_table_hout
    heal_out_model = HealTreeModel(heal_out_item, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    heal_out_table.setModel(heal_out_model)
    heal_out_table.expand(heal_out_model.index(0, 0, 
            damage_in_model.createIndex(0, 0, heal_out_model._root)))
    heal_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)

    heal_in_table = self.widgets.analysis_table_hin
    heal_in_model = HealTreeModel(heal_in_item, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    heal_in_table.setModel(heal_in_model)
    heal_in_table.expand(heal_in_model.index(0, 0, 
            damage_in_model.createIndex(0, 0, heal_in_model._root)))
    heal_in_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    
    update_shown_columns_dmg(self)
    update_shown_columns_heal(self)

def update_shown_columns_dmg(self):
    """
    Hides / shows columns of the dmg analysis tables.
    """
    dout_table = self.widgets.analysis_table_dout
    dtaken_table = self.widgets.analysis_table_dtaken
    for i in range(self.settings.value('dmg_columns_length', type=int)):
        state = self.settings.value(f'dmg_columns|{i}')
        if state:
            dout_table.showColumn(i+1)
            dtaken_table.showColumn(i+1)
        else:
            dout_table.hideColumn(i+1)
            dtaken_table.hideColumn(i+1)

def update_shown_columns_heal(self):
    """
    Hides / shows columns of the heal analysis tables.
    """
    hout_table = self.widgets.analysis_table_hout
    hin_table = self.widgets.analysis_table_hin
    for i in range(self.settings.value('heal_columns_length', type=int)):
        state = self.settings.value(f'heal_columns|{i}')
        if state:
            hout_table.showColumn(i+1)
            hin_table.showColumn(i+1)
        else:
            hout_table.hideColumn(i+1)
            hin_table.hideColumn(i+1)
        
def resize_tree_table(tree):
    """
    Resizes the columns of the given tree table to fit its contents.

    Parameters:
    - :param tree: QTreeView -> tree to be resized
    """
    for col in range(tree.header().count()):
        width = max(tree.sizeHintForColumn(col), tree.header().sectionSizeHint(col)) + 5
        tree.header().resizeSection(col, width)
