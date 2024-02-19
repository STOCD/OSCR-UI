"""Backend inteface to the OSCR web server"""

import tempfile

import OSCR_django_client
from OSCR.utilities import logline_to_str
from OSCR_django_client.api import CombatlogApi, LadderApi, LadderEntriesApi
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QMessageBox,
                             QPushButton, QTreeView, QVBoxLayout, QWidget)

from .style import get_style_class
from .widgetbuilder import RFIXED, SMINMIN, SMPIXEL


def create_ladder_layout(self):
    """Create the Ladder Selection Layout"""

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    self.ladder_combo = QComboBox()

    self.ladder_results_model = QStandardItemModel()

    self.ladder_results_view = QTreeView()
    self.ladder_results_view.setModel(self.ladder_results_model)

    self.ladder_results_view.setStyleSheet(
        get_style_class(self, "QTreeView", "tree_table")
    )
    self.ladder_results_view.setSizePolicy(SMINMIN)
    self.ladder_results_view.setAlternatingRowColors(True)
    self.ladder_results_view.setHorizontalScrollMode(SMPIXEL)
    self.ladder_results_view.setVerticalScrollMode(SMPIXEL)
    self.ladder_results_view.setSortingEnabled(True)
    self.ladder_results_view.setEditTriggers(
        QAbstractItemView.EditTrigger.NoEditTriggers
    )
    # self.ladder_results_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    # self.ladder_results_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    # self.ladder_results_view.header().setStyleSheet(get_style_class(self, 'QHeaderView', 'tree_self.ladder_results_view_header'))
    # self.ladder_results_view.header().setSectionsMovable(False)
    self.ladder_results_view.header().setSectionsClickable(True)
    self.ladder_results_view.header().setStretchLastSection(False)
    self.ladder_results_view.header().setSortIndicatorShown(False)

    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_layout.setContentsMargins(0, 0, 0, 0)
    results_layout.addWidget(self.ladder_results_view)

    combat_button = QPushButton("View Combat Log")
    combat_button.clicked.connect(self.download_and_view_combat)

    self.ladders = {}
    self.ladder_combo.clear()
    self.ladder_combo.addItem("Select a League")
    self.ladder_combo.currentIndexChanged.connect(
        self.update_ladder_index,
    )

    res = self.backend.ladders()
    if res is not None:
        for ladder in res.results:
            key = f"{ladder.metric} - {ladder.name} ({ladder.difficulty})"
            self.ladders[key] = ladder
            self.ladder_combo.addItem(key)

    layout.addWidget(self.ladder_combo)
    layout.addWidget(results_widget)
    layout.addWidget(combat_button)

    return layout


def update_ladder_index(self, index):
    """Open Combat Log Dialog Box"""

    self.ladder_results_model.clear()
    self.ladder_results_model.setHorizontalHeaderLabels(
        [
            "Rank",
            "Date",
            "Name",
            "Handle",
            "DPS",
            "Damage",
            "Deaths",
            "Combat Time",
        ]
    )

    if index >= 1:
        ladder = self.ladders[self.ladder_combo.currentText()]
        res = self.backend.ladder_entries(ladder.id)
        if res is not None:
            for idx, entry in enumerate(res.results):
                row_rank = QStandardItem()
                row_rank.setText(f"{int(idx + 1)}")
                row_rank.setEditable(False)

                row_date = QStandardItem()
                row_date.setText(entry.var_date)
                row_date.setEditable(False)

                row_name = QStandardItem(entry.data["name"])
                row_name.setEditable(False)

                row_handle = QStandardItem(entry.data["handle"])
                row_handle.setEditable(False)

                row_damage = QStandardItem()
                row_damage.setText(f"{int(entry.data['total_damage']):,}")
                row_damage.setEditable(False)

                row_dps = QStandardItem()
                row_dps.setText(f"{int(entry.data['DPS']):,}")
                row_dps.setEditable(False)

                row_deaths = QStandardItem()
                row_deaths.setText(f"{int(entry.data['deaths']):,}")
                row_deaths.setEditable(False)

                row_time = QStandardItem()
                row_time.setText(f"{int(entry.data['combat_time']):,}")
                row_time.setEditable(False)

                self.ladder_results_model.appendRow(
                    [
                        row_rank,
                        row_date,
                        row_name,
                        row_handle,
                        row_dps,
                        row_damage,
                        row_deaths,
                        row_time,
                    ]
                )

        # HACK
        self.ladder_results_view.resizeColumnToContents(0)
        self.ladder_results_view.resizeColumnToContents(1)
        self.ladder_results_view.resizeColumnToContents(2)
        self.ladder_results_view.resizeColumnToContents(3)
        self.ladder_results_view.resizeColumnToContents(4)
        self.ladder_results_view.resizeColumnToContents(5)
        self.ladder_results_view.resizeColumnToContents(6)
        self.ladder_results_view.resizeColumnToContents(7)


def download_and_view_combat(self, idx):
    """
    Download a combat log and view its contents in the overview / analysis pages.
    """


def upload_callback(self):
    """
    Helper function to grab the current combat and upload it to the backend.
    """

    with tempfile.NamedTemporaryFile() as file:
        for line in self.parser1.active_combat.log_data:
            file.write(logline_to_str(line).encode())
            file.flush()
        self.backend.upload(file.name)


class OSCRClient:
    def __init__(self, address=None):
        """Initialize an instance of the OSCR backlend client"""

        # TODO: This is a test domain and not for production.
        if not address:
            self.address = "https://kraust-oscr.koyeb.app"
            # self.address = "http://127.0.0.1:8000"

        self.api_client = OSCR_django_client.api_client.ApiClient()
        self.api_client.configuration.host = self.address
        self.api_combatlog = CombatlogApi(api_client=self.api_client)
        self.api_ladder = LadderApi(api_client=self.api_client)
        self.api_ladder_entries = LadderEntriesApi(api_client=self.api_client)

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
