import os
from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QLayout, QLineEdit, QFrame, QHeaderView, QScrollArea, QSplitter,
    QTabWidget, QTableView, QTreeView, QVBoxLayout, QHBoxLayout, QGridLayout)
from PySide6.QtCore import QDir, QSize, QTimer, QThread
from PySide6.QtGui import (
    QCloseEvent, QFontDatabase, QIntValidator, QKeySequence, QResizeEvent, QShortcut)

from OSCR import LIVE_TABLE_HEADER, TABLE_HEADER, TREE_HEADER, HEAL_TREE_HEADER
from .analysisgraphs import AnalysisGraphs
from .analysistables import AnalysisTables
from .config import OSCRConfig, OSCRSettings
from .datamodels import SortingProxy, TreeModel, TreeSelectionModel
from .dialogs import DetectionInfoDialog, DialogsWrapper, UploadresultDialog
from .iofunctions import get_asset_path, load_icon_series, load_icon
from .liveparser import LiveParserWindow
from .leagueconnector import OSCRLeagueConnector
from .parserbridge import ParserBridge
from .sidebar import OSCRLeftSidebar
from .textedit import format_path
from .theme import AppTheme
from .translation import init_translation, tr
from .widgetbuilder import (
    ABOTTOM, ACENTER, AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER, OVERTICAL, SMAXMAX, SMAXMIN,
    SMINMAX, SMINMIN, SMIXMAX, SCROLLOFF, SCROLLON,
    create_annotated_slider, create_button, create_button_series, create_combo_box, create_entry,
    create_frame, create_icon_button, create_label)
from .widgetmanager import WidgetManager
from .widgets import AnalysisPlot, BannerLabel, FlipButton

# only for developing; allows to terminate the qt event loop with keyboard interrupt
# from signal import signal, SIGINT, SIG_DFL
# signal(SIGINT, SIG_DFL)


class OSCRUI():

    def __init__(self, args, app_dir_path: str, version: str) -> None:
        """
        Creates new Instance of OSCR.

        Parameters:
        - :param args: command line arguments, following arguments must be accessible
            - `args.config_dir`: contains override for config dir, `str` or `None`
        - :param app_dir_path: absolute path to install directory
        - :param version: version of the app
        """
        self.version: str = version
        self.args = args
        self.app_dir: str = app_dir_path

        # Setting up app base
        self.config: OSCRConfig = OSCRConfig()
        self.config.config_dir = self.get_config_dir_path(self.args.config_dir)
        if self.config.config_dir is None:
            # TODO show error message
            sys.exit(1)
        self.settings = OSCRSettings(Path(self.config.config_dir, self.config.settings_file))
        self.init_settings()
        self.init_config()
        init_translation(self.settings.language)
        QDir.addSearchPath('assets_folder', os.path.join(app_dir_path, 'assets'))
        self.theme: AppTheme = AppTheme(self.config.ui_scale)

        # Setting up GUI including app modules
        self.app, self.window = self.create_main_window()
        self.cache_assets()
        self.widgets: WidgetManager = WidgetManager(self.settings)
        self.tables: AnalysisTables = AnalysisTables(self.theme, self.settings)
        self.graphs: AnalysisGraphs = AnalysisGraphs(self.theme, self.settings)
        self.dialogs: DialogsWrapper = DialogsWrapper(self.window, self.theme)
        self.upload_dialog: UploadresultDialog = UploadresultDialog(self.window, self.theme)
        self.detection_info: DetectionInfoDialog = DetectionInfoDialog(self.window, self.theme)
        self.live_parser: LiveParserWindow = LiveParserWindow(
            self.settings, self.theme, self.dialogs, self.widgets)
        self.parser: ParserBridge = ParserBridge(
            self.settings, self.config, self.widgets, self.dialogs)
        self.parser._tables = self.tables
        self.parser._graphs = self.graphs
        self.league: OSCRLeagueConnector = OSCRLeagueConnector(
            self.widgets, self.dialogs, self.theme, self.config, self.parser, self.upload_dialog)
        self.sidebar: OSCRLeftSidebar = OSCRLeftSidebar(
            version, self.window, self.parser, self.detection_info, self.dialogs, self.widgets,
            self.league, self.theme, self.config, self.settings)
        self.copy_shortcut: QShortcut = QShortcut(
            QKeySequence.StandardKey.Copy, self.window, self.copy_analysis_table_callback)
        self.setup_main_layout()

        # Showing window
        self.window.show()
        if self.settings.auto_scan:
            QTimer.singleShot(
                100,
                lambda: self.parser.analyze_log_file(Path(self.sidebar.log_path_widget.text())))

    def run(self) -> int:
        """
        Runs the event loop.

        :return: exit code of event loop
        """
        return self.app.exec()

    def cache_assets(self):
        """
        Caches assets like icon images
        """
        icons = {
            'oscr': 'oscr_icon_small.png',
            'expand-left': 'expand-left.svg',
            'collapse-left': 'collapse-left.svg',
            'expand-right': 'expand-right.svg',
            'collapse-right': 'collapse-right.svg',
            'edit': 'edit.svg',
            'parser-down': 'parser-down.svg',
            'export-parse': 'export.svg',
            'copy': 'copy.svg',
            'ladder': 'ladder.svg',
            'star-plus': 'star_plus.svg',
            'star-minus': 'star_minus.svg',
            'stocd': 'section31badge.png',
            'stobuilds': 'stobuildslogo.png',
            'close': 'close.svg',
            'expand-top': 'expand-top.svg',
            'collapse-top': 'collapse-top.svg',
            'expand-bottom': 'expand-bottom.svg',
            'collapse-bottom': 'collapse-bottom.svg',
            'check': 'check.svg',
            'dash': 'dash.svg',
            'live-parser': 'live-parser.svg',
            'freeze': 'snowflake.svg',
            'clear-plot': 'clear-plot.svg',
            'error': 'error.svg',
            'warning': 'warning.svg',
            'info': 'info.svg',
            'chevron-right': 'chevron-right.svg',
            'chevron-down': 'chevron-down.svg',
            'TFO-normal': 'TFO_normal.png',
            'TFO-advanced': 'TFO_advanced.png',
            'TFO-elite': 'TFO_elite.png',
            'json': 'json.svg'
        }
        self.theme.icons = load_icon_series(icons, self.app_dir)

    def setup_config_dir(self, dir_path: Path) -> None | OSError:
        """
        Sets up config directory.
        """
        try:
            dir_path.mkdir(exist_ok=True)
            templog_folder_path = dir_path / '_temp'
            templog_folder_path.mkdir(mode=0o755, exist_ok=True)
        except OSError as e:
            return e

    def get_config_dir_path(self, override: str | None = None) -> Path | None:
        """
        Identifies appropriate config directory and returns path to that directory. Returns `None`
        if no usable config dir could be identified.
        """
        if override is not None:
            config_dir = Path(override)
            if self.setup_config_dir(config_dir) is None:
                return config_dir
            else:
                return

        if os.name == 'nt':
            for env_name in ('APPDATA', 'USERPROFILE'):
                config_basedir = os.getenv(env_name)
                if config_basedir is not None:
                    config_dir = Path(config_basedir, 'OSCR_UI')
                    if self.setup_config_dir(config_dir) is None:
                        return config_dir
        else:
            config_basedir = os.getenv('XDG_CONFIG_HOME')
            if config_basedir is not None:
                config_dir = Path(config_basedir, 'OSCR_UI')
                if self.setup_config_dir(config_dir) is None:
                    return config_dir
            home_dir = os.getenv('HOME')
            if home_dir is None:
                return
            config_dir = Path(home_dir, '.config', 'OSCR_UI')
            if self.setup_config_dir(config_dir) is None:
                return config_dir
            config_dir = home_dir / '.oscr_ui'
            if self.setup_config_dir(config_dir) is None:
                return config_dir

    def init_settings(self):
        """
        Prepares settings.
        """
        if not self.settings.log_path:
            if os.name == 'nt':
                self.settings.log_path = os.getenv('USERPROFILE') + '/'
            else:
                self.settings.log_path = os.getenv('HOME') + '/'

    def init_config(self):
        """
        Prepares config.
        """
        self.config.ui_scale = self.settings.ui_scale
        self.config.templog_folder_path = self.config.config_dir / self.config.templog_folder_name
        if os.name == 'nt':
            self.config.home_dir = os.getenv('USERPROFILE') + '/'
        else:
            self.config.home_dir = os.getenv('HOME') + '/'

    @property
    def sidebar_item_width(self) -> int:
        """
        Width of the sidebar.
        """
        return int(
            self.theme.opt.sidebar_item_width * self.window.width() * self.config.ui_scale)

    def main_window_close_callback(self, event: QCloseEvent):
        """
        Executed when application is closed.
        """
        if self.live_parser.isVisible():
            self.live_parser.toggle_window(False)
        self.settings.state__geometry = self.window.saveGeometry()
        self.settings.state__overview_splitter = self.widgets.overview_splitter.saveState()
        self.settings.state__analysis_splitter = self.widgets.analysis_splitter.saveState()
        self.settings.store_settings()
        event.accept()

    def main_window_resize_callback(self, event: QResizeEvent):
        """
        Executed when application is resized.
        """
        self.widgets.sidebar_tabber.setFixedWidth(self.sidebar_item_width)
        event.accept()

    def set_sto_logpath_callback(self, logpath_entry: QLineEdit):
        """
        Formats and stores new logpath to `sto_log_path`.

        Parameters:
        - :param logpath_entry: the entry that holds the path
        """
        formatted_path = format_path(logpath_entry.text())
        self.settings.sto_log_path = formatted_path
        logpath_entry.setText(formatted_path)

    def copy_analysis_table_callback(self):
        """
        Copies the current selection of analysis table as tab-delimited table.
        """
        if self.widgets.main_tabber.currentIndex() != 1:
            return
        current_tab = self.widgets.analysis_tree_tabber.currentIndex()
        self.tables.copy_analysis_table(current_tab)

    def copy_analysis_callback(self):
        """
        Copies data from current analysis table in user-specified format.
        """
        copy_mode = self.widgets.analysis_copy_combobox.currentText()
        current_tab = self.widgets.analysis_tree_tabber.currentIndex()
        self.tables.copy_analysis_data(current_tab, copy_mode)

    # ----------------------------------------------------------------------------------------------
    # GUI building functions below
    # ----------------------------------------------------------------------------------------------

    def create_main_window(self, argv=[]) -> tuple[QApplication, QWidget]:
        """
        Creates and initializes main window.

        :return: QApplication, QWidget
        """
        app = QApplication(argv)
        QThread.currentThread().setPriority(QThread.Priority.TimeCriticalPriority)
        font_database = QFontDatabase()
        font_database.addApplicationFont(get_asset_path('Overpass-Bold.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('Overpass-Medium.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('Overpass-Regular.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('RobotoMono-Regular.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('RobotoMono-Medium.ttf', self.app_dir))
        app.setStyleSheet(self.theme.create_style_sheet(self.theme['app']['style']))
        window = QWidget()
        window.setMinimumSize(
                self.config.ui_scale * self.config.minimum_window_width,
                self.config.ui_scale * self.config.minimum_window_height)
        window.setWindowIcon(load_icon('oscr_icon_small.png', self.app_dir))
        window.setWindowTitle('Open Source Combatlog Reader')
        if self.settings.state__geometry:
            window.restoreGeometry(self.settings.state__geometry)
        window.closeEvent = self.main_window_close_callback
        window.resizeEvent = self.main_window_resize_callback
        return app, window

    def setup_main_layout(self):
        """
        Sets up the main layout of the app.
        """
        layout, main_frame = self.create_master_layout()
        self.window.setLayout(layout)

        margin = self.theme['defaults']['margin']
        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, margin, 0)
        main_layout.setSpacing(0)

        left = create_frame(self.theme)
        left.setSizePolicy(SMAXMIN)
        main_layout.addWidget(left, 0, 0)

        button_column = QGridLayout()
        csp = self.theme['defaults']['csp']
        button_column.setContentsMargins(csp, csp, csp, csp)
        button_column.setRowStretch(0, 1)
        main_layout.addLayout(button_column, 0, 1)
        icon_size = self.theme.opt.icon_size
        left_flip_config = {
            'icon_r': self.theme.icons['collapse-left'], 'func_r': left.hide,
            'icon_l': self.theme.icons['expand-left'], 'func_l': left.show,
            'tooltip_r': tr('Collapse Sidebar'), 'tooltip_l': tr('Expand Sidebar')
        }
        sidebar_flip_button = FlipButton('', '')
        sidebar_flip_button.configure(left_flip_config)
        sidebar_flip_button.setIconSize(QSize(icon_size, icon_size))
        sidebar_flip_button.setStyleSheet(
            self.theme.get_style_class('QPushButton', 'small_button'))
        sidebar_flip_button.setSizePolicy(SMAXMAX)
        button_column.addWidget(sidebar_flip_button, 0, 0, alignment=ATOP)

        graph_flip_config = {
            'icon_r': self.theme.icons['collapse-top'], 'tooltip_r': tr('Collapse Graph'),
            'func_r': self.widgets.collapse_analysis_graph,
            'icon_l': self.theme.icons['expand-top'], 'tooltip_l': tr('Expand Graph'),
            'func_l': self.widgets.expand_analysis_graph
        }
        graph_button = FlipButton('', '')
        graph_button.configure(graph_flip_config)
        graph_button.setIconSize(QSize(icon_size, icon_size))
        graph_button.setStyleSheet(self.theme.get_style_class('QPushButton', 'small_button'))
        graph_button.setSizePolicy(SMAXMAX)
        button_column.addWidget(graph_button, 2, 0)
        graph_button.hide()
        self.widgets.analysis_graph_button = graph_button

        table_flip_config = {
            'icon_r': self.theme.icons['collapse-bottom'], 'tooltip_r': tr('Collapse Table'),
            'func_r': self.tables.collapse_overview_table,
            'icon_l': self.theme.icons['expand-bottom'], 'tooltip_l': tr('Expand Table'),
            'func_l': self.tables.expand_overview_table
        }
        table_button = FlipButton('', '')
        table_button.configure(table_flip_config)
        table_button.setIconSize(QSize(icon_size, icon_size))
        table_button.setStyleSheet(self.theme.get_style_class('QPushButton', 'small_button'))
        table_button.setSizePolicy(SMAXMAX)
        button_column.addWidget(table_button, 3, 0)
        self.widgets.overview_table_button = table_button

        center = create_frame(self.theme)
        center.setSizePolicy(SMINMIN)
        main_layout.addWidget(center, 0, 2)

        main_frame.setLayout(main_layout)
        self.sidebar.create_sidebar(left)
        self.setup_main_tabber(center)
        self.setup_overview_frame()
        self.setup_analysis_frame()
        self.setup_league_standings_frame()
        self.setup_settings_frame()

    def setup_main_tabber(self, frame: QFrame):
        """
        Sets up the tabber switching between Overview, Analysis, League and Settings.

        Parameters:
        - :param frame: QFrame -> parent frame of the sidebar
        """
        o_frame = create_frame(self.theme)
        a_frame = create_frame(self.theme)
        l_frame = create_frame(self.theme)
        s_frame = create_frame(self.theme)

        main_tabber = QTabWidget(frame)
        main_tabber.setStyleSheet(self.theme.get_style_class('QTabWidget', 'tabber'))
        main_tabber.tabBar().hide()
        main_tabber.setSizePolicy(SMINMIN)
        main_tabber.addTab(o_frame, '&O')
        main_tabber.addTab(a_frame, '&A')
        main_tabber.addTab(l_frame, '&L')
        main_tabber.addTab(s_frame, '&S')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_tabber)
        frame.setLayout(layout)

        self.widgets.main_menu_buttons[0].clicked.connect(lambda: self.widgets.switch_main_tab(0))
        self.widgets.main_menu_buttons[1].clicked.connect(lambda: self.widgets.switch_main_tab(1))
        self.widgets.main_menu_buttons[2].clicked.connect(lambda: self.widgets.switch_main_tab(2))
        self.widgets.main_menu_buttons[2].clicked.connect(self.league.establish_league_connection)
        self.widgets.main_menu_buttons[3].clicked.connect(lambda: self.widgets.switch_main_tab(3))
        self.widgets.main_tab_frames.append(o_frame)
        self.widgets.main_tab_frames.append(a_frame)
        self.widgets.main_tab_frames.append(l_frame)
        self.widgets.main_tab_frames.append(s_frame)
        self.widgets.main_tabber = main_tabber

    def setup_overview_frame(self):
        """
        Sets up the frame housing the combatlog overview
        """
        o_frame = self.widgets.main_tab_frames[0]
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        switch_layout = QGridLayout()
        switch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(switch_layout)
        splitter = QSplitter(OVERTICAL)
        splitter.setStyleSheet(self.theme.get_style_class('QSplitter', 'splitter'))
        splitter.setChildrenCollapsible(False)
        self.widgets.overview_splitter = splitter
        layout.addWidget(splitter)

        self.graphs.create_overview_plots()
        o_tabber = QTabWidget(o_frame)
        o_tabber.setStyleSheet(self.theme.get_style_class('QTabWidget', 'tabber'))
        o_tabber.tabBar().hide()
        o_tabber.addTab(self.graphs.dps_bar_plot, 'BAR')
        o_tabber.addTab(self.graphs.dps_graph_plot, 'DPS')
        o_tabber.addTab(self.graphs.dmg_bar_plot, 'DMG')
        o_tabber.setMinimumHeight(self.sidebar_item_width * 0.8)
        splitter.addWidget(o_tabber)
        splitter.setStretchFactor(0, self.theme.opt.overview_graph_stretch)

        switch_layout.setColumnStretch(0, 1)
        switch_frame = create_frame(self.theme)
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 2)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            tr('DPS Bar'): {
                'callback': lambda: self.widgets.switch_overview_tab(0), 'align': ACENTER,
                'toggle': True},
            tr('DPS Graph'): {
                'callback': lambda: self.widgets.switch_overview_tab(1), 'align': ACENTER,
                'toggle': False},
            tr('Damage Graph'): {
                'callback': lambda: self.widgets.switch_overview_tab(2), 'align': ACENTER,
                'toggle': False}
        }
        switcher, buttons = create_button_series(self.theme, switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.overview_menu_buttons = buttons
        icon_layout = QHBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(self.theme['defaults']['csp'])
        copy_button = create_icon_button(self.theme, 'copy', tr('Copy Result'))
        copy_button.clicked.connect(self.parser.copy_summary_data)
        icon_layout.addWidget(copy_button)
        ladder_button = create_icon_button(self.theme, 'ladder', tr('Upload Result'))
        ladder_button.clicked.connect(self.league.upload_callback)
        icon_layout.addWidget(ladder_button)
        switch_layout.addLayout(icon_layout, 0, 2, alignment=ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)
        table_frame = create_frame(self.theme, size_policy=SMINMIN)
        table_frame.setMinimumHeight(self.sidebar_item_width * 0.4)
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        sorting_proxy = SortingProxy()
        self.parser.overview_table_model.init_fonts(
            self.theme.get_font('table_header'), self.theme.get_font('table'))
        sorting_proxy.setSourceModel(self.parser.overview_table_model)
        table = QTableView()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setModel(sorting_proxy)
        self.tables.style_table(table)
        table_layout.addWidget(table)
        self.tables.overview_table = table
        table_frame.setLayout(table_layout)
        splitter.addWidget(table_frame)
        self.tables.overview_table_frame = table_frame
        o_frame.setLayout(layout)
        if self.settings.state__overview_splitter:
            splitter.restoreState(self.settings.state__overview_splitter)
        else:
            h = splitter.height()
            splitter.setSizes((h * 0.5, h * 0.5))
        self.widgets.overview_tabber = o_tabber

    def create_analysis_tab(
            self, graph_frame: QFrame, tree_frame: QFrame, tree_model: TreeModel,
            is_heal_table: bool) -> tuple[QTreeView, AnalysisPlot]:
        """
        Creates analysis graph and table, prepares and returns them.

        Parameters:
        - :param graph_frame: frame to put the graph into
        - :param tree_frame: frame to put the tree table into
        - :param tree_model: data model for the tree table
        - :param is_heal_table: initializes `tree_model` with heal header if `True`; initializes
        `tree_model` with damage header if `False`
        """
        csp = self.theme['defaults']['csp'] * self.config.ui_scale
        graph_layout = QHBoxLayout()
        graph_layout.setContentsMargins(csp, csp, csp, 0)
        graph_layout.setSpacing(csp)

        plot_bundle_frame = create_frame(self.theme, size_policy=SMINMAX)
        plot_bundle_layout = QVBoxLayout()
        plot_bundle_layout.setContentsMargins(0, 0, 0, 0)
        plot_bundle_layout.setSpacing(0)
        plot_bundle_layout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        plot_legend_frame = create_frame(self.theme)
        plot_legend_layout = QHBoxLayout()
        plot_legend_layout.setContentsMargins(0, 0, 0, 0)
        plot_legend_layout.setSpacing(2 * self.theme['defaults']['margin'])
        plot_legend_frame.setLayout(plot_legend_layout)
        plot_widget = AnalysisPlot(self.theme, self.theme['plot']['color_cycler'])
        plot_widget.setStyleSheet(self.theme.get_style('plot_widget_nullifier'))
        plot_widget.setSizePolicy(SMINMAX)
        plot_bundle_layout.addWidget(plot_widget)
        plot_bundle_layout.addWidget(plot_legend_frame, alignment=AHCENTER)
        plot_bundle_frame.setLayout(plot_bundle_layout)
        graph_layout.addWidget(plot_bundle_frame, stretch=1)

        plot_button_frame = create_frame(self.theme, size_policy=SMAXMIN)
        plot_button_layout = QVBoxLayout()
        plot_button_layout.setContentsMargins(0, 0, 0, 0)
        plot_button_layout.setSpacing(0)
        plot_button_layout.setAlignment(AVCENTER)
        freeze_button = create_icon_button(self.theme, 'freeze', tr('Freeze Graph'))
        freeze_button.setCheckable(True)
        freeze_button.setChecked(True)
        freeze_button.clicked.connect(plot_widget.toggle_freeze)
        plot_button_layout.addWidget(freeze_button, alignment=ABOTTOM)
        clear_button = create_icon_button(self.theme, 'clear-plot', tr('Clear Graph'))
        clear_button.clicked.connect(plot_widget.clear)
        plot_button_layout.addWidget(clear_button, alignment=ATOP)
        plot_button_frame.setLayout(plot_button_layout)
        graph_layout.addWidget(plot_button_frame, stretch=0)
        graph_frame.setLayout(graph_layout)

        tree_layout = QVBoxLayout()
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)
        tree = self.tables.create_analysis_table('tree_table')
        if is_heal_table:
            tree_model.header_data = tr(HEAL_TREE_HEADER)
        else:
            tree_model.header_data = tr(TREE_HEADER)
        tree_model.init_fonts(
            self.theme.get_font('tree_table_header'), self.theme.get_font('tree_table'),
            self.theme.get_font('tree_table_cells'))
        tree.setModel(tree_model)
        tree.setSelectionModel(TreeSelectionModel(tree_model))
        tree.clicked.connect(lambda index, pw=plot_widget: pw.add_bar(index.internalPointer()))
        tree_layout.addWidget(tree)
        tree_frame.setLayout(tree_layout)
        return tree, plot_widget

    def setup_analysis_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        a_frame = self.widgets.main_tab_frames[1]
        dout_graph_frame = create_frame(self.theme)
        dtaken_graph_frame = create_frame(self.theme)
        hout_graph_frame = create_frame(self.theme)
        hin_graph_frame = create_frame(self.theme)
        dout_tree_frame = create_frame(self.theme)
        dtaken_tree_frame = create_frame(self.theme)
        hout_tree_frame = create_frame(self.theme)
        hin_tree_frame = create_frame(self.theme)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        switch_layout = QGridLayout()
        switch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(switch_layout)
        splitter = QSplitter(OVERTICAL)
        splitter.setStyleSheet(self.theme.get_style_class('QSplitter', 'splitter'))
        splitter.setChildrenCollapsible(False)
        self.widgets.analysis_splitter = splitter
        layout.addWidget(splitter)

        a_graph_tabber = QTabWidget(a_frame)
        a_graph_tabber.setStyleSheet(self.theme.get_style_class('QTabWidget', 'tabber'))
        a_graph_tabber.tabBar().hide()
        a_graph_tabber.addTab(dout_graph_frame, 'DOUT')
        a_graph_tabber.addTab(dtaken_graph_frame, 'DTAKEN')
        a_graph_tabber.addTab(hout_graph_frame, 'HOUT')
        a_graph_tabber.addTab(hin_graph_frame, 'HIN')
        self.widgets.analysis_graph_tabber = a_graph_tabber
        splitter.addWidget(a_graph_tabber)
        if not self.settings.analysis_graph:
            self.widgets.analysis_graph_button.flip()
        a_tree_tabber = QTabWidget(a_frame)
        a_tree_tabber.setStyleSheet(self.theme.get_style_class('QTabWidget', 'tabber'))
        a_tree_tabber.tabBar().hide()
        a_tree_tabber.addTab(dout_tree_frame, 'DOUT')
        a_tree_tabber.addTab(dtaken_tree_frame, 'DTAKEN')
        a_tree_tabber.addTab(hout_tree_frame, 'HOUT')
        a_tree_tabber.addTab(hin_tree_frame, 'HIN')
        self.widgets.analysis_tree_tabber = a_tree_tabber
        splitter.addWidget(a_tree_tabber)

        switch_layout.setColumnStretch(0, 1)
        switch_frame = create_frame(self.theme)
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 1)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            tr('Damage Out'): {
                'callback': lambda _: self.widgets.switch_analysis_tab(0), 'align': ACENTER,
                'toggle': True},
            tr('Damage Taken'): {
                'callback': lambda _: self.widgets.switch_analysis_tab(1), 'align': ACENTER,
                'toggle': False},
            tr('Heals Out'): {
                'callback': lambda _: self.widgets.switch_analysis_tab(2), 'align': ACENTER,
                'toggle': False},
            tr('Heals In'): {
                'callback': lambda _: self.widgets.switch_analysis_tab(3), 'align': ACENTER,
                'toggle': False}
        }
        switcher, buttons = create_button_series(self.theme, switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.analysis_menu_buttons = buttons
        copy_layout = QHBoxLayout()
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(self.theme['defaults']['csp'])
        copy_combobox = create_combo_box(self.theme)
        copy_combobox.addItems((
            tr('Selection'), tr('Global Max One Hit'), tr('Max One Hit'), tr('Magnitude'),
            tr('Magnitude / s')))
        copy_layout.addWidget(copy_combobox)
        self.widgets.analysis_copy_combobox = copy_combobox
        copy_button = create_icon_button(self.theme, 'copy', 'Copy Data')
        copy_button.clicked.connect(self.copy_analysis_callback)
        copy_layout.addWidget(copy_button)
        switch_layout.addLayout(copy_layout, 0, 2, alignment=ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)

        self.tables.damage_out_table, _ = self.create_analysis_tab(
            dout_graph_frame, dout_tree_frame, self.parser.damage_out_model, is_heal_table=False)
        self.tables.damage_in_table, _ = self.create_analysis_tab(
            dtaken_graph_frame, dtaken_tree_frame, self.parser.damage_in_model, is_heal_table=False)
        self.tables.heal_out_table, _ = self.create_analysis_tab(
            hout_graph_frame, hout_tree_frame, self.parser.heal_out_model, is_heal_table=True)
        self.tables.heal_in_table, _ = self.create_analysis_tab(
            hin_graph_frame, hin_tree_frame, self.parser.heal_in_model, is_heal_table=True)

        a_frame.setLayout(layout)
        if self.settings.state__analysis_splitter:
            splitter.restoreState(self.settings.state__analysis_splitter)
        else:
            h = splitter.height()
            splitter.setSizes((h * 0.5, h * 0.5))

    def setup_league_standings_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        l_frame = self.widgets.main_tab_frames[2]
        m = self.theme['defaults']['csp']
        layout = QVBoxLayout()
        layout.setContentsMargins(0, m, 0, m)
        layout.setSpacing(m)

        ladder_table = QTableView()
        table_style = {'border-style': 'solid', 'border-width': '@bw', 'border-color': '@bc'}
        self.tables.style_table(ladder_table, table_style, single_row_selection=True)
        self.league.ladder_table_model.init_fonts(
            self.theme.get_font('table_header'), self.theme.get_font('table'))
        ladder_table.setModel(self.league.ladder_table_sort)
        self.widgets.ladder_table = ladder_table
        layout.addWidget(ladder_table, stretch=1)

        control_layout = QGridLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(0)
        control_layout.setColumnStretch(2, 1)
        search_label = create_label(
            self.theme, tr('Search:'), 'label_subhead', style_override={'margin-bottom': 0})
        control_layout.addWidget(search_label, 0, 0, alignment=AVCENTER)
        search_bar = create_entry(
            self.theme, placeholder=tr('name@handle'),
            style_override={'margin-left': '@isp', 'margin-top': 0})
        search_bar.textChanged.connect(self.league.apply_league_table_filter)
        control_layout.addWidget(search_bar, 0, 1, alignment=AVCENTER)
        control_button_style = {
            tr('View Parse'): {'callback': self.league.download_and_view_combat},
            tr('More'): {'callback': self.league.extend_ladder, 'style': {'margin-right': 0}}
        }
        control_button_layout = create_button_series(
            self.theme, control_button_style, 'button', seperator='•')
        control_layout.addLayout(control_button_layout, 0, 3, alignment=AVCENTER)
        layout.addLayout(control_layout)

        l_frame.setLayout(layout)

    def create_master_layout(self) -> tuple[QVBoxLayout, QFrame]:
        """
        Creates and returns the master layout for an OSCR window.

        :return: populated QVBoxlayout and content frame QFrame
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        bg_frame = create_frame(self.theme, style_override={'background-color': '@oscr'})
        bg_frame.setSizePolicy(SMINMIN)
        layout.addWidget(bg_frame)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        lbl = BannerLabel(get_asset_path('oscrbanner-slim-dark-label.png', self.app_dir), bg_frame)
        main_layout.addWidget(lbl)

        menu_frame = create_frame(self.theme, style_override={'background-color': '@oscr'})
        menu_frame.setSizePolicy(SMINMAX)
        menu_frame.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(menu_frame)
        menu_layout = QGridLayout()
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)
        menu_layout.setColumnStretch(1, 1)
        menu_button_style = {
            tr('Overview'): {'style': {'margin-left': '@isp'}},
            tr('Analysis'): {},
            tr('League Standings'): {},
            tr('Settings'): {},
        }
        bt_lay, buttons = create_button_series(
            self.theme, menu_button_style, style='menu_button', seperator='•', ret=True)
        menu_layout.addLayout(bt_lay, 0, 0)
        self.widgets.main_menu_buttons = buttons

        size = [self.theme.opt.icon_size * 1.3] * 2
        live_parser_button = create_icon_button(
            self.theme, 'live-parser', tr('Live Parser'), 'live_icon_button', icon_size=size)
        live_parser_button.setCheckable(True)
        live_parser_button.clicked[bool].connect(self.live_parser.toggle_window)
        menu_layout.addWidget(live_parser_button, 0, 2)
        self.widgets.live_parser_button = live_parser_button
        menu_frame.setLayout(menu_layout)

        w = self.theme['app']['frame_thickness']
        main_frame = create_frame(self.theme, style_override={'margin': (0, w, w, w)})
        main_frame.setSizePolicy(SMINMIN)
        main_layout.addWidget(main_frame)
        bg_frame.setLayout(main_layout)

        return layout, main_frame

    def setup_settings_frame(self):
        """
        Populates the settings frame.
        """
        settings_frame = self.widgets.main_tab_frames[3]
        settings_layout = QHBoxLayout()
        isp = self.theme['defaults']['isp']
        settings_layout.setContentsMargins(2 * isp, isp, isp, isp)
        settings_layout.setSpacing(isp)
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(isp)
        scroll_frame = create_frame(self.theme)
        scroll_area = QScrollArea()
        scroll_area.setSizePolicy(SMINMIN)
        scroll_area.setHorizontalScrollBarPolicy(SCROLLOFF)
        scroll_area.setVerticalScrollBarPolicy(SCROLLON)
        scroll_area.setAlignment(AHCENTER)
        settings_layout.addWidget(scroll_area)
        settings_frame.setLayout(settings_layout)

        # first section
        sec_1 = QGridLayout()
        sec_1.setContentsMargins(0, 0, 0, 0)
        sec_1.setVerticalSpacing(self.theme['defaults']['isp'])
        sec_1.setHorizontalSpacing(self.theme['defaults']['csp'])

        combat_delta_label = create_label(
            self.theme, tr('Seconds Between Combats:'), 'label_subhead')
        sec_1.addWidget(combat_delta_label, 0, 0, alignment=ARIGHT)
        combat_delta_validator = QIntValidator()
        combat_delta_validator.setBottom(1)
        combat_delta_entry = create_entry(
            self.theme, str(self.settings.seconds_between_combats),
            combat_delta_validator, style_override={'margin-top': 0})
        combat_delta_entry.setSizePolicy(SMIXMAX)
        combat_delta_entry.editingFinished.connect(
            lambda: self.settings.set('seconds_between_combats', int(combat_delta_entry.text())))
        sec_1.addWidget(combat_delta_entry, 0, 1, alignment=AVCENTER)

        combat_num_label = create_label(
            self.theme, tr('Number of combats to isolate:'), 'label_subhead')
        sec_1.addWidget(combat_num_label, 1, 0, alignment=ARIGHT)
        combat_num_validator = QIntValidator()
        combat_num_validator.setBottom(1)
        combat_num_entry = create_entry(
            self.theme, str(self.settings.combats_to_parse), combat_num_validator,
            style_override={'margin-top': 0})
        combat_num_entry.setSizePolicy(SMIXMAX)
        combat_num_entry.editingFinished.connect(
            lambda: self.settings.set('combats_to_parse', int(combat_num_entry.text())))
        sec_1.addWidget(combat_num_entry, 1, 1, alignment=AVCENTER)

        combat_lines_label = create_label(
            self.theme, tr('Minimum number of lines per combat:'), 'label_subhead')
        sec_1.addWidget(combat_lines_label, 2, 0, alignment=ARIGHT)
        combat_lines_validator = QIntValidator()
        combat_lines_validator.setBottom(1)
        combat_lines_entry = create_entry(
            self.theme, str(self.settings.combat_min_lines), combat_lines_validator,
            style_override={'margin-top': 0})
        combat_lines_entry.setSizePolicy(SMIXMAX)
        combat_lines_entry.editingFinished.connect(
            lambda: self.settings.set('combat_min_lines', int(combat_lines_entry.text())))
        sec_1.addWidget(combat_lines_entry, 2, 1, alignment=AVCENTER)

        graph_resolution_label = create_label(
            self.theme, tr('Graph resolution (interval in seconds):'), 'label_subhead')
        sec_1.addWidget(graph_resolution_label, 3, 0, alignment=ARIGHT)
        graph_resolution_layout = create_annotated_slider(
            self.theme, self.settings.graph_resolution * 10, 1, 20,
            callback=self.settings.set_graph_resolution)
        sec_1.addLayout(graph_resolution_layout, 3, 1, alignment=ALEFT)

        overview_sort_label = create_label(
            self.theme, tr('Sort overview table by column:'), 'label_subhead')
        sec_1.addWidget(overview_sort_label, 4, 0, alignment=ARIGHT)
        overview_sort_combo = create_combo_box(self.theme, style_override={'font': '@small_text'})
        overview_sort_combo.addItems(TABLE_HEADER)
        overview_sort_combo.setCurrentIndex(self.settings.overview_sort_column)
        overview_sort_combo.currentIndexChanged.connect(
            lambda new_index: self.settings.set('overview_sort_column', new_index))
        sec_1.addWidget(overview_sort_combo, 4, 1, alignment=ALEFT | AVCENTER)

        overview_sort_order_label = create_label(
            self.theme, tr('Overview table sort order:'), 'label_subhead')
        sec_1.addWidget(overview_sort_order_label, 5, 0, alignment=ARIGHT)
        overview_sort_order_combo = create_combo_box(
            self.theme, style_override={'font': '@small_text'})
        overview_sort_order_combo.addItems((tr('Descending'), tr('Ascending')))
        overview_sort_order_combo.setCurrentText(self.settings.overview_sort_order)
        overview_sort_order_combo.currentTextChanged.connect(
            lambda new_text: self.settings.set('overview_sort_order', new_text))
        sec_1.addWidget(overview_sort_order_combo, 5, 1, alignment=ALEFT | AVCENTER)

        auto_scan_label = create_label(self.theme, tr('Scan log automatically:'), 'label_subhead')
        sec_1.addWidget(auto_scan_label, 6, 0, alignment=ARIGHT)
        auto_scan_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
        auto_scan_button.setStyleSheet(self.theme.get_style_class(
            'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        auto_scan_button.setFont(self.theme.get_font('app', '@font'))
        auto_scan_button.r_function = lambda: self.settings.set('auto_scan', True)
        auto_scan_button.l_function = lambda: self.settings.set('auto_scan', False)
        if self.settings.auto_scan:
            auto_scan_button.flip()
        sec_1.addWidget(auto_scan_button, 6, 1, alignment=ALEFT | AVCENTER)
        sto_log_path_button = create_button(self.theme, tr('STO Logfile:'), style_override={
            'margin': 0, 'font': ('Overpass', 11, 'medium'), 'border-color': '@bc',
            'border-style': 'solid', 'border-width': '@bw', 'padding-bottom': 1})
        sec_1.addWidget(sto_log_path_button, 7, 0, alignment=ARIGHT | AVCENTER)
        sto_log_path_entry = create_entry(
            self.theme, self.settings.sto_log_path, style_override={'margin-top': 0})
        sto_log_path_entry.setSizePolicy(SMIXMAX)
        sto_log_path_entry.editingFinished.connect(
            lambda: self.set_sto_logpath_callback(sto_log_path_entry))
        sec_1.addWidget(sto_log_path_entry, 7, 1, alignment=AVCENTER)
        sto_log_path_button.clicked.connect(lambda: self.browse_sto_logpath(sto_log_path_entry))

        opacity_label = create_label(self.theme, tr('Live Parser Opacity:'), 'label_subhead')
        sec_1.addWidget(opacity_label, 8, 0, alignment=ARIGHT)
        opacity_slider_layout = create_annotated_slider(
            self.theme, default_value=round(self.settings.liveparser__window_opacity * 20, 0),
            min=1, max=20, callback=self.settings.set_liveparser_opacity,
            style_override_slider={'::sub-page:horizontal': {'background-color': '@bc'}})
        sec_1.addLayout(opacity_slider_layout, 8, 1, alignment=AVCENTER)

        live_graph_active_label = create_label(
            self.theme, tr('LiveParser Graph:'), 'label_subhead')
        sec_1.addWidget(live_graph_active_label, 9, 0, alignment=ARIGHT)
        live_graph_active_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
        live_graph_active_button.setStyleSheet(self.theme.get_style_class(
            'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        live_graph_active_button.setFont(self.theme.get_font('app', '@font'))
        live_graph_active_button.r_function = (
            lambda: self.settings.set('liveparser__graph_active', True))
        live_graph_active_button.l_function = (
            lambda: self.settings.set('liveparser__graph_active', False))
        if self.settings.liveparser__graph_active:
            live_graph_active_button.flip()
        sec_1.addWidget(live_graph_active_button, 9, 1, alignment=ALEFT | AVCENTER)

        live_graph_field_label = create_label(
            self.theme, tr('LiveParser Graph Field:'), 'label_subhead')
        sec_1.addWidget(live_graph_field_label, 10, 0, alignment=ARIGHT)
        live_graph_field_combo = create_combo_box(
            self.theme, style_override={'font': '@small_text'})
        live_graph_field_combo.addItems(self.config.live_graph_fields)
        live_graph_field_combo.setCurrentIndex(self.settings.liveparser__graph_field)
        live_graph_field_combo.currentIndexChanged.connect(
            lambda new_index: self.settings.set('liveparser__graph_field', new_index))
        sec_1.addWidget(live_graph_field_combo, 10, 1, alignment=ALEFT)

        live_name_label = create_label(self.theme, tr('LiveParser Player:'), 'label_subhead')
        sec_1.addWidget(live_name_label, 11, 0, alignment=ARIGHT)
        live_player_combo = create_combo_box(self.theme, style_override={'font': '@small_text'})
        live_player_combo.addItems(('Name', 'Handle'))
        live_player_combo.setCurrentText(self.settings.liveparser__player_display)
        live_player_combo.currentTextChanged.connect(
            lambda new_text: self.settings.set('liveparser__player_display', new_text))
        sec_1.addWidget(live_player_combo, 11, 1, alignment=ALEFT)

        overview_tab_label = create_label(self.theme, tr('Default Overview Tab:'), 'label_subhead')
        sec_1.addWidget(overview_tab_label, 12, 0, alignment=ARIGHT)
        overview_tab_combo = create_combo_box(self.theme, style_override={'font': '@small_text'})
        overview_tab_combo.addItems((tr('DPS Bar'), tr('DPS Graph'), tr('Damage Graph')))
        overview_tab_combo.setCurrentIndex(self.settings.first_overview_tab)
        overview_tab_combo.currentIndexChanged.connect(
            lambda new_index: self.settings.set('first_overview_tab', new_index))
        sec_1.addWidget(overview_tab_combo, 12, 1, alignment=ALEFT)

        ui_scale_label = create_label(self.theme, tr('UI Scale:'), 'label_subhead')
        sec_1.addWidget(ui_scale_label, 13, 0, alignment=ARIGHT)
        ui_scale_slider_layout = create_annotated_slider(
            self.theme, default_value=round(self.settings.ui_scale * 50, 0), min=25, max=75,
            callback=self.settings.set_ui_scale)
        sec_1.addLayout(ui_scale_slider_layout, 13, 1, alignment=ALEFT)

        ui_scale_label = create_label(self.theme, tr('LiveParser Scale:'), 'label_subhead')
        sec_1.addWidget(ui_scale_label, 14, 0, alignment=ARIGHT)
        live_scale_slider_layout = create_annotated_slider(
            self.theme, default_value=round(self.settings.liveparser__window_scale * 50, 0),
            min=25, max=75, callback=self.settings.set_liveparser_scale)
        sec_1.addLayout(live_scale_slider_layout, 14, 1, alignment=ALEFT)
        sec_1.setAlignment(AHCENTER)

        live_enabled_label = create_label(
            self.theme, tr('LiveParser default state:'), 'label_subhead')
        sec_1.addWidget(live_enabled_label, 15, 0, alignment=ARIGHT)
        live_enabled_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
        live_enabled_button.setStyleSheet(self.theme.get_style_class(
            'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        live_enabled_button.setFont(self.theme.get_font('app', '@font'))
        live_enabled_button.r_function = (
            lambda: self.settings.set('liveparser__auto_enabled', True))
        live_enabled_button.l_function = (
            lambda: self.settings.set('liveparser__auto_enabled', False))
        if self.settings.liveparser__auto_enabled:
            live_enabled_button.flip()
        sec_1.addWidget(live_enabled_button, 15, 1, alignment=ALEFT)

        result_format_label = create_label(
            self.theme, tr('Result Clipboard Format:'), 'label_subhead')
        sec_1.addWidget(result_format_label, 16, 0, alignment=ARIGHT)
        result_format_combo = create_combo_box(self.theme, style_override={'font': '@small_text'})
        result_format_combo.addItems(('Compact', 'Verbose', 'CSV'))
        result_format_combo.setCurrentText(self.settings.copy_format)
        result_format_combo.currentTextChanged.connect(
            lambda new_text: self.settings.set('copy_format', new_text))
        sec_1.addWidget(result_format_combo, 16, 1, alignment=ALEFT)

        live_copy_label = create_label(
            self.theme, tr('Show kills in LiveParser Copy:'), 'label_subhead')
        sec_1.addWidget(live_copy_label, 17, 0, alignment=ARIGHT)
        live_copy_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
        live_copy_button.setStyleSheet(self.theme.get_style_class(
                'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        live_copy_button.setFont(self.theme.get_font('app', '@font'))
        live_copy_button.r_function = lambda: self.settings.set('liveparser__copy_kills', True)
        live_copy_button.l_function = lambda: self.settings.set('liveparser__copy_kills', False)
        if self.settings.liveparser__copy_kills:
            live_copy_button.flip()
        sec_1.addWidget(live_copy_button, 17, 1, alignment=ALEFT)

        languages = ('English',)  # 'Chinese', 'German')
        language_codes = ('en',)  # 'zh', 'de')
        language_label = create_label(self.theme, tr('Language:'), 'label_subhead')
        sec_1.addWidget(language_label, 18, 0, alignment=ARIGHT)
        language_combo = create_combo_box(self.theme, style_override={'font': '@small_text'})
        language_combo.addItems(languages)
        current_language_code = self.settings.language
        language_combo.setCurrentText(languages[language_codes.index(current_language_code)])
        language_combo.currentIndexChanged.connect(
            lambda index: self.settings.set('language', language_codes[index]))
        sec_1.addWidget(language_combo, 18, 1, alignment=ALEFT | AVCENTER)
        scroll_layout.addLayout(sec_1)

        # seperator
        section_seperator = create_frame(
            self.theme, 'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
        section_seperator.setFixedHeight(self.theme['defaults']['bw'])
        scroll_layout.addWidget(section_seperator)

        # second section
        hider_frame_style_override = {
            'border-color': '@lbg',
            'border-width': '@bw', 'border-style': 'solid', 'border-radius': 2
        }
        sec_2 = QVBoxLayout()
        sec_2.setContentsMargins(0, isp, 0, 0)
        sec_2.setSpacing(isp)
        sec_2.setAlignment(AHCENTER)
        dmg_hider_label = create_label(
            self.theme, tr('Damage table columns:'), 'label_subhead')
        sec_2.addWidget(dmg_hider_label)
        dmg_hider_layout = QVBoxLayout()
        dmg_hider_frame = create_frame(
            self.theme, size_policy=SMINMAX, style_override=hider_frame_style_override)
        dmg_hider_frame.setMinimumWidth(self.sidebar_item_width)
        for i, head in enumerate(tr(TREE_HEADER)[1:]):
            bt = create_button(
                self.theme, head, 'toggle_button', toggle=self.settings.dmg_columns[i])
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                lambda state, i=i: self.settings.dmg_columns.__setitem__(i, state))
            dmg_hider_layout.addWidget(bt, stretch=1)
        dmg_seperator = create_frame(
            self.theme, 'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
        dmg_seperator.setFixedHeight(self.theme['defaults']['bw'])
        dmg_hider_layout.addWidget(dmg_seperator)
        apply_button = create_button(self.theme, tr('Apply'), 'button')
        apply_button.clicked.connect(self.tables.update_shown_damage_columns)
        dmg_hider_layout.addWidget(apply_button, alignment=ARIGHT | ATOP)
        dmg_hider_frame.setLayout(dmg_hider_layout)
        sec_2.addWidget(dmg_hider_frame, alignment=ATOP)

        heal_hider_label = create_label(
            self.theme, tr('Heal table columns:'), 'label_subhead')
        sec_2.addWidget(heal_hider_label)
        heal_hider_layout = QVBoxLayout()
        heal_hider_frame = create_frame(
            self.theme, size_policy=SMINMAX, style_override=hider_frame_style_override)
        for i, head in enumerate(tr(HEAL_TREE_HEADER)[1:]):
            bt = create_button(
                self.theme, head, 'toggle_button', toggle=self.settings.heal_columns[i])
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                lambda state, i=i: self.settings.heal_columns.__setitem__(i, state))
            heal_hider_layout.addWidget(bt, stretch=1)
        heal_seperator = create_frame(
            self.theme, 'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
        heal_seperator.setFixedHeight(self.theme['defaults']['bw'])
        heal_hider_layout.addWidget(heal_seperator)
        apply_button_2 = create_button(self.theme, tr('Apply'), 'button')
        apply_button_2.clicked.connect(self.tables.update_shown_heal_columns)
        heal_hider_layout.addWidget(apply_button_2, alignment=ARIGHT | ATOP)
        heal_hider_frame.setLayout(heal_hider_layout)

        sec_2.addWidget(heal_hider_frame, alignment=ATOP)
        live_hider_label = create_label(
            self.theme, tr('Live Parser columns:'), 'label_subhead')
        sec_2.addWidget(live_hider_label)
        live_hider_layout = QVBoxLayout()
        live_hider_frame = create_frame(
            self.theme, size_policy=SMINMAX, style_override=hider_frame_style_override)
        for i, head in enumerate(tr(LIVE_TABLE_HEADER)):
            bt = create_button(
                self.theme, head, 'toggle_button', toggle=self.settings.liveparser__columns[i])
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                lambda state, i=i: self.settings.liveparser__columns.__setitem__(i, state))
            live_hider_layout.addWidget(bt, stretch=1)
        live_separator = create_frame(
            self.theme, 'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
        live_separator.setFixedHeight(self.theme['defaults']['bw'])
        live_hider_layout.addWidget(live_separator)
        apply_button_3 = create_button(self.theme, tr('Apply'), 'button')
        apply_button_3.clicked.connect(self.live_parser.update_shown_columns)
        live_hider_layout.addWidget(apply_button_3, alignment=ARIGHT | ATOP)
        live_hider_frame.setLayout(live_hider_layout)
        sec_2.addWidget(live_hider_frame, alignment=ATOP)

        scroll_layout.addLayout(sec_2)

        scroll_frame.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_frame)
