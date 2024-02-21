from multiprocessing import Pipe, Process
import os

from PyQt6.QtCore import QThread, pyqtSignal, Qt

from OSCR import OSCR, TREE_HEADER

from .datamodels import TreeModel, TreeSortingProxy
from .displayer import create_overview
from .iofunctions import store_json
from .widgetbuilder import show_warning


class CustomThread(QThread):
    """
    Subclass of QThread able to execute an arbitrary function in a seperate thread.
    """
    result = pyqtSignal(tuple)

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
        analysis_thread.start()

    # subsequent run / click on older combat
    elif isinstance(combat_id, int) and combat_id != self.current_combat_id:
        if combat_id == -1: return
        get_data(self, combat_id)
        self.current_combat_id = combat_id
        analysis_thread = CustomThread(self.window, lambda: parser.full_combat_analysis(combat_id))
        analysis_thread.result.connect(lambda result: analysis_data_slot(self, result))
        analysis_thread.start()

    create_overview(self)

    #self.widgets['main_menu_buttons'][1].setDisabled(True)
    # reset tabber
    self.widgets['main_tabber'].setCurrentIndex(0)
    self.widgets['overview_tabber'].setCurrentIndex(0)

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
    self.widgets['main_menu_buttons'][1].setDisabled(False)

def populate_analysis(self, damage_out_item):
    """
    Populates the Analysis' treeview table.
    """
    damage_out_table = self.widgets['analysis_table_dout']
    damage_out_model = TreeModel(damage_out_item, self.theme_font('tree_table_header'),
                self.theme_font('tree_table'),
                self.theme_font('', self.theme['tree_table']['::item']['font']))
    damage_out_table.setModel(damage_out_model)
    damage_out_table.expand(damage_out_model.index(0, 0, damage_out_model.createIndex(0, 0, damage_out_model._root)))
    damage_out_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    update_shown_columns_dmg(self)
    """table = self.widgets['analysis_table_dout']
    model = TreeModel(DAMAGE_HEADER, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    model.populate_dout(self.main_data, 1)
    table.setModel(model)
    table.expand(model.index(0, 0))
    resize_tree_table(table)

    dtaken_table = self.widgets['analysis_table_dtaken']
    dtaken_model = TreeModel(DAMAGE_HEADER, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    dtaken_model.populate_in(self.main_data, 3)
    dtaken_table.setModel(dtaken_model)
    dtaken_table.expand(dtaken_model.index(0, 0))
    resize_tree_table(dtaken_table)

    hin_table = self.widgets['analysis_table_hin']
    hin_model = TreeModel(HEAL_HEADER, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    hin_model.populate_in(self.main_data, 6)
    hin_table.setModel(hin_model)
    hin_table.expand(hin_model.index(0, 0))
    resize_tree_table(hin_table)

    hout_table = self.widgets['analysis_table_hout']
    hout_model = TreeModel(HEAL_HEADER, self.theme_font('tree_table_header'),
            self.theme_font('tree_table'),
            self.theme_font('', self.theme['tree_table']['::item']['font']))
    hout_model.populate_dout(self.main_data, 4)
    hout_table.setModel(hout_model)
    hout_table.expand(hout_model.index(0, 0))
    resize_tree_table(hout_table)
    
    self.update_shown_columns_heal()"""

def update_shown_columns_dmg(self):
    """
    Hides / shows columns of the dmg analysis table according to self.settings['dmg_columns']
    """
    dout_table = self.widgets['analysis_table_dout']
    #dtaken_table = self.widgets['analysis_table_dtaken']
    for i in range(self.settings.value('dmg_columns_length', type=int)):
        state = self.settings.value(f'dmg_columns|{i}')
        if state:
            dout_table.showColumn(i+1)
            #dtaken_table.showColumn(i+1)
        else:
            dout_table.hideColumn(i+1)
            #dtaken_table.hideColumn(i+1)

def update_shown_columns_heal(self):
    """
    Hides / shows columns of the heals analysis table according to self.settings['dmg_columns']
    """
    return
    hout_table = self.widgets['analysis_table_hout']
    hin_table = self.widgets['analysis_table_hin']
    for i, state in enumerate(self.settings['heal_columns']):
        if state:
            hout_table.showColumn(i+1)
            hin_table.showColumn(i+1)
        else:
            hout_table.hideColumn(i+1)
            hin_table.hideColumn(i+1)
        store_json(self.settings, self.config['settings_path'])
        
def resize_tree_table(tree):
    """
    Resizes the columns of the given tree table to fit its contents

    Parameters:
    - :param tree: QTreeView -> tree to be resized
    """
    for col in range(tree.header().count()):
        width = max(tree.sizeHintForColumn(col), tree.header().sectionSizeHint(col)) + 5
        tree.header().resizeSection(col, width)
