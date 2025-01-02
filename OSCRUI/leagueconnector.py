"""Backend interface to the OSCR web server"""

import gzip
import json
import os
import tempfile

from OSCR_django_client.api import (
        CombatlogApi, LadderApi, LadderEntriesApi, VariantApi)
from OSCR_django_client.api_client import ApiClient
from OSCR_django_client.exceptions import ServiceException
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from .callbacks import switch_main_tab, switch_overview_tab
from .datafunctions import CustomThread, analyze_log_callback
from .datamodels import LeagueTableModel, SortingProxy
from .dialogs import show_message
from .style import theme_font
from .subwindows import uploadresult_dialog
from .textedit import format_datetime_str
from .translation import tr

LEAGUE_TABLE_HEADER = (
        'Name', 'Handle', 'DPS', 'Total Damage', 'Deaths', 'Combat Time', 'Date', 'Max One Hit',
        'Debuff', 'Highest Damage Ability')

OSCR_SERVER_BACKEND = "https://oscr.stobuilds.com/"
# OSCR_SERVER_BACKEND = "http://127.0.0.1:8000"


def establish_league_connection(self):
    """
    Connects to the league server if not already connected.

    Parameters:
    - :param fetch_ladder: fetches available maps and updates map selector if true
    """
    if self.league_api is None:
        self.league_api = OSCRClient()
        map_fetch_thread = CustomThread(
            self.window, lambda: fetch_and_insert_maps(self)
        )
        map_fetch_thread.start()


def fetch_and_insert_maps(self):
    """
    Retrieves maps from API and inserts them into the list.
    """
    # Only populate the table once.
    if self.widgets.variant_combo.count() > 0:
        return

    variants = self.league_api.variants(ordering="-start_date")
    for variant in variants.results:
        self.widgets.variant_combo.addItem(variant.name)
        if variant.name == 'Default':
            self.widgets.variant_combo.setCurrentText('Default')


def update_seasonal_records(self, new_season: str):
    """
    Update the default records widget

    Parameters:
    - :param new_season: Name of the season to be shown
    """
    ladders = self.league_api.ladders(variant=new_season)
    if ladders is not None:
        self.widgets.ladder_selector.clear()
        for ladder in ladders.results:
            solo = "[Solo]" if ladder.is_solo else ""
            key = f"{ladder.name} {solo}|{ladder.difficulty}"
            text = f"{ladder.name} {solo}"
            self.league_api.ladder_dict[key] = ladder
            item = QListWidgetItem(text)
            item.difficulty = ladder.difficulty
            if ladder.difficulty != 'Any' and ladder.difficulty is not None:
                icon = self.icons[f'TFO-{ladder.difficulty.lower()}']
                icon.addPixmap(icon.pixmap(18, 24), QIcon.Mode.Selected)
                item.setIcon(icon)
            self.widgets.ladder_selector.addItem(item)


def apply_league_table_filter(self, filter_text: str):
    """
    Sets filter to proxy model of league table

    Parameters:
    - :param filter_text: text to filter the table for
    """
    try:
        self.widgets.ladder_table.model().name_filter = filter_text
    except AttributeError:
        pass


def slot_ladder(self, selected_map_item: QListWidgetItem):
    """
    Fetches current ladder and puts it into the table.

    Parameters:
    - :param selected_map_item: item containing name and difficulty of clicked map
    """
    map_key = f'{selected_map_item.text()}|{selected_map_item.difficulty}'
    if map_key not in self.league_api.ladder_dict:
        return

    selected_ladder = self.league_api.ladder_dict[map_key]
    self.league_api.current_ladder_id = selected_ladder.id
    ladder_data = self.league_api.ladder_entries(selected_ladder.id)
    if ladder_data.count > 50:
        self.league_api.entire_ladder_loaded = False
    else:
        self.league_api.entire_ladder_loaded = True
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
        tr(LEAGUE_TABLE_HEADER),
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
    table.scrollToTop()


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
        self.widgets.ladder_table.model().sourceModel().extend_data(
            table_index, table_data, logfile_ids
        )


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
        mode="wb", dir=self.config['templog_folder_path'], delete=False
    ) as file:
        file.write(result)
    analyze_log_callback(
        self, path=file.name, hidden_path=True
    )
    switch_overview_tab(self, self.settings.value('first_overview_tab', type=int))
    switch_main_tab(self, 1)


def upload_callback(self):
    """
    Helper function to grab the current combat and upload it to the backend.
    """
    try:
        current_combat = self.parser.combats[self.current_combats.currentIndex().data()[0]]
    except IndexError:
        show_message(self, tr("Logfile Upload"), tr("No data to upload."), 'info')
        return

    establish_league_connection(self)

    with tempfile.NamedTemporaryFile(delete=False, dir=self.config['templog_folder_path']) as temp:
        with open(current_combat.log_file, 'rb') as log_file:
            log_file.seek(current_combat.file_pos[0])
            data = gzip.compress(
                    log_file.read(current_combat.file_pos[1] - current_combat.file_pos[0]))
            temp.write(data)
            temp.flush()
    res = self.league_api.upload(temp.name)
    if res:
        uploadresult_dialog(self, res)
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
