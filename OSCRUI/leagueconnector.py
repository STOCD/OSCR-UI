"""Backend inteface to the OSCR web server"""

import gzip
import tempfile
import os

import OSCR_django_client
from OSCR.utilities import logline_to_str
from OSCR_django_client.api import CombatlogApi, LadderApi, LadderEntriesApi
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QMessageBox,
                             QPushButton, QTreeView, QVBoxLayout, QWidget)

from .datamodels import LeagueTableModel, SortingProxy
from .textedit import format_datetime_str
from .style import theme_font

LADDER_HEADER = ('Name', 'Handle', 'DPS', 'Total Damage', 'Deaths', 'Combat Time', 'Date', 'Max One Hit',
        'Debuff')

def establish_league_connection(self, fetch_maps: bool = False):
    """
    Connects to the league server if not already connected.

    Parameters:
    - :param fetch_ladder: fetches available maps and updates map selector if true
    """
    if self.league_api is None:
        self.league_api = OSCRClient()
    if fetch_maps and isinstance(self.league_api, OSCRClient):
        ladders = self.league_api.ladders()
        if ladders is not None:
            for ladder in ladders.results:
                key = f"{ladder.metric} - {ladder.name} ({ladder.difficulty})"
                self.league_api.ladder_dict[key] = ladder
                self.widgets.ladder_map.addItem(key)

def update_ladder_index(self, index):
    """Open Combat Log Dialog Box"""

    selected_map = self.widgets.ladder_map.currentText()
    if not selected_map in self.league_api.ladder_dict:
        return
    
    selected_ladder = self.league_api.ladder_dict[selected_map]
    ladder_data = self.league_api.ladder_entries(selected_ladder.id)
    table_index = list()
    table_data = list()

    for rank, entry in enumerate(ladder_data.results, 1):
        table_index.append(rank)
        row = entry.data
        table_data.append((row['name'], row['handle'], row['DPS'], row['total_damage'], row['deaths'], 
                row['combat_time'], format_datetime_str(entry.var_date), row['max_one_hit'], row['debuff']))
        
    model = LeagueTableModel(table_data, LADDER_HEADER, table_index, theme_font(self, 'table_header'),
            theme_font(self, 'table'))
    sorting_proxy = SortingProxy()
    sorting_proxy.setSourceModel(model)
    table = self.widgets.ladder_table
    table.setModel(sorting_proxy)
    table.resizeColumnsToContents()
    table_header = table.horizontalHeader()
    for col in range(len(model._header)):
        table_header.resizeSection(col, table_header.sectionSize(col) + 5)


def download_and_view_combat(self, idx):
    """
    Download a combat log and view its contents in the overview / analysis pages.
    """


def upload_callback(self):
    """
    Helper function to grab the current combat and upload it to the backend.
    """

    establish_league_connection(self)

    if (
        self.parser1.active_combat is None
        or self.parser1.active_combat.log_data is None
    ):
        raise Exception("No data to upload")

    with tempfile.NamedTemporaryFile(dir=self.app_dir, delete=False) as file:
        data = gzip.compress(
            "".join(
                [logline_to_str(line) for line in self.parser1.active_combat.log_data]
            ).encode()
        )
        file.write(data)
        file.flush()
    self.league_api.upload(file.name)
    os.remove(file.name)


class OSCRClient:
    def __init__(self, address=None):
        """Initialize an instance of the OSCR backlend client"""

        # TODO: This is a test domain and not for production.
        if not address:
            self.address = "https://oscr-server.vercel.app"
            # self.address = "http://127.0.0.1:8000"

        self.api_client = OSCR_django_client.api_client.ApiClient()
        self.api_client.configuration.host = self.address
        self.api_combatlog = CombatlogApi(api_client=self.api_client)
        self.api_ladder = LadderApi(api_client=self.api_client)
        self.api_ladder_entries = LadderEntriesApi(api_client=self.api_client)
        self.ladder_dict: dict = dict()

    def upload(self, filename):
        """Upload a combat log located at path for analysis"""

        reply = QMessageBox()
        reply.setWindowTitle("Open Source Combatlog Reader")

        try:
            res = self.api_combatlog.combatlog_upload(file=filename)
            lines = []
            for entry in res:
                lines.append(entry.detail)
            reply.setText("\n".join(lines))
        except OSCR_django_client.exceptions.ServiceException as e:
            reply.setText(str(e))

        reply.exec()

    def download(self, id):
        """Download a combat log"""
        try:
            return self.api_combatlog.combatlog_download(id=id)
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            reply.setText(str(e))
            reply.exec()

        return None

    def ladders(self):
        """Fetch the list of ladders"""
        try:
            return self.api_ladder.ladder_list()
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            reply.setText(str(e))
            reply.exec()

        return None

    def ladder_entries(self, id, page=1):
        """Fetch the nth page of ladder entries"""
        try:
            return self.api_ladder_entries.ladder_entries_list(
                ladder=str(id),
                page=page,
                ordering="-data__DPS",
                page_size=200,
            )
        except OSCR_django_client.exceptions.ServiceException as e:
            reply = QMessageBox()
            reply.setWindowTitle("Open Source Combatlog Reader")
            reply.setText(str(e))
            reply.exec()

        return None
