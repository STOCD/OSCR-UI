from multiprocessing import Pipe, Process
import os

from PyQt6.QtCore import QThread, pyqtSignal

from .OSCR import OSCR

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
    
    # initial run / click on the Analyze button
    if combat_id is None:
        if not path or not os.path.isfile(path):
            show_warning(self, 'Invalid Logfile', 'The Logfile you are trying to open does not exist.')
            return
        if path != self.settings['log_path']:
            self.settings['log_path'] = path
            store_json(self.settings, self.config['settings_path'])

        get_data(self, combat=None, path=path)
        self.current_combats.clear()
        self.current_combats.addItems(parser.analyzed_combats)
        self.current_combats.setCurrentRow(0)
        self.current_combat_id = 0
        self.current_combat_path = path

    # subsequent run / click on older combat
    elif isinstance(combat_id, int) and combat_id != self.current_combat_id:
        if combat_id == -1: return
        get_data(self, combat_id)
        self.current_combat_id = combat_id

    create_overview(self)

    self.widgets['main_menu_buttons'][1].setDisabled(True)
    # reset tabber
    self.widgets['main_tabber'].setCurrentIndex(0)
    self.widgets['overview_tabber'].setCurrentIndex(0)

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

def get_analysis_data(self, path, id=None):
    """
    Starts new process using the multiprcessing module to retrieve full combat data.
    Populates the Analysis table. Don't use this in the main thread as it blocks execution.

    Parameters:
    - :param path: path to combat log file
    - :param id: id of older combat (0 -> oldest combat in the file; len(...) - 1 -> latest combat)
    """
    receiver, sender = Pipe()
    analysis_process = Process(target=analysis_parser, args=(path, sender, id))
    analysis_process.start()
    data = receiver.recv() # waits for the pipe to receive data from the process
    self.main_data = data
    """with open('new_data.json', 'w') as f:
        json.dump(data, f)"""
    self.populate_analysis()
    self.widgets['main_menu_buttons'][1].setDisabled(False)

def analysis_parser(path, pipe, id=None):
    """
    Retrieves combat analysis data from parser. Used in different process.

    Parameters:
    - :param path: path of the combat log to be analyzed
    - :param pipe: pipe to transmit results back through
    - :param id: older combat id (optional)
    """
    parser = OSCR.parser()
    if id is None:
        parser.readCombatShallow(path)
        uiD, dmgI, healI, uiID, _, _, _, _, _, npcdmg, npcdps = parser.readCombatFull(path)
    elif isinstance(id, int):
        parser.readCombatShallow(path)
        uiD, dmgI, healI, uiID, _, _, _, _, _, npcdmg, npcdps = parser.readPreviousCombatFull(id)
    pipe.send(uiD)

def populate_analysis(self):
    """
    Populates the Analysis' treeview table.
    """
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
    self.update_shown_columns_dmg()
    self.update_shown_columns_heal()"""

def update_shown_columns_dmg(self):
    """
    Hides / shows columns of the dmg analysis table according to self.settings['dmg_columns']
    """
    dout_table = self.widgets['analysis_table_dout']
    dtaken_table = self.widgets['analysis_table_dtaken']
    for i, state in enumerate(self.settings['dmg_columns']):
        if state:
            dout_table.showColumn(i+1)
            dtaken_table.showColumn(i+1)
        else:
            dout_table.hideColumn(i+1)
            dtaken_table.hideColumn(i+1)
    store_json(self.settings, self.config['settings_path'])

def update_shown_columns_heal(self):
    """
    Hides / shows columns of the heals analysis table according to self.settings['dmg_columns']
    """
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