from pathlib import Path
from threading import Thread

from PySide6.QtCore import QObject, Signal

from OSCR import OSCR, extract_bytes
from OSCR.combat import Combat

from .config import OSCRConfig, OSCRSettings
from .datamodels import CombatModel
from .dialogs import show_message
from .iofunctions import browse_path, save_to_json
from .translation import tr


class ParserBridge(QObject):
    """Contains logic to connect with the OSCR parser"""

    completed_combat = Signal(object)
    parser_error = Signal(object)

    def __init__(self, global_settings: OSCRSettings, global_config: OSCRConfig):
        """
        Interface that connects with the OSCR parser

        Parameters:
        - :param parser_settings: dictionary containing settings for the parser
        """
        self._global_settings: OSCRSettings = global_settings
        self._global_config: OSCRConfig = global_config
        self._parser = OSCR(settings=self.parser_settings)
        self.completed_combat.connect(self.insert_combat)
        self.parser_error.connect(self.show_parser_error)
        self._parser.combat_analyzed_callback = lambda combat: self.completed_combat.emit(combat)
        self._parser.error_callback = lambda error: self.parser_error.emit(error)
        self._thread: Thread | None = None
        self.analyzed_combats: CombatModel = CombatModel()
        self.current_combat_id: int = -1

    @property
    def parser_settings(self) -> dict:
        """
        Returns settings relevant to the parser
        """
        relevant_settings = (
            'combats_to_parse', 'seconds_between_combats',
            'graph_resolution', 'combat_min_lines')
        settings = {'excluded_event_ids': self._global_config.excluded_event_ids}
        for setting_key in relevant_settings:
            setting = getattr(self._global_settings, setting_key)
            if setting != '':
                settings[setting_key] = setting
        settings['templog_folder_path'] = str(self._global_config.templog_folder_path.absolute())
        return settings

    @property
    def combat_list(self) -> list[Combat]:
        return self._parser.combats

    @property
    def current_combat(self) -> Combat:
        return self._parser.combats[self.current_combat_id]

    def analyze_log_file(self, path: Path, hidden_path: bool = False):
        """
        Starts analyzation of current logfile.

        Parameters:
        - :param path: path to combat log file, set to
        - :param hidden_path: True when settings should not be updated with log path
        """
        if not path.is_file():
            show_message(
                self, tr('Invalid Logfile'),
                tr('The Logfile you are trying to open does not exist.'), 'warning')
            return
        if self._thread is not None and self._thread.is_alive():
            # TODO Show feedback
            return
        if not hidden_path and path != self._global_settings.log_path:
            self._global_settings = path

        self._parser.reset_parser()
        self.analyzed_combats.clear()
        self._parser.log_path = str(path)
        # Only analyze 1 combat for best performance, see self.insert_combat for remaining combats
        self._thread = Thread(target=self._parser.analyze_log_file, kwargs={'max_combats': 1})
        self._thread.start()

        # TODO switch tabs
        # switch_main_tab()
        # switch_overview_tab()

    def analyze_log_background(self, amount: int):
        """
        Analyzes older combats from current combatlog in the background.

        Parameters:
        - :param amount: amount of combats to analyze
        """
        # TODO what happens if no combat is analyzed already
        if self._thread is not None and not self._thread.is_alive():
            self._thread = Thread(
                target=self._parser.analyze_log_file_mp, kwargs={'max_combats': amount})
            self._thread.start()
        # TODO feedback

    def insert_combat(self, combat: Combat):
        """
        Called by parser as soon as combat has been analyzed. Inserts combat into UI.

        Parameters:
        - :param combat: analyzed combat
        """
        difficulty = combat.difficulty if combat.difficulty is not None else ''
        combat_time = combat.start_time
        date = f'{combat_time.year}-{combat_time.month:02d}-{combat_time.day:02d}'
        time = f'{combat_time.hour:02d}:{combat_time.minute:02d}:{combat_time.second:02d}'
        self.analyzed_combats.insert_item((combat.id, combat.map, date, time, difficulty))
        if combat.id == 0:
            self.current_combat_id = 0
            # TODO replace with new functions
            # self.current_combats.setCurrentIndex(self.analyzed_combats.createIndex(0, 0, 0))
            # create_overview(self, combat)
            # populate_analysis(self, combat)
            self.analyze_log_background(self._global_settings.combats_to_parse - 1)

    def show_parser_error(self, error: BaseException):
        """
        Handles error raised by parser during analyzation of logfile.

        Parameters:
        - :param error: captured error with optionally additional data in the error.args attribute
        """
        pass

    def show_combat(self, index: int):
        """
        Shows analyzed combat. Combat must be isolated and available in the parsers `combat`
        attribute.

        Parameters:
        - :param index: index of the combat in the parsers combat list
        """
        combat = self._parser.combats[index]
        self.current_combat_id = combat.id
        # create_overview(self, combat)
        # populate_analysis(self, combat)
        # TODO replace with new methods

    def save_combat(self, combat_info: tuple[int, str, str, str, str] | None):
        """
        Callback for save button.

        Parameters:
        - :param combat_info: tuple of combat-identifying data (id, map, date, time, difficulty)
        """
        if combat_info is None or combat_info[0] >= len(self._parser.combats):
            return
        combat = self._parser.combats[combat_info[0]]
        filename = combat.map
        if combat.difficulty is not None and combat.difficulty != '':
            filename += ' ' + combat.difficulty
        filename += f' {combat.start_time.strftime("%Y-%m-%d %H.%M")}.log'
        preset_path = Path(self._parser.log_path).parent / filename
        path = browse_path(preset_path, 'Logfile (*.log);;Any File (*.*)', save=True)
        if path is not None:
            self._parser.export_combat(combat_info[0], path)
        # TODO feedback

    def export_combat_json(self, combat_info: tuple[int, str, str, str, str] | None):
        """
        Exports current combat to JSON file

        Parameters:
        - :param combat_info: tuple of combat-identifying data (id, map, date, time, difficulty)
        """
        if combat_info is None or combat_info[0] >= len(self._parser.combats):
            return
        combat = self._parser.combats[combat_info[0]]
        filename = combat.map
        if combat.difficulty is not None and combat.difficulty != '':
            filename += ' ' + combat.difficulty
        filename += f' {combat.start_time.strftime("%Y-%m-%d %H.%M")}.json'
        preset_path = Path(self._parser.log_path) / filename
        path = browse_path(preset_path, 'JSON File (*.json);;Any File (*.*)', save=True)
        if path is not None:
            save_to_json(path, combat.get_export())
        # TODO feedback

    def trim_logfile(self, path: Path) -> bool:
        """
        Removes all combats but the most recent one from a logfile

        Parameters:
        - :param path: path of logfile to be trimmed

        :return: True if successful, False if not
        """
        # TODO feedback
        if Path(self._parser.log_path) == path:
            self._parser.export_combat(0, path)
        else:
            combats = self._parser.isolate_combats(path, 1)
            if len(combats) < 1:
                return False
            combat = combats[0]
            extract_bytes(path, path, combat[5], combat[6])
        return True

    def populate_split_combats_list(
            self, combat_list: CombatModel, log_file: Path | None = None) -> bool:
        """
        Isolates all combats in the current logfile and inserts them into `combat_list`

        Parameters:
        - :param combat_list: CombatModel to insert the isolated combats into
        - :param log_file: path to log file to use instead of current log file (optional)

        :return: True if successful, False if not
        """
        if log_file is None:
            log_path = self._parser.log_path
        elif log_file.is_file():
            log_path = str(log_file)
        else:
            # TODO feedback
            return False
        combats = self._parser.isolate_combats(log_path)
        combat_list.set_items(combats)
