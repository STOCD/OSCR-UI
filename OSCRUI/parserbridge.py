from pathlib import Path
from threading import Thread
from traceback import format_exception

from PySide6.QtCore import QModelIndex, QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from OSCR import (
    compose_logfile as oscr__compose_logfile, OSCR, extract_bytes as oscr__extract_bytes,
    repair_logfile as oscr__repair_logfile, TABLE_HEADER)
from OSCR.combat import Combat

from .analysisgraphs import AnalysisGraphs
from .analysistables import AnalysisTables
from .config import OSCRConfig, OSCRSettings
from .datamodels import CombatModel, DamageTreeModel, HealTreeModel, OverviewTableModel
from .dialogs import DialogsWrapper
from .iofunctions import browse_path, save_to_json
from .textedit import format_damage_number
from .translation import tr
from .widgetmanager import WidgetManager


class ParserBridge(QObject):
    """Contains logic to connect with the OSCR parser"""

    completed_combat = Signal(Combat)
    parser_error = Signal(object)
    parser_status = Signal(str)
    status_message = Signal(str, str)

    def __init__(
            self, global_settings: OSCRSettings, global_config: OSCRConfig, widgets: WidgetManager,
            dialogs: DialogsWrapper):
        """
        Interface that connects with the OSCR parser

        Parameters:
        - :param global_settings: settings of the app
        - :param global_config: config of the app
        - :param widgets: stores widgets
        - :param dialogs: used to access dialogs
        """
        super().__init__()
        self._global_settings: OSCRSettings = global_settings
        self._global_config: OSCRConfig = global_config
        self._parser = OSCR(settings=self.parser_settings)
        self.completed_combat.connect(self.insert_combat)
        self.parser_error.connect(self.show_parser_error)
        self._parser.combat_analyzed_callback = lambda combat: self.completed_combat.emit(combat)
        self._parser.task_finished_callback = self.analyzation_finished
        self._thread: Thread | None = None
        self.analyzed_combats: CombatModel = CombatModel()
        self.current_combat_id: int = -1
        self.overview_table_model: OverviewTableModel = OverviewTableModel()
        self.damage_out_model: DamageTreeModel = DamageTreeModel()
        self.damage_in_model: DamageTreeModel = DamageTreeModel()
        self.heal_out_model: HealTreeModel = HealTreeModel()
        self.heal_in_model: HealTreeModel = HealTreeModel()
        self._widgets: WidgetManager = widgets
        self._dialogs: DialogsWrapper = dialogs
        self._tables: AnalysisTables
        self._graphs: AnalysisGraphs

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

    def set_parser_status(self, status: str, message: str, description: str = ''):
        """
        Notifies that parser status has changed.

        Parameters:
        - :param status: name of the status to display
        - :param message: message describing the status
        - :param description: long description of the status (optional)
        """
        self.parser_status.emit(status)
        self.status_message.emit(message, description)

    def show_info(self, message: str, description: str = ''):
        """
        Notifies that an information message should be shown.

        Parameters:
        - :param message: short information message
        - :param description: description of the short message
        """
        self.status_message.emit(message, description)

    def analyzation_finished(self, new_combats: list[int]):
        """
        Adds information about new combats to log.

        Parameters:
        - :param new_combats: contains ids of combats that have been added
        """
        if len(new_combats) == 0:
            desc = tr(
                'All combats in this log file have been analyzed. To re-analyze the log file, '
                'click the "Analyze" button.')
            self.set_parser_status('ready', tr('All combats analyzed'), desc)
        else:
            details = (
                tr('Successfully analyzed') + f' {len(new_combats)} ' + tr('new combats with ids')
                + ' ' + ', '.join(map(str, new_combats)))
            self.show_info(tr('Combats analyzed'), details)
            self.set_parser_status('ready', tr('Idle'))

    def analyze_log_file(self, path: Path, hidden_path: bool = False):
        """
        Starts analyzation of current logfile.

        Parameters:
        - :param path: path to combat log file, set to
        - :param hidden_path: True when settings should not be updated with log path
        """
        if not path.is_file():
            self.show_info(tr('Invalid logfile'), tr('Please select an existing file to parse.'))
            return
        if self._thread is not None and self._thread.is_alive():
            desc = tr(
                'The parser is currently analyzing a log file, please wait for it to finish before '
                'analyzing another log file.')
            self.show_info(tr('Parser busy'), desc)
            return
        if not hidden_path and path != self._global_settings.log_path:
            self._global_settings.log_path = str(path)

        self._parser.reset_parser()
        self.analyzed_combats.clear()
        self._parser.log_path = str(path)
        # Only analyze 1 combat for best performance, see self.insert_combat for remaining combats
        self._thread = Thread(target=self._parser.analyze_log_file, kwargs={'max_combats': 1})
        self._thread.start()

        self.set_parser_status('active', tr('Analyzing Logfile'))
        self._widgets.switch_main_tab(0)
        self._widgets.switch_overview_tab(self._global_settings.first_overview_tab)

    def analyze_log_background(self, amount: int = -1):
        """
        Analyzes older combats from current combatlog in the background.

        Parameters:
        - :param amount: amount of combats to analyze (optional)
        """
        # TODO what happens if no combat is analyzed already
        if self._thread is not None and not self._thread.is_alive():
            if amount < 1:
                amount = self._global_settings.combats_to_parse
            self._thread = Thread(
                target=self._parser.analyze_log_file_mp, kwargs={'max_combats': amount})
            self._thread.start()
            self.set_parser_status('active', tr('Analyzing Logfile'))
        else:
            desc = tr(
                'The parser is currently analyzing a log file, please wait for it to finish before '
                'analyzing another log file.')
            self.show_info(tr('Parser busy'), desc)

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
            self._widgets.combats_list.setCurrentIndex(self.analyzed_combats.createIndex(0, 0, 0))
            self.show_combat(combat=combat)
            self.show_info(tr('Combat analyzed'), tr('Successfully analyzed combat with id 0.'))
            self.analyze_log_background(self._global_settings.combats_to_parse - 1)

    def populate_analysis(self, combat: Combat):
        """
        Inserts the data of `combat` into the analysis treeview tables by replacing the underlying
        datamodel.

        Parameters:
        - :param combat: combat containing the data to show
        """
        damage_out_item, damage_in_item, heal_out_item, heal_in_item = combat.root_items
        self.damage_out_model.set_data(damage_out_item)
        self.damage_in_model.set_data(damage_in_item)
        self.heal_out_model.set_data(heal_out_item)
        self.heal_in_model.set_data(heal_in_item)

    def show_parser_error(self, error: BaseException):
        """
        Handles error raised by parser during analyzation of logfile.

        Parameters:
        - :param error: captured error with optionally additional data in the error.args attribute
        """
        default_message, *additional_messages = error.args
        error.args = (default_message,)
        error_text = ''.join(format_exception(error))
        if len(additional_messages) > 0:
            error_text += '\n\n++++++++++++++++++++++++++++++++++++++++++++++++++\n\n'
            error_text += '\n'.join(additional_messages)
        error_message = tr(
            'An error occurred while parsing the selected combatlog. You can try repairing the '
            'log file using the repair functionality in the "Manage Logfile" dialog. If the error '
            'persists, please report it to the #oscr-support channel in the STOBuilds Discord.')
        self._dialogs.show_error(tr('Parser Error'), error_message, error_text)

    def show_combat(self, index: int = -1, combat: Combat | None = None):
        """
        Shows analyzed combat. Combat must be isolated and available in the parsers `combat`
        attribute or given as argument.

        Parameters:
        - :param index: index of the combat in the parsers combat list
        - :param combat: combat to show
        """
        if combat is None:
            combat = self._parser.combats[index]
            self.current_combat_id = combat.id

        overview_table = list()
        dps_graph_data = dict()
        dmg_bar_data = dict()
        time_data = dict()
        for player in combat.players.values():
            overview_table.append((*player,))
            dps_graph_data[player.handle] = player.DPS_graph_data
            dmg_bar_data[player.handle] = player.DMG_graph_data
            time_data[player.handle] = player.graph_time
        overview_table.sort(key=lambda x: x[0])
        if len(overview_table) > 0:
            table_cell_data = [list(line[2:]) for line in overview_table]
            table_index = [line[0] + line[1] for line in overview_table]
            self.overview_table_model.set_data(table_cell_data, TABLE_HEADER, table_index)
            self._graphs.plot_overview_data(overview_table, dps_graph_data, dmg_bar_data, time_data)
        else:
            self.overview_table_model.clear()
            self._graphs.clear_overview_plots()
        self._widgets.log_duration_value.setText(f'{combat.meta['log_duration']:.1f}s')
        self._widgets.player_duration_value.setText(f'{combat.meta['player_duration']:.1f}s')
        self.populate_analysis(combat)
        self._tables.refresh_tables(
            self.damage_out_model.player_index, self.damage_in_model.player_index,
            self.heal_out_model.player_index, self.heal_in_model.player_index)

    def save_combat(self, combat_info: tuple[int, str, str, str, str] | None):
        """
        Callback for save button.

        Parameters:
        - :param combat_info: tuple of combat-identifying data (id, map, date, time, difficulty)
        """
        if combat_info is None or combat_info[0] >= len(self._parser.combats):
            desc = tr('Please analyze a log file and select a combat before attempting to export '
                      'a combat.')
            self.show_info(tr('No combat selected'), desc)
            return
        combat = self._parser.combats[combat_info[0]]
        filename = combat.map
        if combat.difficulty is not None and combat.difficulty != '':
            filename += ' ' + combat.difficulty
        combat_time = combat.start_time.strftime("%Y-%m-%d %H.%M")
        filename += f' {combat_time}.log'
        preset_path = Path(self._global_settings.log_path).parent / filename
        path = browse_path(preset_path, 'Logfile (*.log);;Any File (*.*)', save=True)
        if path is None:
            self.show_info(tr('Export cancelled'), tr('The export process was manually cancelled.'))
        elif self._parser.export_combat(combat_info[0], path):
            desc = (
                tr('Combat') + f' {combat_info[0]} ({combat.map} {combat_time}) '
                + tr('was successfully exported to') + f' "{path.name}".')
            self.show_info(tr('Export successful'), desc)
        else:
            desc = (
                tr('Exporting combat') + f' {combat_info[0]} ({combat.map} {combat_time}) '
                + tr('failed because OSCR could not write to the specified location.'))
            self.show_info(tr('Export failed'), desc)

    def export_combat_json(self, combat_info: tuple[int, str, str, str, str] | None):
        """
        Exports current combat to JSON file

        Parameters:
        - :param combat_info: tuple of combat-identifying data (id, map, date, time, difficulty)
        """
        if combat_info is None or combat_info[0] >= len(self._parser.combats):
            desc = tr('Please analyze a log file and select a combat before attempting to export '
                      'a combat.')
            self.show_info(tr('No combat selected'), desc)
            return
        combat = self._parser.combats[combat_info[0]]
        filename = combat.map
        if combat.difficulty is not None and combat.difficulty != '':
            filename += ' ' + combat.difficulty
        combat_time = combat.start_time.strftime("%Y-%m-%d %H.%M")
        filename += f' {combat_time}.json'
        preset_path = Path(self._parser.log_path) / filename
        path = browse_path(preset_path, 'JSON File (*.json);;Any File (*.*)', save=True)
        if path is None:
            self.show_info(tr('Export cancelled'), tr('The export process was manually cancelled.'))
        elif save_to_json(path, combat.get_export()):
            desc = (
                tr('Combat') + f' {combat_info[0]} ({combat.map} {combat_time}) '
                + tr('was successfully exported to') + f' "{path.name}".')
            self.show_info(tr('Export successful'), desc)
        else:
            desc = (
                tr('Exporting combat') + f' {combat_info[0]} ({combat.map} {combat_time}) '
                + tr('failed because OSCR could not write to the specified location.'))
            self.show_info(tr('Export failed'), desc)

    def trim_logfile(self, path: Path) -> bool:
        """
        Removes all combats but the most recent one from a logfile

        Parameters:
        - :param path: path of logfile to be trimmed

        :return: True if successful, False if not
        """
        combats = self._parser.isolate_combats(path, 1)
        if len(combats) < 1:
            return False
        if oscr__extract_bytes(path, path, combats[0][5], combats[0][6]):
            desc = tr('Log file') + f' "{path.name}" ' + tr('was successfully trimmed.')
            self.show_info(tr('Log file trimmed'), desc)
            return True
        else:
            desc = tr('Log file') + f' "{path.name}" ' + tr('could not be written to by OSCR.')
            self.show_info(tr('Trimming failed'), desc)
            return False

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
            self.show_info(tr('Invalid logfile'), tr('Please select an existing file to parse.'))
            return False
        combats = self._parser.isolate_combats(log_path)
        combat_list.set_items(combats)

    def init_analysis_table_fonts(self, header_font: QFont, name_font: QFont, cell_font: QFont):
        """
        Sets fonts to use for cells and header and names.

        Parameters:
        - :param header_font: font used for the header
        - :param name_font: font used for the first column
        - :param cell_font: font used for the second to last column
        """
        self.damage_out_model.init_fonts(header_font, name_font, cell_font)
        self.damage_in_model.init_fonts(header_font, name_font, cell_font)
        self.heal_out_model.init_fonts(header_font, name_font, cell_font)
        self.heal_in_model.init_fonts(header_font, name_font, cell_font)

    def current_combat_meta(self) -> dict[str] | None:
        """
        Returns metadata from current combat or `None` if no combat available

        Parameters:
        - :param combat_id: number of the combat to get meta
        """
        if self.current_combat_id >= 0:
            return self._parser.combats[self.current_combat_id].meta
        return None

    def repair_logfile(self, path: Path):
        """
        Repairs given logfile.
        """
        if path.is_file():
            res = oscr__repair_logfile(str(path), str(self._global_config.templog_folder_path))
            if res == '':
                self._dialogs.show_message(
                    tr('Repair Logfile'), tr('The Logfile has been repaired.'))
            elif res == 'PermissionError':
                error_message = ('The Logfile could not be repaired due to a permission error. '
                                 'Make sure the selected logfile can be overwritten without '
                                 'elevated permissions.')
                self._dialogs.show_message(tr('Permission Error'), tr(error_message), 'error')
        else:
            self._dialogs.show_message(
                tr('Repair Logfile'), tr('The Logfile you are trying to open does not exist.'),
                'warning')

    def isolate_combats(self, path: Path) -> list[tuple]:
        """
        Isolates combats of logfile at given path and returns them.

        Parameters:
        - :param path: path to logfile
        """
        return self._parser.isolate_combats(str(path))

    def extract_combats(self, selected_indices: list[QModelIndex], source_path: Path):
        """
        Extracts combats in `selected_indices` from current logfile and prompts the user to select a
        file to write them to.

        Parameters:
        - :param selected_indices: list of model indices refering to the selected combats
        - :param source_path: path of logfile that combats are extracted from
        """
        combat_intervals = list()
        for index in selected_indices:
            data = index.data()
            combat_intervals.append((data[5], data[6]))
        combat_intervals.sort(key=lambda element: element[0])
        target_path = browse_path(source_path.parent, 'Logfile (*.log);;Any File (*.*)', save=True)
        if target_path is not None:
            oscr__compose_logfile(
                str(source_path), str(target_path), combat_intervals,
                str(self._global_config.templog_folder_path))
            self._dialogs.show_message(tr('Split Logfile'), tr('Logfile has been saved.'))

    def copy_summary_data(self):
        """
        Callback to copy the combat summary of the active combat to the user's clipboard.
        """
        if self.current_combat_id < 0:
            return
        current_combat = self.current_combat
        duration = current_combat.duration.total_seconds()
        combat_time = f'{int(duration / 60):02}:{duration % 60:02.0f}'

        if self._global_settings.copy_format == 'Compact':
            parts = ['OSCR (DPS)', current_combat.map]
            difficulty = current_combat.difficulty
            if difficulty != 'Any' and difficulty is not None:
                parts.append(difficulty)
            parts.append(combat_time)
            players = sorted(
                current_combat.players.values(), reverse=True, key=lambda player: player.DPS)
            for player in players:
                parts.append(f'{player.handle} - {player.DPS:,.0f}')
            QApplication.clipboard().setText(' | '.join(parts))
        elif self._global_settings.copy_format == 'Verbose':
            summary = f'{{ OSCR }} {current_combat.map}'
            difficulty = current_combat.difficulty
            if difficulty is not None and difficulty != 'Any':
                summary += f' ({difficulty}) - DPS / DMG [{combat_time}]: '
            else:
                summary += f' - DPS / DMG [{combat_time}]: '
            players = sorted(
                current_combat.players.values(), reverse=True, key=lambda player: player.DPS)
            parts = list()
            for player in players:
                parts.append(
                    f'`{player.handle}` {player.DPS:,.0f} / '
                    + format_damage_number(player.total_damage))
            QApplication.clipboard().setText(summary + ' | '.join(parts))
        elif self._global_settings.copy_format == 'CSV':
            difficulty = self.current_combat.difficulty
            if difficulty is None:
                difficulty = 'Unknown'
            parts = ['OSCR', 'DPS', current_combat.map, difficulty, combat_time]
            players = sorted(
                current_combat.players.values(), reverse=True, key=lambda player: player.DPS)
            for player in players:
                parts.append(player.handle)
                parts.append(f'{player.DPS:.0f}')
            QApplication.clipboard().setText(', '.join(parts))
