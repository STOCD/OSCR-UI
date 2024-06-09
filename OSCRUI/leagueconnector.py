"""Backend inteface to the OSCR web server"""

import gzip
import os
import tempfile
import json

import OSCR_django_client
from OSCR.utilities import logline_to_str
from OSCR_django_client.api import CombatlogApi, LadderApi, LadderEntriesApi
from PySide6.QtWidgets import QMessageBox

from .datafunctions import CustomThread, analyze_log_callback
from .datamodels import LeagueTableModel, SortingProxy
from .style import theme_font
from .subwindows import show_warning, uploadresult_dialog
from .textedit import format_datetime_str

LADDER_HEADER = (
    "Name",
    "Handle",
    "DPS",
    "Total Damage",
    "Deaths",
    "Combat Time",
    "Date",
    "Max One Hit",
    "Debuff",
    "Build",
)


def establish_league_connection(self):
    """
    Connects to the league server if not already connected.

    Parameters:
    - :param fetch_ladder: fetches available maps and updates map selector if true
    """
    if self.league_api is None:
        self.league_api = OSCRClient()
        map_fetch_thread = CustomThread(self.window, lambda: fetch_and_insert_maps(self))
        map_fetch_thread.start()


def fetch_and_insert_maps(self):
    """
    Retrieves maps from API and inserts them into the list.
    """
    ladders = self.league_api.ladders()
    if ladders is not None:
        self.widgets.ladder_selector.clear()
        for ladder in ladders.results:
            solo = "[Solo]" if ladder.is_solo else ""
            variant = f"[{ladder.variant_name}] " if ladder.variant_name != "Default" else ""
            key = f"{variant}{ladder.name} ({ladder.difficulty}) {solo}"
            self.league_api.ladder_dict[key] = ladder
            self.widgets.ladder_selector.addItem(key)


def apply_league_table_filter(self, filter_text: str):
    """
    Sets filter to proxy model of league table
    """
    try:
        self.widgets.ladder_table.model().name_filter = filter_text
    except AttributeError:
        pass


def slot_ladder(self, selected_map):
    """
    Fetches current ladder and puts it into the table.
    """

    if selected_map not in self.league_api.ladder_dict:
        return
    if self.widgets.map_tabber.currentIndex() == 0:
        self.widgets.favorite_ladder_selector.selectionModel().clear()
    else:
        self.widgets.ladder_selector.selectionModel().clear()

    selected_ladder = self.league_api.ladder_dict[selected_map]
    self.league_api.current_ladder_id = selected_ladder.id
    ladder_data = self.league_api.ladder_entries(selected_ladder.id)
    if len(ladder_data.results) >= 50:
        self.league_api.entire_ladder_loaded = False
    self.league_api.pages_loaded = 1
    table_index = list()
    table_data = list()
    logfile_ids = list()

    for entry in ladder_data.results:
        logfile_ids.append(entry.combatlog)
        row = entry.data
        table_index.append(entry.rank)
        table_data.append(
            (
                row["name"],
                row["handle"],
                row["DPS"],
                row["total_damage"],
                row["deaths"],
                row["combat_time"],
                format_datetime_str(entry.var_date),
                row["max_one_hit"],
                row["debuff"],
                row.get("build", "Unknown"),
            )
        )

    model = LeagueTableModel(
        table_data,
        LADDER_HEADER,
        table_index,
        theme_font(self, "table_header"),
        theme_font(self, "table"),
        combatlog_id_list=logfile_ids,
    )
    sorting_proxy = SortingProxy()
    sorting_proxy.setSourceModel(model)
    table = self.widgets.ladder_table
    table.setModel(sorting_proxy)
    table.resizeColumnsToContents()
    # table_header = table.horizontalHeader()
    # for col in range(len(model._header)):
    #     table_header.resizeSection(col, table_header.sectionSize(col) + 5)


def extend_ladder(self):
    """
    Extends the ladder table by 50 newly fetched rows.
    """
    if self.league_api.entire_ladder_loaded:
        return
    if self.league_api.current_ladder_id is None:
        return

    ladder_data = self.league_api.ladder_entries(
        self.league_api.current_ladder_id, self.league_api.pages_loaded + 1
    )
    if ladder_data is not None:
        if len(ladder_data.results) < 50:
            self.league_api.entire_ladder_loaded = True
        self.league_api.pages_loaded += 1
        table_index = list()
        table_data = list()
        logfile_ids = list()
        for entry in ladder_data.results:
            logfile_ids.append(entry.combatlog)
            row = entry.data
            table_index.append(entry.rank)
            table_data.append(
                (
                    row["name"],
                    row["handle"],
                    row["DPS"],
                    row["total_damage"],
                    row["deaths"],
                    row["combat_time"],
                    format_datetime_str(entry.var_date),
                    row["max_one_hit"],
                    row["debuff"],
                    row.get("build", "Unknown"),
                )
            )
        self.widgets.ladder_table.model().sourceModel().extend_data(table_index, table_data, logfile_ids)


def download_and_view_combat(self):
    """
    Download a combat log and view its contents in the overview / analysis pages.
    """
    table = self.widgets.ladder_table
    table_model = table.model().sourceModel()
    selection = table.selectedIndexes()
    original_index = table.model().mapToSource(selection[0])
    row = original_index.row()
    log_id = table_model._combatlog_id_list[row]
    result = self.league_api.download(log_id)
    result = gzip.decompress(result)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False
    ) as file:
        file.write(result.decode())
    analyze_log_callback(self, path=file.name, parser_num=1, hidden_path=True)
    self.switch_overview_tab(0)
    self.switch_main_tab(0)


def upload_callback(self):
    """
    Helper function to grab the current combat and upload it to the backend.
    """
    if self.parser1.active_combat is None or self.parser1.active_combat.log_data is None:
        show_warning(self, "OSCR - Logfile Upload", "No data to upload.")
        return

    establish_league_connection(self)

    with tempfile.NamedTemporaryFile(delete=False) as file:
        data = gzip.compress(
            "".join([logline_to_str(line) for line in self.parser1.active_combat.log_data]).encode()
        )
        file.write(data)
        file.flush()
    res = self.league_api.upload(file.name)
    if res:
        uploadresult_dialog(self, res)
    os.remove(file.name)


class OSCRClient:
    def __init__(self, address=None):
        """Initialize an instance of the OSCR backlend client"""

        # TODO: This is a test domain and not for production.
        if not address:
            self.address = "https://oscr.stobuilds.com"

        self.api_client = OSCR_django_client.api_client.ApiClient()
        self.api_client.configuration.host = self.address
        self.api_combatlog = CombatlogApi(api_client=self.api_client)
        self.api_ladder = LadderApi(api_client=self.api_client)
        self.api_ladder_entries = LadderEntriesApi(api_client=self.api_client)
        self.ladder_dict: dict = dict()
        self.current_ladder_id = None
        self.pages_loaded: int = -1
        self.entire_ladder_loaded: bool = True

    def upload(self, filename):
        """Upload a combat log located at path for analysis"""

        try:
            return self.api_combatlog.combatlog_upload(file=filename)
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(data.get("detail", "Failed to parse error from server"))
            except Exception as e:
                reply.setText("Failed to parse error from server")
            reply.exec()

    def download(self, id):
        """Download a combat log"""
        try:
            return self.api_combatlog.combatlog_download(id=id)
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(data.get("detail", "Failed to parse error from server"))
            except Exception as e:
                reply.setText("Failed to parse error from server")
            reply.exec()

        return None

    def ladders(self):
        """Fetch the list of ladders"""
        try:
            return self.api_ladder.ladder_list()
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(data.get("detail", "Failed to parse error from server"))
            except Exception as e:
                reply.setText("Failed to parse error from server")
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
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            try:
                data = json.loads(e.body)
                reply.setText(data.get("detail", "Failed to parse error from server"))
            except Exception as e:
                reply.setText("Failed to parse error from server")
            reply.exec()

        return None
