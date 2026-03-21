"""Backend interface to the OSCR web server"""

import gzip
from gzip import compress as gzip__compress, decompress as gzip__decompress
import json
from json import JSONDecodeError, loads as json__loads
import os
from pathlib import Path
from tempfile import NamedTemporaryFile as TempFile

from OSCR_django_client import (
    ApiClient, CombatlogApi, CombatLogUploadV2Response, Ladder, LadderApi, LadderEntriesApi,
    LadderEntriesList200Response, Variant, VariantApi)
from OSCR_django_client.exceptions import ServiceException
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from .config import OSCRConfig
from .datafunctions import CustomThread
from .datamodels import LeagueTableModel, SortingProxy
from .dialogs import DialogsWrapper, UploadresultDialog
from .parserbridge import ParserBridge
from .theme import AppTheme
from .subwindows import uploadresult_dialog
from .textedit import format_datetime_str
from .translation import tr
from .widgetmanager import WidgetManager

LEAGUE_TABLE_HEADER = [
        'Name', 'Handle', 'DPS', 'Total Damage', 'Deaths', 'Combat Time', 'Date', 'Max One Hit',
        'Debuff', 'Highest Damage Ability']

OSCR_SERVER_BACKEND = "https://oscr.stobuilds.com/"
# OSCR_SERVER_BACKEND = "http://127.0.0.1:8000"


class OSCRLeagueConnector():
    """Manages connection to League Tables"""
    def __init__(
            self, widgets: WidgetManager, dialogs: DialogsWrapper, theme: AppTheme,
            config: OSCRConfig, parser: ParserBridge, upload_dialog: UploadresultDialog):
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
        self._thread: CustomThread | None = None
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
            self._thread = CustomThread(None, self.fetch_and_insert_maps)
            self._thread.start()

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

    def upload(self, file_path: str) -> CombatLogUploadV2Response | None:
        """
        Upload a combat log located at path to the league tables

        Parameters:
        - :param file_path: path to file that will be uploaded
        """
        try:
            return self._api_combatlog.combatlog_uploadv2(file=file_path)
        except BaseException as e:
            self.handle_fetch_error(e)

    def download(self, id: int) -> bytearray | None:
        """
        Download a combat log, returns gzipped file bytes.

        Parameters:
        - :param id: id of the combatlog to download
        """
        try:
            return self._api_combatlog.combatlog_download(id=id)
        except BaseException as e:
            self.handle_fetch_error(e)

    def ladder_entries(self, id: int, page: int = 1) -> LadderEntriesList200Response | None:
        """
        Fetch ladder entries from server. Returns `None` if ladder entries could not be retrieved.

        Parameters:
        - same as `LadderApi.ladder_list`
        """
        try:
            return self._api_ladder_entries.ladder_entries_list(
                ladder=str(id), page=page, ordering="-data__DPS", page_size=50)
        except BaseException as e:
            self.handle_fetch_error(e)

    def ladders(self, **kwargs) -> list[Ladder] | None:
        """
        Fetch ladders from server. Returns `None` if ladders could not be retrieved.

        Parameters:
        - same as `LadderApi.ladder_list`
        """
        try:
            return self._api_ladder.ladder_list(**kwargs).results
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
        ladders = self.ladders(variant=new_season)
        if ladders is not None:
            self._widgets.ladder_selector.clear()
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
                self._widgets.ladder_selector.addItem(item)

    def apply_league_table_filter(self, filter_text: str):
        """
        Sets filter to proxy model of league table

        Parameters:
        - :param filter_text: text to filter the table for
        """
        self.ladder_table_sort.name_filter = filter_text

    def slot_ladder(self, selected_map_item: QListWidgetItem):
        """
        Fetches current ladder and puts it into the table.

        Parameters:
        - :param selected_map_item: item containing name and difficulty of clicked map
        """
        map_key = f'{selected_map_item.text()}|{selected_map_item.difficulty}'
        if map_key not in self.ladder_meta:
            return
        selected_ladder = self.ladder_meta[map_key]
        self.current_ladder_id = selected_ladder.id
        ladder_response = self.ladder_entries(selected_ladder.id)
        if ladder_response is None:
            return
        if ladder_response.count > 50:
            self.entire_ladder_loaded = False
        else:
            self.entire_ladder_loaded = True
        self.pages_loaded = 1
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
        self.ladder_table_model.replace_data(table_index, table_data, logfile_ids)
        self._widgets.ladder_table.resizeColumnsToContents()
        self._widgets.ladder_table.scrollToTop()

    def extend_ladder(self):
        """
        Extends the ladder table by 50 newly fetched rows.
        """
        if self.entire_ladder_loaded or self.current_ladder_id is None:
            return
        ladder_response = self.ladder_entries(self.current_ladder_id, self.pages_loaded + 1)
        if ladder_response is None:
            return
        if len(ladder_response.results) < 50:
            self.entire_ladder_loaded = True
        self.pages_loaded += 1
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
        self.ladder_table_model.extend_data(table_index, table_data, logfile_ids)
        self._widgets.ladder_table.resizeColumnsToContents()

    def download_and_view_combat(self):
        """
        Download a combat log and view its contents in the overview / analysis pages.
        """
        selection = self._widgets.ladder_table.selectedIndexes()
        if len(selection) < 1:
            return
        original_index = self.ladder_table_sort.mapToSource(selection[0])
        log_id = self.ladder_table_model.combatlog_id_list[original_index.row()]
        result = self.download(log_id)
        if result is None:
            return
        result = gzip__decompress(result)

        with TempFile(mode="wb", dir=str(self._config.templog_folder_path), delete=False) as file:
            file.write(result)
        self._parser.analyze_log_file(Path(file.name), hidden_path=True)

    def upload_callback(self):
        """
        Helper function to grab the current combat and upload it to the backend.
        """
        try:
            current_combat = self._parser.current_combat
        except IndexError:
            return
        self.establish_league_connection()

        with (TempFile(delete=False, dir=str(self._config.templog_folder_path)) as temp,
              open(current_combat.log_file, 'rb') as log_file):
            log_file.seek(current_combat.file_pos[0])
            temp.write(gzip__compress(
                log_file.read(current_combat.file_pos[1] - current_combat.file_pos[0])))
            temp.flush()
        res = self.upload(temp.name)
        if res is not None:
            self._upload_dialog.show_dialog(res)
        os.remove(temp.name)


class OSCRClient:
    def __init__(self):
        """Initialize an instance of the OSCR backlend client"""

        self.address = OSCR_SERVER_BACKEND
        self.api_client = ApiClient()
        self.api_client.configuration.host = self.address
        self.api_combatlog = CombatlogApi(api_client=self.api_client)
        self.api_ladder = LadderApi(api_client=self.api_client)
        self.api_ladder_entries = LadderEntriesApi(api_client=self.api_client)
        self.api_variant = VariantApi(api_client=self.api_client)
        self.ladder_dict: dict = dict()
        self.ladder_dict_season: dict = dict()
        self.current_ladder_id = None
        self.pages_loaded: int = -1
        self.entire_ladder_loaded: bool = True

    def upload(self, filename):
        """Upload a combat log located at path for analysis"""

        try:
            return self.api_combatlog.combatlog_uploadv2(file=filename)
        except ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(
                    data.get("detail", tr("Failed to parse error from server"))
                )
            except Exception:
                reply.setText(tr("Failed to parse error from server"))
            reply.exec()

    def download(self, id):
        """Download a combat log"""
        try:
            return self.api_combatlog.combatlog_download(id=id)
        except ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(
                    data.get("detail", tr("Failed to parse error from server"))
                )
            except Exception:
                reply.setText(tr("Failed to parse error from server"))
            reply.exec()

        return None

    def ladders(self, **kwargs):
        """Fetch the list of ladders"""
        try:
            return self.api_ladder.ladder_list(**kwargs)
        except ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(
                    data.get("detail", tr("Failed to parse error from server"))
                )
            except Exception:
                reply.setText(tr("Failed to parse error from server"))
            reply.exec()

        return None

    def ladder_entries(self, id, page=1):
        """Fetch the nth page of ladder entries"""
        try:
            return self.api_ladder_entries.ladder_entries_list(
                ladder=str(id),
                page=page,
                ordering="-data__DPS",
                page_size=50,
            )
        except ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(
                    data.get("detail", tr("Failed to parse error from server"))
                )
            except Exception:
                reply.setText(tr("Failed to parse error from server"))
            reply.exec()

        return None

    def variants(self, **kwargs):
        """Return a list of Variants"""

        try:
            return self.api_variant.variant_list(**kwargs)
        except ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(
                    data.get("detail", tr("Failed to parse error from server"))
                )
            except Exception:
                reply.setText(tr("Failed to parse error from server"))
            reply.exec()

        return None
