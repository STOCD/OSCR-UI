"""Backend interface to the OSCR web server"""

from gzip import compress as gzip__compress, decompress as gzip__decompress
from json import JSONDecodeError, loads as json__loads
from pathlib import Path
from tempfile import NamedTemporaryFile as TempFile
from typing import Callable

from OSCR_django_client import (
    ApiClient, CombatlogApi, CombatLogUploadV2Response, Ladder, LadderApi, LadderEntriesApi,
    Variant, VariantApi)
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidgetItem

from .config import OSCRConfig
from .datamodels import LeagueTableModel, SortingProxy
from .dialogs import DialogsWrapper, UploadresultDialog
from .parserbridge import ParserBridge
from .textedit import format_datetime_str
from .theme import AppTheme
from .translation import tr
from .widgetmanager import WidgetManager

LEAGUE_TABLE_HEADER = [
        'Name', 'Handle', 'DPS', 'Total Damage', 'Deaths', 'Combat Time', 'Date', 'Max One Hit',
        'Debuff', 'Highest Damage Ability']

OSCR_SERVER_BACKEND = "https://oscr.stobuilds.com/"
# OSCR_SERVER_BACKEND = "http://127.0.0.1:8000"


class FetchThread(QThread):
    """Thread with attached callback"""

    result: Signal = Signal(object)

    def __init__(
            self, target: Callable, args: tuple = tuple(), kwargs: dict[str] = dict(),
            callback: Callable | None = None):
        super().__init__()
        self._target: Callable = target
        self._args: tuple = args
        self._kwargs: dict[str] = kwargs
        self._callback: Callable | None = callback
        self.result.connect(self.handle_result)

    @Slot(object)
    def run(self):
        """
        This function will be executed in a separate thread.
        """
        self.result.emit(self._target(*self._args, **self._kwargs))

    @Slot(object)
    def handle_result(self, thread_result: object):
        """
        Calls callback function in original thread if it's given.
        """
        if self._callback is not None:
            self._callback(thread_result)


class OSCRLeagueConnector(QObject):
    """Manages connection to League Tables"""

    ladder_data: Signal = Signal(dict)
    status_message: Signal = Signal(str, str)

    def __init__(
            self, widgets: WidgetManager, dialogs: DialogsWrapper, theme: AppTheme,
            config: OSCRConfig, parser: ParserBridge, upload_dialog: UploadresultDialog):
        super().__init__()
        self._widgets: WidgetManager = widgets
        self._dialogs: DialogsWrapper = dialogs
        self._theme: AppTheme = theme
        self._config: OSCRConfig = config
        self._parser: ParserBridge = parser
        self._upload_dialog: UploadresultDialog = upload_dialog
        self._api: ApiClient | None = None
        self._api_variant: VariantApi
        self._api_ladder: LadderApi
        self._api_ladder_entries: LadderEntriesApi
        self._api_combatlog: CombatlogApi
        self._thread: FetchThread | None = None
        self.ladder_meta: dict[str, Ladder] = dict()
        self.current_ladder_id: int | None = None
        self.entire_ladder_loaded: bool = False
        self.pages_loaded: int = 0
        self.ladder_table_model: LeagueTableModel = LeagueTableModel(LEAGUE_TABLE_HEADER)
        self.ladder_table_sort: SortingProxy = SortingProxy()
        self.ladder_table_sort.setSourceModel(self.ladder_table_model)

    def establish_league_connection(self):
        """
        Connects to the league server if not already connected.

        Parameters:
        - :param fetch_ladder: fetches available maps and updates map selector if true
        """
        if self._api is None:
            self._api = ApiClient()
            self._api.configuration.host = OSCR_SERVER_BACKEND
            self._api_variant = VariantApi(api_client=self._api)
            self._api_ladder = LadderApi(api_client=self._api)
            self._api_ladder_entries = LadderEntriesApi(api_client=self._api)
            self._api_combatlog = CombatlogApi(api_client=self._api)
            self._thread = FetchThread(target=self.fetch_and_insert_maps)
            self._thread.start()
            self.status_message.emit(tr('Fetching seasons'), '')

    def handle_fetch_error(self, error: BaseException):
        """
        Shows error message after fetching data from server failed.

        Parameters:
        - :param error: error object that was raised in trying to fetch from server
        """
        error_details = ''
        error_args = getattr(error, 'args', None)
        if error_args is not None:
            error_details = f'{error_args}\n\n'
        error_reason = getattr(error, 'reason', None)
        if error_reason is not None:
            error_details += f'{error_args}\n\n'
        error_body = getattr(error, 'body', None)
        if isinstance(error_body, str):
            try:
                error_details += json__loads(error_body) + '\n\n'
            except JSONDecodeError:
                pass
        self.status_message.emit(tr('League table error'), tr('Retrieving League data failed.'))
        self._dialogs.show_error(
            tr('League Error'), tr('Retrieving League data failed.'), error_details)

    def fetch_and_insert_maps(self):
        """
        Retrieves maps from API and inserts them into the list.
        """
        # Only populate the table once.
        if self._widgets.variant_combo.count() > 0:
            return
        variants = self.variants(ordering="-start_date")
        if variants is not None:
            for variant in variants:
                self._widgets.variant_combo.addItem(variant.name)
                if variant.name == 'Default':
                    self._widgets.variant_combo.setCurrentText('Default')
            self.status_message.emit(tr('Seasons fetched'), '')

    def upload(self, combat: tuple[str, int, int]) -> CombatLogUploadV2Response | None:
        """
        Upload a combat log located at path to the league tables

        Parameters:
        - :param combat: contains path to log file, start and end position of combat in log file
        """
        try:
            with (TempFile(dir=str(self._config.templog_folder_path)) as temp,
                    open(combat[0], 'rb') as log_file):
                log_file.seek(combat[1])
                temp.write(gzip__compress(
                    log_file.read(combat[2] - combat[1])))
                temp.flush()
                response = self._api_combatlog.combatlog_uploadv2(file=temp.name)
            return response
        except BaseException as e:
            self.handle_fetch_error(e)

    def download(self, id: int) -> Path | None:
        """
        Download a combat log, returns gzipped file bytes.

        Parameters:
        - :param id: id of the combatlog to download
        """
        try:
            result = self._api_combatlog.combatlog_download(id=id)
            if result is None:
                return
            with TempFile(mode="wb", dir=str(self._config.templog_folder_path), delete=False) as f:
                f.write(gzip__decompress(result))
            return Path(f.name)
        except BaseException as e:
            self.handle_fetch_error(e)

    def ladder_entries(self, id: int, page: int = 1) -> tuple[list, list, list] | None:
        """
        Fetch ladder entries from server and creates table data. Returns tuple containing the table
        index, row data, list of logfile ids and whether the entire ladder was loaded if
        successful. Returns `None` if ladder entries could not be retrieved.

        Parameters:
        - same as `LadderApi.ladder_list`
        """
        try:
            ladder_response = self._api_ladder_entries.ladder_entries_list(
                ladder=str(id), page=page, ordering="-data__DPS", page_size=50)
            table_index = list()
            table_data = list()
            logfile_ids = list()
            for entry in ladder_response.results:
                logfile_ids.append(entry.combatlog)
                row = entry.data
                table_index.append(entry.rank)
                table_data.append((
                    row['name'], row['handle'], row['DPS'], row['total_damage'], row['deaths'],
                    row['combat_time'], format_datetime_str(entry.var_date), row['max_one_hit'],
                    row['debuff'], row.get('build', 'Unknown')))
            return table_index, table_data, logfile_ids
        except BaseException as e:
            self.handle_fetch_error(e)

    def ladders(self, **kwargs) -> list[QListWidgetItem] | None:
        """
        Fetch ladders from server and create ladder list. Returns `None` if ladders could not be
        retrieved.

        Parameters:
        - same as `LadderApi.ladder_list`
        """
        try:
            ladders = self._api_ladder.ladder_list(**kwargs).results
            ladder_list = list()
            for ladder in ladders:
                solo = ' [Solo]' if ladder.is_solo else ''
                key = f'{ladder.name}{solo}|{ladder.difficulty}'
                text = f'{ladder.name}{solo}'
                self.ladder_meta[key] = ladder
                item = QListWidgetItem(text)
                item.difficulty = ladder.difficulty
                if ladder.difficulty != 'Any' and ladder.difficulty is not None:
                    icon = self._theme.icons[f'TFO-{ladder.difficulty.lower()}']
                    icon.addPixmap(icon.pixmap(18, 24), QIcon.Mode.Selected)
                    item.setIcon(icon)
                ladder_list.append(item)
            return ladder_list
        except BaseException as e:
            self.handle_fetch_error(e)

    def variants(self, **kwargs) -> list[Variant] | None:
        """
        Fetch variants from server. Returns `None` if variants could not be retrieved.

        Parameters:
        - same as `VariantApi.variant_list`
        """
        try:
            return self._api_variant.variant_list(**kwargs).results
        except BaseException as e:
            self.handle_fetch_error(e)

    def update_seasonal_records(self, new_season: str):
        """
        Update the default records widget

        Parameters:
        - :param new_season: Name of the season to be shown
        """
        if self._thread is not None and not self._thread.isRunning():
            self._thread = FetchThread(
                self.ladders, kwargs={'variant': new_season},
                callback=self._insert_seasonal_records)
            self._thread.start()
            self.status_message.emit(
                tr('Updating ladders'),
                tr('Retrieving ladders for season') + f' "{new_season}" ' + tr('from the server.'))

    def _insert_seasonal_records(self, ladder_list: list[QListWidgetItem] | None):
        """
        Puts fetched seasonal records into the ladder selector.

        Parameters:
        - :param ladder_list: list containing the ladder items
        """
        if ladder_list is not None:
            self._widgets.ladder_selector.clear()
            for ladder_item in ladder_list:
                self._widgets.ladder_selector.addItem(ladder_item)
            self.status_message.emit(
                tr('Ladders updated'), tr('Updated ladders to match the selected season.'))

    def apply_league_table_filter(self, filter_text: str):
        """
        Sets filter to proxy model of league table

        Parameters:
        - :param filter_text: text to filter the table for
        """
        self.ladder_table_sort.name_filter = filter_text

    def show_ladder(self, selected_map_item: QListWidgetItem):
        """
        Fetches current ladder and puts it into the table.

        Parameters:
        - :param selected_map_item: item containing name and difficulty of clicked map
        """
        if self._thread is not None and not self._thread.isRunning():
            map_key = f'{selected_map_item.text()}|{selected_map_item.difficulty}'
            if map_key not in self.ladder_meta:
                return
            selected_ladder = self.ladder_meta[map_key]
            self.current_ladder_id = selected_ladder.id
            self._thread = FetchThread(
                self.ladder_entries, args=(selected_ladder.id,), callback=self._insert_ladder_rows)
            self._thread.start()
            if selected_map_item.difficulty is None:
                map_name = selected_map_item.text()
            else:
                map_name = f'{selected_map_item.text()} - {selected_map_item.difficulty}'
            self.status_message.emit(
                tr('Retrieving ladder'), tr('Fetching ladder table for') + f' "{map_name}".')

    def _insert_ladder_rows(self, ladder_data: tuple[list, list, list] | None):
        """
        Puts fetched ladder rows into the table.
        """
        if ladder_data is not None:
            table_index, table_data, logfile_ids = ladder_data
            self.entire_ladder_loaded = False
            self.pages_loaded = 1
            self.ladder_table_model.replace_data(table_index, table_data, logfile_ids)
            self._widgets.ladder_table.resizeColumnsToContents()
            self._widgets.ladder_table.scrollToTop()
            self.status_message.emit(
                tr('Table updated'), tr('Ladder table retrieved successfully.'))

    def extend_ladder(self):
        """
        Extends the ladder table by 50 newly fetched rows.
        """
        if (self.entire_ladder_loaded or self.current_ladder_id is None
                or self._thread is None or self._thread.isRunning()):
            return
        self._thread = FetchThread(
            self.ladder_entries, args=(self.current_ladder_id, self.pages_loaded + 1),
            callback=self._extend_ladder_rows)
        self._thread.start()
        self.status_message.emit(
            tr('Extending ladder'), tr('Fetching more rows of the current ladder.'))

    def _extend_ladder_rows(self, ladder_data: tuple[list, list, list] | None):
        """
        Adds fetched ladder rows to the table.
        """
        if ladder_data is not None:
            table_index, table_data, logfile_ids = ladder_data
            self.pages_loaded += 1
            self.ladder_table_model.extend_data(table_index, table_data, logfile_ids)
            self._widgets.ladder_table.resizeColumnsToContents()
            self._widgets.ladder_table.scrollToTop()
            self.status_message.emit(
                tr('Table updated'), tr('Ladder table retrieved successfully.'))
            if len(table_data) < 50:
                self.entire_ladder_loaded = True
                self.status_message.emit(
                    tr('Table complete'),
                    tr('All entries of the current ladder are present in the table.'))

    def download_and_view_combat(self):
        """
        Download a combat log and view its contents in the overview / analysis pages.
        """
        selection = self._widgets.ladder_table.selectedIndexes()
        if len(selection) < 1 or self._thread is None or self._thread.isRunning():
            return
        original_index = self.ladder_table_sort.mapToSource(selection[0])
        log_id = self.ladder_table_model.combatlog_id_list[original_index.row()]
        self._thread = FetchThread(
            self.download, args=(log_id,),
            callback=lambda log_path: self._parser.analyze_log_file(log_path, hidden_path=True))
        self._thread.start()
        self.status_message.emit(tr('Downloading log file'), tr('Log file id:') + f' "{log_id}"')

    def upload_callback(self):
        """
        Helper function to grab the current combat and upload it to the backend.
        """
        try:
            current_combat = self._parser.current_combat
        except IndexError:
            return
        if self._thread is not None and self._thread.isRunning():
            return
        self.establish_league_connection()
        combat = (current_combat.log_file, current_combat.file_pos[0], current_combat.file_pos[1])
        self._thread = FetchThread(self.upload, args=(combat,), callback=self._handle_upload)
        self._thread.start()
        self.status_message.emit(tr('Uploading log file'), '')

    def _handle_upload(self, response: CombatLogUploadV2Response | None):
        """
        Informs the user after upload.

        Parameters:
        - :param response: contains data about upload
        """
        if response is None:
            self.status_message.emit(tr('Upload failed'), tr('Could not connect to the server.'))
        else:
            self.status_message.emit(tr('Upload performed'), '')
            self._upload_dialog.show_dialog(response)
