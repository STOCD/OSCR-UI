from PySide6.QtWidgets import (
    QComboBox, QFrame, QLabel, QListWidget, QPushButton, QSplitter, QTableView, QTabWidget,
    QTreeView)

from .widgets import AnalysisPlot, FlipButton
from .config import OSCRSettings


class WidgetManager():
    """
    Class to store and manage widgets.
    """
    def __init__(self, global_settings: OSCRSettings):
        self.main_menu_buttons: list[QPushButton] = list()
        self.main_tabber: QTabWidget
        self.main_tab_frames: list[QFrame] = list()
        self.sidebar_tabber: QTabWidget
        self.sidebar_tab_frames: list[QFrame] = list()
        self.map_tabber: QTabWidget
        self.map_tab_frames: list[QFrame] = list()
        self.map_menu_buttons: list[QPushButton] = list()

        self.log_duration_value: QLabel
        self.player_duration_value: QLabel

        self.overview_menu_buttons: list[QPushButton] = list()
        self.overview_tabber: QTabWidget
        self.overview_tab_frames: list[QFrame] = list()
        self.overview_table_frame: QFrame
        self.overview_table_button: FlipButton
        self.overview_splitter: QSplitter

        self.analysis_splitter: QSplitter
        self.analysis_menu_buttons: list[QPushButton] = list()
        self.analysis_copy_combobox: QComboBox
        self.analysis_graph_tabber: QTabWidget
        self.analysis_tree_tabber: QTabWidget
        self.analysis_graph_frames: list[QFrame] = list()
        self.analysis_tree_frames: list[QFrame] = list()
        self.analysis_table_dout: QTreeView
        self.analysis_table_dtaken: QTreeView
        self.analysis_table_hout: QTreeView
        self.analysis_table_hin: QTreeView
        self.analysis_plot_dout: AnalysisPlot
        self.analysis_plot_dtaken: AnalysisPlot
        self.analysis_plot_hout: AnalysisPlot
        self.analysis_plot_hin: AnalysisPlot
        self.analysis_graph_button: FlipButton

        self.ladder_selector: QListWidget
        self.favorite_ladder_selector: QListWidget
        self.variant_combo: QComboBox
        self.ladder_table: QTableView

        self.live_parser_table: QTableView
        self.live_parser_button: QPushButton
        self.live_parser_curves: list
        self.live_parser_splitter: QSplitter
        self.live_parser_duration_label: QLabel

        self._global_settings: OSCRSettings = global_settings

    @property
    def analysis_table(self):
        return (self.analysis_table_dout, self.analysis_table_dtaken, self.analysis_table_hout,
                self.analysis_table_hin)

    def switch_analysis_tab(self, tab_index: int):
        """
        Callback for tab switch buttons; switches tab and sets active button.

        Parameters:
        - :param tab_index: index of the tab to switch to
        """
        self.analysis_graph_tabber.setCurrentIndex(tab_index)
        self.analysis_tree_tabber.setCurrentIndex(tab_index)
        for index, button in enumerate(self.analysis_menu_buttons):
            if index == tab_index:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def switch_overview_tab(self, tab_index: int):
        """
        Callback for tab switch buttons; switches tab and sets active button.

        Parameters:
        - :param tab_index: index of the tab to switch to
        """
        self.overview_tabber.setCurrentIndex(tab_index)
        for index, button in enumerate(self.overview_menu_buttons):
            if index == tab_index:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def switch_main_tab(self, tab_index: int):
        """
        Callback for main tab switch buttons. Switches main and sidebar tabs.

        Parameters:
        - :param tab_index: index of the tab to switch to
        """
        SIDEBAR_TAB_CONVERSION = (0, 0, 1, 2)
        self.main_tabber.setCurrentIndex(tab_index)
        self.sidebar_tabber.setCurrentIndex(SIDEBAR_TAB_CONVERSION[tab_index])
        if tab_index == 0:
            self.overview_table_button.show()
        else:
            self.overview_table_button.hide()
        if tab_index == 1:
            self.analysis_graph_button.show()
        else:
            self.analysis_graph_button.hide()

    def expand_overview_table(self):
        """
        Shows the overview table
        """
        self.overview_table_frame.show()

    def collapse_overview_table(self):
        """
        Hides the overview table
        """
        self.overview_table_frame.hide()

    def expand_analysis_graph(self):
        """
        Shows the analysis graph
        """
        self.analysis_graph_tabber.show()
        self._global_settings.analysis_graph = True

    def collapse_analysis_graph(self):
        """
        Hides the analysis graph
        """
        self.analysis_graph_tabber.hide()
        self._global_settings.analysis_graph = False
