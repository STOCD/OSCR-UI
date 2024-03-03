from signal import signal, SIGINT, SIG_DFL
import os

from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QFrame, QListWidget, QTabWidget, QTableView
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import QSize, QSettings
from PySide6.QtGui import QIntValidator

from OSCR import TREE_HEADER, HEAL_TREE_HEADER

from .iofunctions import load_icon_series, get_asset_path, load_icon
from .textedit import format_path
from .widgets import BannerLabel, FlipButton, WidgetStorage, AnalysisPlot
from .widgetbuilder import SMAXMAX, SMAXMIN, SMINMAX, SMINMIN, ALEFT, ARIGHT, ATOP, ACENTER, AHCENTER, ABOTTOM
from .leagueconnector import OSCRClient

# only for developing; allows to terminate the qt event loop with keyboard interrupt
signal(SIGINT, SIG_DFL)

class OSCRUI():


    from .datafunctions import init_parser, copy_summary_callback, copy_analysis_callback
    from .datafunctions import analyze_log_callback, update_shown_columns_dmg, update_shown_columns_heal
    from .displayer import create_legend_item
    from .iofunctions import browse_path
    from .style import get_style_class, create_style_sheet, theme_font, get_style
    from .widgetbuilder import create_frame, create_label, create_button_series, create_icon_button
    from .widgetbuilder import create_analysis_table, create_button, create_combo_box, style_table
    from .widgetbuilder import split_dialog, create_entry
    from .leagueconnector import upload_callback, update_ladder_index, establish_league_connection

    app_dir = None

    config = {} # see main.py for contents

    settings: QSettings # see main.py for defaults

    # stores widgets that need to be accessed from outside their creating function
    widgets: WidgetStorage

    league_api: OSCRClient

    def __init__(self, version, theme, args, path, config) -> None:
        """
        Creates new Instance of OSCR.

        Parameters:
        - :param version: version of the app
        - :param theme: dict -> default theme
        - :param args: command line arguments
        - :param path: absolute path to main.py file
        - :param config: app configuration (!= settings these are not changed by the user)
        """
        self.version = version
        self.theme = theme
        self.args = args
        self.app_dir = path
        self.config = config
        self.widgets = WidgetStorage()
        self.league_api = None
        self.init_settings()
        self.app, self.window = self.create_main_window()
        self.init_config()
        self.init_parser()
        self.cache_assets()
        self.setup_main_layout()
        self.window.show()

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
            'save': 'save.svg',
            'log-up': 'log-up.svg',
            'log-down': 'log-down.svg',
            'log-cut': 'log-cut-tight.svg',
            'parser-left': 'parser-left.svg',
            'parser-right': 'parser-right.svg',
            'export-parse': 'export-parse.svg',
            'copy': 'copy.svg',
            'ladder': 'ladder.svg'
        }
        self.icons = load_icon_series(icons, self.app_dir)

    def init_settings(self):
        """
        Prepares settings. Loads stored settings. Saves current settings for next startup.
        """
        settings_path = os.path.abspath(self.app_dir + self.config["settings_path"])
        self.settings = QSettings(settings_path, QSettings.Format.IniFormat)
        for setting, value in self.config['default_settings'].items():
            if self.settings.value(setting, None) is None:
                self.settings.setValue(setting, value)
        if not self.settings.value('log_path', ''):
            self.settings.setValue('log_path', format_path(self.app_dir))
        
    def init_config(self):
        """
        Prepares config.
        """
        self.current_combat_id = -1
        self.current_combat_path = ''
        self.config['templog_folder_path'] = os.path.abspath(
                self.app_dir + self.config['templog_folder_path'])
    
    @property
    def parser_settings(self) -> dict:
        """
        Returns settings relevant to the parser
        """
        relevant_settings = (('combats_to_parse', int), ('seconds_between_combats', int),
                ('excluded_event_ids',  list), ('graph_resolution', float))
        settings = dict()
        for setting_key, settings_type in relevant_settings:
            setting = self.settings.value(setting_key, type=settings_type, defaultValue='')
            if setting:
                settings[setting_key] = setting
        settings['templog_folder_path'] = self.config['templog_folder_path']
        return settings


    @property
    def sidebar_item_width(self) -> int:
        """
        Width of the sidebar.
        """
        return int(self.theme['s.c']['sidebar_item_width'] * self.window.width())

    def main_window_close_callback(self, event):
        """
        Executed when application is closed.
        """
        window_geometry = self.window.saveGeometry()
        self.settings.setValue('geometry', window_geometry)
        event.accept()

    def main_window_resize_callback(self, event):
        """
        Executed when application is resized.
        """
        self.entry.setFixedWidth(self.sidebar_item_width)
        self.current_combats.setFixedWidth(self.sidebar_item_width)
        self.widgets.ladder_map.setFixedWidth(self.sidebar_item_width)
        event.accept()
    
    # -------------------------------------------------------------------------------------------------------
    # GUI functions below
    # -------------------------------------------------------------------------------------------------------

    def create_main_window(self, argv=[]) -> tuple[QApplication, QWidget]:
        """
        Creates and initializes main window.

        :return: QApplication, QWidget
        """
        app = QApplication(argv)
        app.setStyleSheet(self.create_style_sheet(self.theme['app']['style']))
        window = QWidget()
        window.setWindowIcon(load_icon('oscr_icon_small.png', self.app_dir))
        window.setWindowTitle('Open Source Combatlog Reader')
        window.setMinimumSize(
                int(self.config['minimum_window_width']),
                int(self.config['minimum_window_height']))
        if self.settings.value('geometry'):
            window.restoreGeometry(self.settings.value('geometry'))        
        window.closeEvent = self.main_window_close_callback
        window.resizeEvent = self.main_window_resize_callback
        return app, window

    def setup_main_layout(self):
        """
        Sets up the main layout of the app.
        """
        layout, main_frame = self.create_master_layout(self.window)
        self.window.setLayout(layout)

        content_layout = QGridLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        left = self.create_frame(main_frame)
        left.setSizePolicy(SMAXMIN)
        content_layout.addWidget(left, 0, 0)

        right = self.create_frame(main_frame, 'frame', 
                {'border-left-style': 'solid', 'border-left-width': '@sep', 'border-left-color': '@oscr' })
        right.setSizePolicy(SMINMIN)
        right.hide()
        content_layout.addWidget(right, 0, 4)

        icon_size = self.theme['s.c']['button_icon_size']
        left_flip_config = {
            'icon_r': self.icons['collapse-left'], 'func_r': left.hide,
            'icon_l': self.icons['expand-left'], 'func_l': left.show
        }
        right_flip_config = {
            'icon_r': self.icons['expand-right'], 'func_r': right.show,
            'icon_l': self.icons['collapse-right'], 'func_l': right.hide
        }
        for col, config in ((1, left_flip_config), (3, right_flip_config)):
            flip_button = FlipButton('', '', main_frame)
            flip_button.configure(config)
            flip_button.setIconSize(QSize(icon_size, icon_size))
            flip_button.setStyleSheet(self.get_style_class('QPushButton', 'small_button'))
            flip_button.setSizePolicy(SMAXMAX)
            content_layout.addWidget(flip_button, 0, col, alignment=ATOP)

        center = self.create_frame(main_frame, 'frame')
        center.setSizePolicy(SMINMIN)
        content_layout.addWidget(center, 0, 2)

        main_frame.setLayout(content_layout)
        self.setup_left_sidebar_tabber(left)
        self.setup_main_tabber(center)
        self.setup_overview_frame()
        self.setup_analysis_frame()
        self.setup_league_standings_frame()
        self.setup_settings_frame()

    def setup_left_sidebar_league(self):
        """
        Sets up the league table management tab of the left sidebar
        """
        frame = self.widgets.sidebar_tab_frames[1]
        m = self.theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, 0.5 * m, m)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        map_label = self.create_label('Available Maps:', 'label_heading', frame)
        left_layout.addWidget(map_label)

        background_frame = self.create_frame(frame, 'light_frame', 
                {'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp'}, SMAXMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        map_selector = QListWidget(background_frame)
        map_selector.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        map_selector.setFont(self.theme_font('listbox'))
        map_selector.setSizePolicy(SMAXMIN)
        self.widgets.ladder_map = map_selector
        map_selector.currentTextChanged.connect(lambda new_text: self.update_ladder_index(new_text))
        map_selector.setFixedWidth(self.sidebar_item_width)
        background_layout.addWidget(map_selector)
        left_layout.addWidget(background_frame, stretch=1)

        frame.setLayout(left_layout)


    def setup_left_sidebar_log(self):
        """
        Sets up the log management tab of the left sidebar
        """
        frame = self.widgets.sidebar_tab_frames[0]
        m = self.theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, 0.5 * m, m)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        head_layout = QHBoxLayout()
        head = self.create_label('STO Combatlog:', 'label', frame)
        head_layout.addWidget(head, alignment=ALEFT)
        cut_log_button = self.create_icon_button(self.icons['log-cut'], 'Manage Logfile', parent=frame)
        cut_log_button.clicked.connect(self.split_dialog)
        head_layout.addWidget(cut_log_button, alignment=ARIGHT)
        left_layout.addLayout(head_layout)

        self.entry = QLineEdit(self.settings.value('log_path', ''), frame)
        self.entry.setStyleSheet(self.get_style_class('QLineEdit', 'entry'))
        self.entry.setFont(self.theme_font('entry'))
        self.entry.setFixedWidth(self.sidebar_item_width)
        left_layout.addWidget(self.entry)
        
        entry_button_config = {
            'default': {'margin-bottom': '@isp'},
            'Browse ...': {'callback': lambda: self.browse_log(self.entry), 'align': ALEFT},
            'Scan': {'callback': lambda: self.analyze_log_callback(path=self.entry.text(), parser_num=1), 
                    'align': ARIGHT}
        }
        entry_buttons = self.create_button_series(frame, entry_button_config, 'button')
        left_layout.addLayout(entry_buttons)

        top_button_row = QHBoxLayout()
        top_button_row.setContentsMargins(0, 0, 0, 0)
        top_button_row.setSpacing(0)

        combat_button_layout = QHBoxLayout()
        combat_button_layout.setContentsMargins(0, 0, 0, 0)
        combat_button_layout.setSpacing(m)
        combat_button_layout.setAlignment(ALEFT)
        export_button = self.create_icon_button(self.icons['export-parse'], 'Export Combat', parent=frame)
        combat_button_layout.addWidget(export_button)
        save_button = self.create_icon_button(self.icons['save'], 'Save Combat to Cache', parent=frame)
        combat_button_layout.addWidget(save_button)
        top_button_row.addLayout(combat_button_layout)

        navigation_button_layout = QHBoxLayout()
        navigation_button_layout.setContentsMargins(0, 0, 0, 0)
        navigation_button_layout.setSpacing(m)
        navigation_button_layout.setAlignment(AHCENTER)
        up_button = self.create_icon_button(self.icons['log-up'], 'Load newer Combats', parent=frame)
        up_button.setEnabled(False)
        navigation_button_layout.addWidget(up_button)
        self.widgets.navigate_up_button = up_button
        down_button = self.create_icon_button(self.icons['log-down'], 'Load older Combats', parent=frame)
        down_button.setEnabled(False)
        navigation_button_layout.addWidget(down_button)
        self.widgets.navigate_down_button = down_button
        top_button_row.addLayout(navigation_button_layout)

        parser_button_layout = QHBoxLayout()
        parser_button_layout.setContentsMargins(0, 0, 0, 0)
        parser_button_layout.setSpacing(m)
        parser_button_layout.setAlignment(ARIGHT)
        parser1_button = self.create_icon_button(self.icons['parser-left'], 'Analyze Combat', parent=frame)
        parser_button_layout.addWidget(parser1_button)
        parser2_button = self.create_icon_button(self.icons['parser-right'], 'Analyze Combat', parent=frame)
        parser_button_layout.addWidget(parser2_button)
        top_button_row.addLayout(parser_button_layout)

        left_layout.addLayout(top_button_row)

        background_frame = self.create_frame(frame, 'light_frame', 
                {'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp'}, SMAXMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        self.current_combats = QListWidget(background_frame)
        self.current_combats.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        self.current_combats.setFont(self.theme_font('listbox'))
        self.current_combats.setSizePolicy(SMAXMIN)
        self.current_combats.setFixedWidth(self.sidebar_item_width)
        background_layout.addWidget(self.current_combats)
        left_layout.addWidget(background_frame, stretch=1)
        
        parser1_button.clicked.connect(
                lambda: self.analyze_log_callback(self.current_combats.currentRow(), parser_num=1))
        export_button.clicked.connect(lambda: self.save_combat(self.current_combats.currentRow()))
        up_button.clicked.connect(lambda: self.navigate_log('up'))
        down_button.clicked.connect(lambda: self.navigate_log('down'))

        parser2_button.setEnabled(False)
        save_button.setEnabled(False)

        frame.setLayout(left_layout)

    def setup_left_sidebar_tabber(self, frame: QFrame):
        """
        Sets up the sidebar used to select parses and combats

        Parameters:
        - :param frame: QFrame -> parent frame of the sidebar
        """
        log_frame = self.create_frame(style='medium_frame')
        league_frame = self.create_frame(style='medium_frame')
        sidebar_tabber = QTabWidget(frame)
        sidebar_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        sidebar_tabber.tabBar().setStyleSheet(self.get_style_class( 'QTabBar', 'tabber_tab'))
        sidebar_tabber.setSizePolicy(SMAXMIN)
        sidebar_tabber.addTab(log_frame, 'Log')
        sidebar_tabber.addTab(league_frame, 'League')
        self.widgets.sidebar_tabber = sidebar_tabber
        self.widgets.sidebar_tab_frames.append(log_frame)
        self.widgets.sidebar_tab_frames.append(league_frame)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar_tabber)
        frame.setLayout(layout)

        self.setup_left_sidebar_log()
        self.setup_left_sidebar_league()

    def setup_main_tabber(self, frame:QFrame):
        """
        Sets up the tabber switching between Overview, Analysis, League and Settings.

        Parameters:
        - :param frame: QFrame -> parent frame of the sidebar
        """
        o_frame = self.create_frame()
        a_frame = self.create_frame()
        l_frame = self.create_frame()
        s_frame = self.create_frame()

        main_tabber = QTabWidget(frame)
        main_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        main_tabber.tabBar().setStyleSheet(self.get_style_class( 'QTabBar', 'tabber_tab'))
        main_tabber.setSizePolicy(SMINMIN)
        main_tabber.addTab(o_frame, '&O')
        main_tabber.addTab(a_frame, '&A')
        main_tabber.addTab(l_frame, '&L')
        main_tabber.addTab(s_frame, '&S')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_tabber)
        frame.setLayout(layout)

        self.widgets.main_menu_buttons[0].clicked.connect(lambda: self.switch_main_tab(0))
        self.widgets.main_menu_buttons[1].clicked.connect(lambda: self.switch_main_tab(1))
        self.widgets.main_menu_buttons[2].clicked.connect(lambda: self.switch_main_tab(2))
        self.widgets.main_menu_buttons[2].clicked.connect(lambda: self.establish_league_connection(True))
        self.widgets.main_menu_buttons[3].clicked.connect(lambda: self.switch_main_tab(3))
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
        bar_frame = self.create_frame(None, 'frame')
        dps_graph_frame = self.create_frame(None, 'frame')
        dmg_graph_frame = self.create_frame(None, 'frame')
        self.widgets.overview_tab_frames.append(bar_frame)
        self.widgets.overview_tab_frames.append(dps_graph_frame)
        self.widgets.overview_tab_frames.append(dmg_graph_frame)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        switch_layout = QGridLayout()
        switch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(switch_layout)

        o_tabber = QTabWidget(o_frame)
        o_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        o_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
        o_tabber.addTab(bar_frame, 'BAR')
        o_tabber.addTab(dps_graph_frame, 'DPS')
        o_tabber.addTab(dmg_graph_frame, 'DMG')
        layout.addWidget(o_tabber)

        switch_layout.setColumnStretch(0, 1)
        switch_frame = self.create_frame(o_frame, 'frame')
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 2)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            'DPS Bar': {'callback': lambda state: self.switch_overview_tab(0), 'align': ACENTER, 'toggle': True},
            'DPS Graph': {'callback': lambda state: self.switch_overview_tab(1), 'align': ACENTER, 'toggle': False},
            'Damage Graph': {'callback': lambda state: self.switch_overview_tab(2), 'align': ACENTER, 
                    'toggle': False}
        }
        switcher, buttons = self.create_button_series(switch_frame, switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.overview_menu_buttons = buttons
        icon_layout = QHBoxLayout()
        icon_layout.setContentsMargins(0, 0, self.theme['defaults']['margin'], 0)
        icon_layout.setSpacing(self.theme['defaults']['csp'])
        copy_button = self.create_icon_button(self.icons['copy'], 'Copy Result')
        copy_button.clicked.connect(self.copy_summary_callback)
        icon_layout.addWidget(copy_button)
        ladder_button = self.create_icon_button(self.icons['ladder'], 'Upload Result')
        ladder_button.clicked.connect(self.upload_callback)
        icon_layout.addWidget(ladder_button)
        switch_layout.addLayout(icon_layout, 0, 2, alignment = ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)
        o_frame.setLayout(layout)
        self.widgets.overview_tabber = o_tabber

    def setup_analysis_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        a_frame = self.widgets.main_tab_frames[1]
        dout_frame = self.create_frame(None, 'frame')
        dtaken_frame = self.create_frame(None, 'frame')
        hout_frame = self.create_frame(None, 'frame')
        hin_frame = self.create_frame(None, 'frame')
        self.widgets.analysis_tab_frames.extend((dout_frame, dtaken_frame, hout_frame, hin_frame))
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        switch_layout = QGridLayout()
        switch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(switch_layout)
        
        a_tabber = QTabWidget(a_frame)
        a_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        a_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
        a_tabber.addTab(dout_frame, 'DOUT')
        a_tabber.addTab(dtaken_frame, 'DTAKEN')
        a_tabber.addTab(hout_frame, 'HOUT')
        a_tabber.addTab(hin_frame, 'HIN')
        self.widgets.analysis_tabber = a_tabber
        layout.addWidget(a_tabber)

        switch_layout.setColumnStretch(0, 1)
        switch_frame = self.create_frame(a_frame, 'frame')
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 1)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            'Damage Out': {'callback': lambda state: self.switch_analysis_tab(0), 'align': ACENTER,
                    'toggle': True},
            'Damage Taken': {'callback': lambda state: self.switch_analysis_tab(1), 'align': ACENTER, 
                    'toggle': False},
            'Heals Out': {'callback': lambda state: self.switch_analysis_tab(2), 'align': ACENTER,
                    'toggle': False},
            'Heals In': {'callback': lambda state: self.switch_analysis_tab(3), 'align': ACENTER,
                    'toggle': False}
        }
        switcher, buttons = self.create_button_series(switch_frame, switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.analysis_menu_buttons = buttons
        copy_layout = QHBoxLayout()
        copy_layout.setContentsMargins(0, 0, self.theme['defaults']['margin'], 0)
        copy_layout.setSpacing(self.theme['defaults']['csp'])
        copy_combobox = self.create_combo_box(switch_frame)
        copy_combobox.addItem('Selection')
        copy_layout.addWidget(copy_combobox)
        self.widgets.analysis_copy_combobox = copy_combobox
        copy_button = self.create_icon_button(self.icons['copy'], 'Copy Data')
        copy_button.clicked.connect(self.copy_analysis_callback)
        copy_layout.addWidget(copy_button)
        switch_layout.addLayout(copy_layout, 0, 2, alignment = ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)

        tabs = (
            (dout_frame, 'analysis_table_dout', 'analysis_plot_dout'), 
            (dtaken_frame, 'analysis_table_dtaken', 'analysis_plot_dtaken'),
            (hout_frame, 'analysis_table_hout', 'analysis_plot_hout'),
            (hin_frame, 'analysis_table_hin', 'analysis_plot_hin')
        )
        for tab, table_name, plot_name in tabs:
            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(0)

            # graph
            plot_frame = self.create_frame(tab, 'plot_widget', size_policy=SMINMAX)
            plot_layout = QHBoxLayout()
            plot_layout.setContentsMargins(0, 0, 0, 0)
            plot_layout.setSpacing(self.theme['defaults']['isp'])
            
            plot_bundle_frame = self.create_frame(plot_frame, size_policy=SMINMAX)
            plot_bundle_layout = QVBoxLayout()
            plot_bundle_layout.setContentsMargins(0, 0, 0, 0)
            plot_bundle_layout.setSpacing(0)
            plot_legend_frame = self.create_frame(plot_bundle_frame)
            plot_legend_layout = QHBoxLayout()
            plot_legend_layout.setContentsMargins(0, 0, 0, 0)
            plot_legend_layout.setSpacing(2 * self.theme['defaults']['margin'])
            plot_legend_frame.setLayout(plot_legend_layout)
            plot_widget = AnalysisPlot(self.theme['plot']['color_cycler'], self.theme['defaults']['fg'],
                    self.theme_font('plot_widget'), plot_legend_layout)
            setattr(self.widgets, plot_name, plot_widget)
            plot_widget.setStyleSheet(self.get_style('plot_widget_nullifier'))
            plot_widget.setSizePolicy(SMINMAX)
            plot_bundle_layout.addWidget(plot_widget)
            plot_bundle_layout.addWidget(plot_legend_frame, alignment=AHCENTER)
            plot_bundle_frame.setLayout(plot_bundle_layout)
            plot_layout.addWidget(plot_bundle_frame, stretch=1)

            plot_button_frame = self.create_frame(plot_frame, size_policy=SMAXMIN)
            plot_button_layout = QVBoxLayout()
            plot_button_layout.setContentsMargins(0, 0, 0, 0)
            plot_button_layout.setSpacing(0)
            freeze_button = self.create_button('Freeze Graph', 'toggle_button', plot_button_frame, 
                    style_override={'border-color': '@bg'}, toggle=True)
            freeze_button.clicked.connect(plot_widget.toggle_freeze)
            plot_button_layout.addWidget(freeze_button, alignment=ARIGHT)
            clear_button = self.create_button('Clear Graph', parent=plot_button_frame)
            clear_button.clicked.connect(plot_widget.clear_plot)
            plot_button_layout.addWidget(clear_button, alignment=ARIGHT)
            plot_button_frame.setLayout(plot_button_layout)
            plot_layout.addWidget(plot_button_frame, stretch=0)

            plot_frame.setLayout(plot_layout)  
            tab_layout.addWidget(plot_frame, stretch=3)

            tree = self.create_analysis_table(tab, 'tree_table')
            setattr(self.widgets, table_name, tree)
            tree.clicked.connect(lambda index, pw=plot_widget: self.slot_analysis_graph(index, pw))
            tab_layout.addWidget(tree, stretch=7)
            tab.setLayout(tab_layout)          
        
        a_frame.setLayout(layout)

    def slot_analysis_graph(self, index, plot_widget: AnalysisPlot):
        item = index.internalPointer()
        color = plot_widget.add_bar(item.graph_data)
        if color is None:
            return
        name = item.data[0]
        if isinstance(name, tuple):
            name = ''.join(name)
        legend_item = self.create_legend_item(color, name)
        plot_widget.add_legend_item(legend_item)

    def setup_league_standings_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        l_frame = self.widgets.main_tab_frames[2]
        layout = QVBoxLayout()
        margin = self.theme['defaults']['margin']
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # spacing = self.theme['defaults']['isp']
        # control_frame = self.create_frame(l_frame)
        # control_frame_layout = QHBoxLayout()
        # control_frame_layout.setContentsMargins(margin, margin, margin, margin)
        # control_frame_layout.setSpacing(spacing)

        ladder_table = QTableView(l_frame)
        self.style_table(ladder_table, {'margin': '@margin'})
        self.widgets.ladder_table = ladder_table

        # layout.addWidget(control_frame, alignment=AHCENTER)
        layout.addWidget(ladder_table)
        l_frame.setLayout(layout)

    def create_master_layout(self, parent) -> tuple[QVBoxLayout, QFrame]:
        """
        Creates and returns the master layout for an OSCR window.

        Parameters:
        - :param parent: parent to the layout, usually a window

        :return: populated QVBoxlayout and content frame QFrame
        """
        layout =  QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        bg_frame = self.create_frame(parent, 'frame', {'background': '@oscr'})
        bg_frame.setSizePolicy(SMINMIN)
        layout.addWidget(bg_frame)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        lbl = BannerLabel(get_asset_path('oscrbanner-slim-dark-label.png', self.app_dir), bg_frame)

        main_layout.addWidget(lbl)

        menu_frame = self.create_frame(bg_frame, 'frame', {'background':'@oscr'})
        menu_frame.setSizePolicy(SMAXMAX)
        menu_frame.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(menu_frame)
        menu_button_style = {
            'Overview': {'style':{'margin-left': '@isp'}},
            'Analysis': {},
            'League Standings': {},
            'Settings': {},
        }
        bt_lay, buttons = self.create_button_series(menu_frame, menu_button_style, 
                style='menu_button', seperator='•', ret=True)
        menu_frame.setLayout(bt_lay)
        self.widgets.main_menu_buttons = buttons

        w = self.theme['app']['frame_thickness']
        main_frame = self.create_frame(bg_frame, 'frame', {'margin':(0, w, w, w)})
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

        col_1_frame = self.create_frame(settings_frame)
        col_1_frame.setSizePolicy(SMINMAX)
        settings_layout.addWidget(col_1_frame, alignment=ATOP, stretch=1)
        col_2_frame = self.create_frame(settings_frame)
        col_2_frame.setSizePolicy(SMINMAX)
        settings_layout.addWidget(col_2_frame, alignment=ATOP, stretch=1)
        col_3_frame = self.create_frame(settings_frame)
        col_3_frame.setSizePolicy(SMINMAX)
        settings_layout.addWidget(col_3_frame, alignment=ATOP, stretch=1)

        # first column
        col_1 = QHBoxLayout()
        col_1.setContentsMargins(0, 0, 0, 0)
        col_1.setSpacing(self.theme['defaults']['isp'])
        col_1_1 = QVBoxLayout()
        col_1_1.setSpacing(0)
        dmg_hider_label = self.create_label('Damage table columns:', 'label_subhead')
        col_1_1.addWidget(dmg_hider_label)
        dmg_hider_layout = QVBoxLayout()
        dmg_hider_frame = self.create_frame(col_1_frame, size_policy=SMINMAX, style_override=
                {'border-color':'@lbg', 'border-width':'@bw', 'border-style':'solid', 'border-radius': 2})
        self.set_buttons = list()
        for i, head in enumerate(TREE_HEADER[1:]):
            bt = self.create_button(head, 'toggle_button', dmg_hider_frame, 
                    toggle=self.settings.value(f'dmg_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(lambda state, i=i: self.settings.setValue(f'dmg_columns|{i}', state))
            dmg_hider_layout.addWidget(bt, stretch=1)
        dmg_seperator = self.create_frame(dmg_hider_frame, 'hr', style_override={'background-color': '@lbg'},
                size_policy=SMINMIN)
        dmg_seperator.setFixedHeight(self.theme['defaults']['bw'])
        dmg_hider_layout.addWidget(dmg_seperator)
        apply_button = self.create_button('Apply', 'button', dmg_hider_frame)
        apply_button.clicked.connect(self.update_shown_columns_dmg)
        dmg_hider_layout.addWidget(apply_button, alignment=ARIGHT|ATOP)
        dmg_hider_frame.setLayout(dmg_hider_layout)
        col_1_1.addWidget(dmg_hider_frame, alignment=ATOP)
        col_1.addLayout(col_1_1, stretch=1)

        col_1_2 = QVBoxLayout()
        col_1_2.setSpacing(0)
        heal_hider_label = self.create_label('Heal table columns:', 'label_subhead', col_1_frame)
        col_1_2.addWidget(heal_hider_label)
        heal_hider_layout = QVBoxLayout()
        heal_hider_frame = self.create_frame(col_1_frame, size_policy=SMINMAX, style_override=
                {'border-color':'@lbg', 'border-width':'@bw', 'border-style':'solid', 'border-radius': 2})
        for i, head in enumerate(HEAL_TREE_HEADER[1:]):
            bt = self.create_button(head, 'toggle_button', heal_hider_frame,
                    toggle=self.settings.value(f'heal_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(lambda state, i=i: self.settings.setValue(f'heal_columns|{i}', state))
            heal_hider_layout.addWidget(bt, stretch=1)
        heal_seperator = self.create_frame(dmg_hider_frame, 'hr', style_override={'background-color': '@lbg'},
            size_policy=SMINMIN)
        heal_seperator.setFixedHeight(self.theme['defaults']['bw'])
        heal_hider_layout.addWidget(heal_seperator)
        apply_button_2 = self.create_button('Apply', 'button', heal_hider_frame)
        apply_button_2.clicked.connect(self.update_shown_columns_heal)
        heal_hider_layout.addWidget(apply_button_2, alignment=ARIGHT|ATOP)
        heal_hider_frame.setLayout(heal_hider_layout)
        col_1_2.addWidget(heal_hider_frame, alignment=ATOP)
        col_1.addLayout(col_1_2, stretch=1)

        col_1_frame.setLayout(col_1)

        # second column
        col_2 = QGridLayout()
        col_2.setContentsMargins(0, 0, 0, 0)
        col_2.setVerticalSpacing(self.theme['defaults']['isp'])
        col_2.setHorizontalSpacing(self.theme['defaults']['csp'])
        combat_delta_label = self.create_label('Seconds Between Combats:', 'label_subhead')
        col_2.addWidget(combat_delta_label, 0, 0, alignment=ARIGHT)
        combat_delta_validator = QIntValidator()
        combat_delta_validator.setBottom(1)
        combat_delta_entry = self.create_entry(self.settings.value('seconds_between_combats', type=str), 
                combat_delta_validator, style_override={'margin-top': 0})
        combat_delta_entry.editingFinished.connect(lambda: self.settings.setValue('seconds_between_combats', 
                combat_delta_entry.text()))
        col_2.addWidget(combat_delta_entry, 0, 1, alignment=ALEFT)
        combat_num_label = self.create_label('Number of combats to isolate:', 'label_subhead')
        col_2.addWidget(combat_num_label, 1, 0, alignment=ARIGHT)
        combat_num_validator = QIntValidator()
        combat_num_validator.setBottom(1)
        combat_num_entry = self.create_entry(self.settings.value('combats_to_parse', type=str),
                combat_num_validator, style_override={'margin-top': 0})
        combat_num_entry.editingFinished.connect(lambda: self.settings.setValue('combats_to_parse', 
                combat_num_entry.text()))
        col_2.addWidget(combat_num_entry, 1, 1, alignment=ALEFT)
        graph_resolution_label = self.create_label('Graph resolution (data points per second):', 
                'label_subhead')
        col_2.addWidget(graph_resolution_label, 2, 0, alignment=ARIGHT)
        graph_resolution_validator = QIntValidator(1, 5)
        default_graph_resolution = str(int(round(1 / self.settings.value('graph_resolution', type=float), 0)))
        graph_resolution_entry = self.create_entry(default_graph_resolution, graph_resolution_validator, 
                style_override={'margin-top': 0})
        graph_resolution_entry.editingFinished.connect(lambda: self.settings.setValue('graph_resolution', 
                round(1 / int(graph_resolution_entry.text()), 1)))
        col_2.addWidget(graph_resolution_entry, 2, 1, alignment=ALEFT)
        split_length_label = self.create_label('Auto Split After Lines:', 'label_subhead')
        col_2.addWidget(split_length_label, 3, 0, alignment=ARIGHT)
        split_length_validator = QIntValidator()
        split_length_validator.setBottom(1)
        split_length_entry = self.create_entry(self.settings.value('split_log_after', type=str),
                split_length_validator, style_override={'margin-top': 0})
        split_length_entry.editingFinished.connect(lambda: self.settings.setValue('split_log_after', 
                split_length_entry.text()))
        col_2.addWidget(split_length_entry, 3, 1, alignment=ALEFT)
        
        col_2_frame.setLayout(col_2)

        settings_frame.setLayout(settings_layout)

    def browse_log(self, entry:QLineEdit):
        """
        Callback for browse button.

        Parameters:
        - :param entry: QLineEdit -> path entry line widget
        """
        current_path = entry.text()
        if current_path != '':
            path = self.browse_path(os.path.dirname(current_path), 'Logfile (*.log);;Any File (*.*)')
            if path != '':
                entry.setText(format_path(path))

    def save_combat(self, combat_num: int):
        """
        Callback for save button.

        Parameters:
        - :param combat_num: number of combat in self.combats
        """
        if not self.parser1.active_combat:
            return
        base_dir = os.path.dirname(self.entry.text())
        if not base_dir:
            base_dir = self.app_dir
        path = self.browse_path(base_dir, 'Logfile (*.log);;Any File (*.*)', save=True)
        if path:
            self.parser1.export_combat(combat_num, path)

    def navigate_log(self, direction: str):
        """
        Load older or newer combats.

        Parameters:
        - :param direction: "up" -> load newer combats; "down" -> load older combats
        """
        logfile_changed = self.parser1.navigate_log(direction)
        selected_row = self.current_combats.currentRow()
        self.current_combats.clear()
        self.current_combats.addItems(self.parser1.analyzed_combats)
        if logfile_changed:
            self.current_combats.setCurrentRow(0)
            self.current_combat_id = None
            self.analyze_log_callback(0, parser_num=1)
        else:
            self.current_combats.setCurrentRow(selected_row)
        self.widgets.navigate_up_button.setEnabled(self.parser1.navigation_up)
        self.widgets.navigate_down_button.setEnabled(self.parser1.navigation_down)

    def switch_analysis_tab(self, tab_index: int):
        """
        Callback for tab switch buttons; switches tab and sets active button.

        Parameters:
        - :param tab_index: index of the tab to switch to
        """
        self.widgets.analysis_tabber.setCurrentIndex(tab_index)
        for index, button in enumerate(self.widgets.analysis_menu_buttons):
            if not index == tab_index:
                button.setChecked(False)
            else:
                button.setChecked(True)
    
    def switch_overview_tab(self, tab_index: int):
        """
        Callback for tab switch buttons; switches tab and sets active button.

        Parameters:
        - :param tab_index: index of the tab to switch to
        """
        self.widgets.overview_tabber.setCurrentIndex(tab_index)
        for index, button in enumerate(self.widgets.overview_menu_buttons):
            if not index == tab_index:
                button.setChecked(False)
            else:
                button.setChecked(True)

    def switch_main_tab(self, tab_index: int):
        """
        Callback for main tab switch buttons. Switches main and sidebar tabs.

        Parameters:
        - :param tab_index: index of the tab to switch to
        """
        SIDEBAR_TAB_CONVERSION = {
            0: 0,
            1: 0,
            2: 1,
            3: 0
        }
        self.widgets.main_tabber.setCurrentIndex(tab_index)
        self.widgets.sidebar_tabber.setCurrentIndex(SIDEBAR_TAB_CONVERSION[tab_index])

    def set_variable(self, var_to_be_set, index, value):
        """
        Assigns value at index to variable
        """
        var_to_be_set[index] = value
