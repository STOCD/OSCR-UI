import os

from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QFrame, QListWidget, QScrollArea
from PySide6.QtWidgets import QSpacerItem, QTabWidget, QTableView
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import QSize, QSettings, QTimer
from PySide6.QtGui import QFontDatabase, QIntValidator

from OSCR import HEAL_TREE_HEADER, LIVE_TABLE_HEADER, TABLE_HEADER, TREE_HEADER

from .leagueconnector import OSCRClient
from .iofunctions import get_asset_path, load_icon_series, load_icon, open_link, reset_temp_folder
from .textedit import format_path
from .widgets import AnalysisPlot, BannerLabel, FlipButton, WidgetStorage
from .widgetbuilder import ABOTTOM, ACENTER, AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER
from .widgetbuilder import SEXPAND, SMAXMAX, SMAXMIN, SMIN, SMINMAX, SMINMIN, SMIXMAX, SMIXMIN
from .widgetbuilder import SCROLLOFF, SCROLLON, SMPIXEL

# only for developing; allows to terminate the qt event loop with keyboard interrupt
from signal import signal, SIGINT, SIG_DFL
signal(SIGINT, SIG_DFL)


class OSCRUI():

    from .callbacks import (
            browse_log, browse_sto_logpath, collapse_overview_table, expand_overview_table,
            favorite_button_callback, navigate_log, save_combat, set_live_scale_setting,
            set_parser_opacity_setting, set_graph_resolution_setting, set_sto_logpath_setting,
            set_ui_scale_setting, switch_analysis_tab, switch_main_tab, switch_map_tab,
            switch_overview_tab)
    from .datafunctions import analyze_log_callback, copy_analysis_callback
    from .datafunctions import copy_summary_callback, init_parser, update_shown_columns_dmg
    from .datafunctions import update_shown_columns_heal
    from .displayer import create_legend_item
    from .iofunctions import browse_path
    from .style import get_style_class, create_style_sheet, theme_font, get_style
    from .subwindows import live_parser_toggle, split_dialog
    from .widgetbuilder import create_analysis_table, create_annotated_slider, create_button
    from .widgetbuilder import create_button_series, create_combo_box, create_entry, create_frame
    from .widgetbuilder import create_icon_button, create_label, style_table
    from .leagueconnector import apply_league_table_filter, download_and_view_combat
    from .leagueconnector import establish_league_connection, extend_ladder, slot_ladder
    from .leagueconnector import upload_callback

    app_dir = None

    versions = ('', '')  # (release version, dev version)

    config = {}  # see main.py for contents

    settings: QSettings  # see main.py for defaults

    # stores widgets that need to be accessed from outside their creating function
    widgets: WidgetStorage

    league_api: OSCRClient

    def __init__(self, theme, args, path, config, versions) -> None:
        """
        Creates new Instance of OSCR.

        Parameters:
        - :param version: version of the app
        - :param theme: dict -> default theme
        - :param args: command line arguments
        - :param path: absolute path to main.py file
        - :param config: app configuration (!= settings these are not changed by the user)
        """
        self.versions = versions
        self.theme = theme
        self.args = args
        self.app_dir = path
        self.config = config
        self.widgets = WidgetStorage()
        self.league_api = None
        self.live_parser_window = None
        self.live_parser = None
        self.init_settings()
        self.init_config()
        self.app, self.window = self.create_main_window()
        self.init_parser()
        self.cache_assets()
        self.setup_main_layout()
        self.window.show()
        if self.settings.value('auto_scan', type=bool):
            QTimer.singleShot(
                    100,
                    lambda: self.analyze_log_callback(path=self.entry.text(), parser_num=1)
            )

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
            'page-up': 'page-up.svg',
            'page-down': 'page-down.svg',
            'edit': 'edit.svg',
            'parser-left': 'parser-left-3.svg',
            'parser-right': 'parser-right-3.svg',
            'export-parse': 'export.svg',
            'copy': 'copy.svg',
            'ladder': 'ladder.svg',
            'star': 'star.svg',
            'stocd': 'section31badge.png',
            'stobuilds': 'stobuildslogo.png',
            'close': 'close.svg',
            'expand-top': 'expand-top.svg',
            'collapse-top': 'collapse-top.svg',
            'expand-bottom': 'expand-bottom.svg',
            'collapse-bottom': 'collapse-bottom.svg',
            'check': 'check.svg',
            'dash': 'dash.svg'
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
        self.config['ui_scale'] = self.settings.value('ui_scale', type=float)
        self.config['live_scale'] = self.settings.value('live_scale', type=float)
        self.config['icon_size'] = round(
                self.config['ui_scale'] * self.theme['s.c']['button_icon_size'])

    @property
    def parser_settings(self) -> dict:
        """
        Returns settings relevant to the parser
        """
        relevant_settings = (
                ('combats_to_parse', int), ('seconds_between_combats', int),
                ('excluded_event_ids', list), ('graph_resolution', float))
        settings = dict()
        for setting_key, settings_type in relevant_settings:
            setting = self.settings.value(setting_key, type=settings_type, defaultValue='')
            if setting:
                settings[setting_key] = setting
        return settings

    @property
    def live_parser_settings(self) -> dict:
        """
        Returns settings relevant to the LiveParser
        """
        return {'seconds_between_combats': self.settings.value('seconds_between_combats', type=int)}

    @property
    def sidebar_item_width(self) -> int:
        """
        Width of the sidebar.
        """
        return int(
                self.theme['s.c']['sidebar_item_width']
                * self.window.width()
                * self.config['ui_scale'])

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
        self.widgets.sidebar_tabber.setFixedWidth(self.sidebar_item_width)
        event.accept()

    # ----------------------------------------------------------------------------------------------
    # GUI functions below
    # ----------------------------------------------------------------------------------------------

    def create_main_window(self, argv=[]) -> tuple[QApplication, QWidget]:
        """
        Creates and initializes main window.

        :return: QApplication, QWidget
        """
        app = QApplication(argv)
        font_database = QFontDatabase()
        font_database.addApplicationFont(get_asset_path('Overpass-Bold.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('Overpass-Medium.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('Overpass-Regular.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('RobotoMono-Regular.ttf', self.app_dir))
        font_database.addApplicationFont(get_asset_path('RobotoMono-Medium.ttf', self.app_dir))
        app.setStyleSheet(self.create_style_sheet(self.theme['app']['style']))
        window = QWidget()
        window.setMinimumSize(
                self.config['ui_scale'] * self.config['minimum_window_width'],
                self.config['ui_scale'] * self.config['minimum_window_height'])
        window.setWindowIcon(load_icon('oscr_icon_small.png', self.app_dir))
        window.setWindowTitle('Open Source Combatlog Reader')
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

        right = self.create_frame(main_frame, 'frame', style_override={
                'border-left-style': 'solid', 'border-left-width': '@sep',
                'border-left-color': '@oscr'})
        right.setSizePolicy(SMINMIN)
        right.hide()
        content_layout.addWidget(right, 0, 4)

        csp = self.theme['defaults']['csp']
        col_1 = QVBoxLayout()
        col_1.setContentsMargins(csp, csp, csp, csp)
        content_layout.addLayout(col_1, 0, 1)
        col_3 = QVBoxLayout()
        col_3.setContentsMargins(csp, csp, csp, csp)
        content_layout.addLayout(col_3, 0, 3)
        icon_size = self.config['icon_size']
        left_flip_config = {
            'icon_r': self.icons['collapse-left'], 'func_r': left.hide,
            'icon_l': self.icons['expand-left'], 'func_l': left.show,
            'tooltip_r': 'Collapse Sidebar', 'tooltip_l': 'Expand Sidebar'
        }
        right_flip_config = {
            'icon_r': self.icons['expand-right'], 'func_r': right.show,
            'icon_l': self.icons['collapse-right'], 'func_l': right.hide,
            'tooltip_r': 'Expand', 'tooltip_l': 'Collapse'
        }
        for col, config in ((col_1, left_flip_config), (col_3, right_flip_config)):
            flip_button = FlipButton('', '', main_frame)
            flip_button.configure(config)
            flip_button.setIconSize(QSize(icon_size, icon_size))
            flip_button.setStyleSheet(self.get_style_class('QPushButton', 'small_button'))
            flip_button.setSizePolicy(SMAXMAX)
            col.addWidget(flip_button, alignment=ATOP)

        table_flip_config = {
            'icon_r': self.icons['collapse-bottom'], 'tooltip_r': 'Collapse Table',
            'func_r': self.collapse_overview_table,
            'icon_l': self.icons['expand-bottom'], 'tooltip_l': 'Expand_Table',
            'func_l': self.expand_overview_table
        }
        table_button = FlipButton('', '', main_frame)
        table_button.configure(table_flip_config)
        table_button.setIconSize(QSize(icon_size, icon_size))
        table_button.setStyleSheet(self.get_style_class('QPushButton', 'small_button'))
        table_button.setSizePolicy(SMAXMAX)
        col_1.addWidget(table_button, alignment=ABOTTOM)
        self.widgets.overview_table_button = table_button

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
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        map_label = self.create_label('Available Maps:', 'label_heading', frame)
        left_layout.addWidget(map_label)

        map_switch_layout = QGridLayout()
        map_switch_layout.setContentsMargins(0, 0, 0, 0)
        map_switch_layout.setSpacing(0)
        map_switch_layout.setColumnStretch(0, 1)
        map_switch_layout.setColumnStretch(1, 3)
        map_switch_layout.setColumnStretch(2, 1)
        map_switch_buttons_frame = self.create_frame(frame, 'medium_frame')
        map_switch_layout.addWidget(map_switch_buttons_frame, 0, 1, alignment=ACENTER)
        map_switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            'All Maps': {
                'callback': lambda: self.switch_map_tab(0), 'align': ACENTER, 'toggle': True},
            'Favorites': {
                'callback': lambda: self.switch_map_tab(1), 'align': ACENTER, 'toggle': False},
        }
        map_switcher, map_buttons = self.create_button_series(
                map_switch_buttons_frame, map_switch_style, 'tab_button', ret=True)
        for button in map_buttons:
            button.setSizePolicy(SMAXMIN)
        map_switcher.setContentsMargins(0, 0, 0, 0)
        map_switch_buttons_frame.setLayout(map_switcher)
        self.widgets.map_menu_buttons = map_buttons
        favorite_button = self.create_icon_button(self.icons['star'], 'Add to Favorites')
        favorite_button.clicked.connect(self.favorite_button_callback)
        map_switch_layout.addWidget(favorite_button, 0, 2, ARIGHT)
        left_layout.addLayout(map_switch_layout)

        all_frame = self.create_frame(style='medium_frame', size_policy=SMINMIN)
        favorites_frame = self.create_frame(style='medium_frame', size_policy=SMINMIN)
        maps_tabber = QTabWidget(frame)
        maps_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        maps_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
        maps_tabber.setSizePolicy(SMINMIN)
        maps_tabber.addTab(all_frame, 'All Maps')
        maps_tabber.addTab(favorites_frame, 'Favorites')
        self.widgets.map_tabber = maps_tabber
        self.widgets.map_tab_frames.append(all_frame)
        self.widgets.map_tab_frames.append(favorites_frame)
        left_layout.addWidget(maps_tabber, stretch=1)

        all_layout = QVBoxLayout()
        all_layout.setContentsMargins(0, 0, 0, 0)
        all_layout.setSpacing(0)
        background_frame = self.create_frame(all_frame, 'light_frame', style_override={
                'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp'},
                size_policy=SMINMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        map_selector = QListWidget(background_frame)
        map_selector.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        map_selector.setFont(self.theme_font('listbox'))
        map_selector.setSizePolicy(SMIXMIN)
        self.widgets.ladder_selector = map_selector
        map_selector.itemClicked.connect(lambda clicked_item: self.slot_ladder(clicked_item.text()))
        background_layout.addWidget(map_selector)
        all_layout.addWidget(background_frame, stretch=1)
        all_frame.setLayout(all_layout)

        favorites_layout = QVBoxLayout()
        favorites_layout.setContentsMargins(0, 0, 0, 0)
        favorites_layout.setSpacing(0)
        background_frame = self.create_frame(favorites_frame, 'light_frame', style_override={
                'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp'},
                size_policy=SMINMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        favorite_selector = QListWidget(background_frame)
        favorite_selector.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        favorite_selector.setFont(self.theme_font('listbox'))
        favorite_selector.setSizePolicy(SMIXMIN)
        self.widgets.favorite_ladder_selector = favorite_selector
        favorite_selector.addItems(self.settings.value('favorite_ladders', type=list))
        favorite_selector.itemClicked.connect(
                lambda clicked_item: self.slot_ladder(clicked_item.text()))
        background_layout.addWidget(favorite_selector)
        favorites_layout.addWidget(background_frame, stretch=1)
        favorites_frame.setLayout(favorites_layout)

        map_label = self.create_label(
                'Seasonal Records:', 'label_heading', frame, {'margin-top': '@isp'})
        left_layout.addWidget(map_label)

        background_frame = self.create_frame(all_frame, 'light_frame', style_override={
                'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp'},
                size_policy=SMINMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        season_selector = QListWidget(background_frame)
        season_selector.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        season_selector.setFont(self.theme_font('listbox'))
        season_selector.setSizePolicy(SMIXMIN)
        self.widgets.season_ladder_selector = season_selector
        season_selector.currentTextChanged.connect(
                lambda new_text: self.slot_ladder(new_text))
        background_layout.addWidget(season_selector)
        left_layout.addWidget(background_frame, stretch=1)

        frame.setLayout(left_layout)

    def setup_left_sidebar_log(self):
        """
        Sets up the log management tab of the left sidebar
        """
        frame = self.widgets.sidebar_tab_frames[0]
        m = self.theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        head_layout = QHBoxLayout()
        head = self.create_label('STO Combatlog:', 'label_heading', frame)
        head_layout.addWidget(head, alignment=ALEFT | ABOTTOM)
        cut_log_button = self.create_icon_button(
                self.icons['edit'], 'Manage Logfile', parent=frame)
        cut_log_button.clicked.connect(self.split_dialog)
        head_layout.addWidget(cut_log_button, alignment=ARIGHT)
        left_layout.addLayout(head_layout)

        self.entry = QLineEdit(self.settings.value('log_path', ''), frame)
        self.entry.setStyleSheet(self.get_style_class('QLineEdit', 'entry'))
        self.entry.setFont(self.theme_font('entry'))
        self.entry.setSizePolicy(SMIXMAX)
        left_layout.addWidget(self.entry)

        entry_button_config = {
            'default': {'margin-bottom': '@isp'},
            'Browse ...': {'callback': lambda: self.browse_log(self.entry), 'align': ALEFT},
            'Default': {
                'callback': lambda: self.entry.setText(self.settings.value('sto_log_path')),
                'align': AHCENTER
            },
            'Scan': {'callback': lambda: self.analyze_log_callback(
                    path=self.entry.text(), parser_num=1), 'align': ARIGHT}
        }
        entry_buttons = self.create_button_series(frame, entry_button_config, 'button')
        left_layout.addLayout(entry_buttons)

        top_button_row = QHBoxLayout()
        top_button_row.setContentsMargins(0, 0, 0, 0)
        top_button_row.setSpacing(m)

        combat_button_layout = QHBoxLayout()
        combat_button_layout.setContentsMargins(0, 0, 0, 0)
        combat_button_layout.setSpacing(m)
        combat_button_layout.setAlignment(ALEFT)
        export_button = self.create_icon_button(
                self.icons['export-parse'], 'Export Combat', parent=frame)
        combat_button_layout.addWidget(export_button)
        save_button = self.create_icon_button(
                self.icons['save'], 'Save Combat to Cache', parent=frame)
        combat_button_layout.addWidget(save_button)
        top_button_row.addLayout(combat_button_layout)

        navigation_button_layout = QHBoxLayout()
        navigation_button_layout.setContentsMargins(0, 0, 0, 0)
        navigation_button_layout.setSpacing(m)
        navigation_button_layout.setAlignment(AHCENTER)
        up_button = self.create_icon_button(
                self.icons['page-up'], 'Load newer Combats', parent=frame)
        up_button.setEnabled(False)
        navigation_button_layout.addWidget(up_button)
        self.widgets.navigate_up_button = up_button
        down_button = self.create_icon_button(
                self.icons['page-down'], 'Load older Combats', parent=frame)
        down_button.setEnabled(False)
        navigation_button_layout.addWidget(down_button)
        self.widgets.navigate_down_button = down_button
        top_button_row.addLayout(navigation_button_layout)

        parser_button_layout = QHBoxLayout()
        parser_button_layout.setContentsMargins(0, 0, 0, 0)
        parser_button_layout.setSpacing(m)
        parser_button_layout.setAlignment(ARIGHT)
        parser1_button = self.create_icon_button(
                self.icons['parser-left'], 'Analyze Combat', parent=frame)
        parser_button_layout.addWidget(parser1_button)
        parser2_button = self.create_icon_button(
                self.icons['parser-right'], 'Analyze Combat', parent=frame)
        parser_button_layout.addWidget(parser2_button)
        top_button_row.addLayout(parser_button_layout)

        left_layout.addLayout(top_button_row)

        background_frame = self.create_frame(frame, 'light_frame', style_override={
                'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp'},
                size_policy=SMINMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        self.current_combats = QListWidget(background_frame)
        self.current_combats.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        self.current_combats.setFont(self.theme_font('listbox'))
        self.current_combats.setSizePolicy(SMIXMIN)
        background_layout.addWidget(self.current_combats)
        left_layout.addWidget(background_frame, stretch=1)

        parser1_button.clicked.connect(
                lambda: self.analyze_log_callback(self.current_combats.currentRow(), parser_num=1))
        export_button.clicked.connect(lambda: self.save_combat(self.current_combats.currentRow()))
        up_button.clicked.connect(lambda: self.navigate_log('up'))
        down_button.clicked.connect(lambda: self.navigate_log('down'))

        parser2_button.setEnabled(False)
        save_button.setEnabled(False)

        live_parser_button = self.create_button(
                'Live Parser', 'tab_button', style_override={'margin-top': '@isp'}, toggle=False)
        live_parser_button.clicked[bool].connect(self.live_parser_toggle)
        left_layout.addWidget(live_parser_button, alignment=AHCENTER)
        self.widgets.live_parser_button = live_parser_button

        frame.setLayout(left_layout)

    def setup_left_sidebar_about(self):
        """
        Sets up the about tab of the left sidebar
        """
        frame = self.widgets.sidebar_tab_frames[2]
        m = self.theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        head_label = self.create_label('About OSCR:', 'label_heading')
        left_layout.addWidget(head_label)
        about_label = self.create_label(
                'Open Source Combatlog Reader (OSCR), developed by the STO Community '
                'Developers in cooperation with the STO Builds Discord.')
        about_label.setWordWrap(True)
        left_layout.addWidget(about_label)
        version_label = self.create_label(
                f'Current Version: {self.versions[0]} ({self.versions[1]})', 'label_subhead',
                style_override={'margin-bottom': '@isp'})
        left_layout.addWidget(version_label)
        link_button_style = {
            'default': {},
            'Website': {'callback': lambda: open_link(self.config['link_website'])},
            'Github': {'callback': lambda: open_link(self.config['link_github'])},
            'Downloads': {
                'callback': lambda: open_link(self.config['link_downloads'])}
        }
        button_layout, buttons = self.create_button_series(
                frame, link_button_style, 'button', seperator='•', ret=True)
        buttons[0].setToolTip(self.config['link_website'])
        buttons[1].setToolTip(self.config['link_github'])
        buttons[2].setToolTip(self.config['link_downloads'])
        left_layout.addLayout(button_layout)
        left_layout.addSpacerItem(QSpacerItem(1, 1, hData=SMIN, vData=SEXPAND))
        logo_layout = QGridLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setColumnStretch(1, 1)
        logo_size = [self.config['icon_size'] * 4] * 2
        stocd_logo = self.create_icon_button(
                self.icons['stocd'], self.config['link_stocd'],
                style_override={'border-style': 'none'}, icon_size=logo_size)
        stocd_logo.clicked.connect(lambda: open_link(self.config['link_stocd']))
        logo_layout.addWidget(stocd_logo, 0, 0)
        left_layout.addLayout(logo_layout)
        stobuilds_logo = self.create_icon_button(
                self.icons['stobuilds'], self.config['link_stobuilds'],
                style_override={'border-style': 'none'}, icon_size=logo_size)
        stobuilds_logo.clicked.connect(lambda: open_link(self.config['link_stobuilds']))
        logo_layout.addWidget(stobuilds_logo, 0, 2)
        frame.setLayout(left_layout)

    def setup_left_sidebar_tabber(self, frame: QFrame):
        """
        Sets up the sidebar used to select parses and combats

        Parameters:
        - :param frame: QFrame -> parent frame of the sidebar
        """
        log_frame = self.create_frame(style='medium_frame', size_policy=SMINMIN)
        league_frame = self.create_frame(style='medium_frame', size_policy=SMINMIN)
        about_frame = self.create_frame(style='medium_frame', size_policy=SMINMIN)
        sidebar_tabber = QTabWidget(frame)
        sidebar_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        sidebar_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
        sidebar_tabber.setSizePolicy(SMAXMIN)
        sidebar_tabber.addTab(log_frame, 'Log')
        sidebar_tabber.addTab(league_frame, 'League')
        sidebar_tabber.addTab(about_frame, 'About')
        self.widgets.sidebar_tabber = sidebar_tabber
        self.widgets.sidebar_tab_frames.append(log_frame)
        self.widgets.sidebar_tab_frames.append(league_frame)
        self.widgets.sidebar_tab_frames.append(about_frame)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar_tabber)
        frame.setLayout(layout)

        self.setup_left_sidebar_log()
        self.setup_left_sidebar_league()
        self.setup_left_sidebar_about()

    def setup_main_tabber(self, frame: QFrame):
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
        main_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
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
        self.widgets.main_menu_buttons[2].clicked.connect(self.establish_league_connection)
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
        bar_frame = self.create_frame()
        dps_graph_frame = self.create_frame()
        dmg_graph_frame = self.create_frame()
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
        layout.addWidget(o_tabber, stretch=self.theme['s.c']['overview_graph_stretch'])

        switch_layout.setColumnStretch(0, 1)
        switch_frame = self.create_frame(o_frame, 'frame')
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 2)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            'DPS Bar': {
                'callback': lambda: self.switch_overview_tab(0), 'align': ACENTER, 'toggle': True},
            'DPS Graph': {
                'callback': lambda: self.switch_overview_tab(1), 'align': ACENTER, 'toggle': False},
            'Damage Graph': {
                'callback': lambda: self.switch_overview_tab(2), 'align': ACENTER, 'toggle': False}
        }
        switcher, buttons = self.create_button_series(
                switch_frame, switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.overview_menu_buttons = buttons
        icon_layout = QHBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(self.theme['defaults']['csp'])
        copy_button = self.create_icon_button(self.icons['copy'], 'Copy Result')
        copy_button.clicked.connect(self.copy_summary_callback)
        icon_layout.addWidget(copy_button)
        ladder_button = self.create_icon_button(self.icons['ladder'], 'Upload Result')
        ladder_button.clicked.connect(self.upload_callback)
        icon_layout.addWidget(ladder_button)
        switch_layout.addLayout(icon_layout, 0, 2, alignment=ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)
        table_frame = self.create_frame(size_policy=SMINMIN)
        layout.addWidget(table_frame, stretch=self.theme['s.c']['overview_table_stretch'])
        self.widgets.overview_table_frame = table_frame
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
            'Damage Out': {
                'callback': lambda state: self.switch_analysis_tab(0), 'align': ACENTER,
                'toggle': True},
            'Damage Taken': {
                'callback': lambda state: self.switch_analysis_tab(1),
                'align': ACENTER, 'toggle': False},
            'Heals Out': {
                'callback': lambda state: self.switch_analysis_tab(2), 'align': ACENTER,
                'toggle': False},
            'Heals In': {
                'callback': lambda state: self.switch_analysis_tab(3), 'align': ACENTER,
                'toggle': False}
        }
        switcher, buttons = self.create_button_series(
                switch_frame, switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.analysis_menu_buttons = buttons
        copy_layout = QHBoxLayout()
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(self.theme['defaults']['csp'])
        copy_combobox = self.create_combo_box(switch_frame)
        copy_combobox.addItems(
                ('Selection', 'Global Max One Hit', 'Max One Hit', 'Magnitude', 'Magnitude / s'))
        copy_layout.addWidget(copy_combobox)
        self.widgets.analysis_copy_combobox = copy_combobox
        copy_button = self.create_icon_button(self.icons['copy'], 'Copy Data')
        copy_button.clicked.connect(self.copy_analysis_callback)
        copy_layout.addWidget(copy_button)
        switch_layout.addLayout(copy_layout, 0, 2, alignment=ARIGHT | ABOTTOM)
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
            plot_widget = AnalysisPlot(
                    self.theme['plot']['color_cycler'], self.theme['defaults']['fg'],
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
            freeze_button = self.create_button(
                    'Freeze Graph', 'toggle_button', plot_button_frame,
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
        color = plot_widget.add_bar(item)
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        ladder_table = QTableView(l_frame)
        self.style_table(ladder_table, {'margin-top': '@isp'}, single_row_selection=True)
        self.widgets.ladder_table = ladder_table
        layout.addWidget(ladder_table, stretch=1)

        control_layout = QGridLayout()
        m = self.theme['defaults']['margin']
        control_layout.setContentsMargins(m, 0, m, m)
        control_layout.setSpacing(0)
        control_layout.setColumnStretch(2, 1)
        search_label = self.create_label(
                'Search:', 'label_subhead', style_override={'margin-bottom': 0})
        control_layout.addWidget(search_label, 0, 0, alignment=AVCENTER)
        search_bar = self.create_entry(
                placeholder='name@handle', style_override={'margin-left': '@isp', 'margin-top': 0})
        search_bar.textChanged.connect(lambda text: self.apply_league_table_filter(text))
        control_layout.addWidget(search_bar, 0, 1, alignment=AVCENTER)
        control_button_style = {
            'View Parse': {'callback': self.download_and_view_combat},
            'More': {'callback': self.extend_ladder, 'style': {'margin-right': 0}}
        }
        control_button_layout = self.create_button_series(
                l_frame, control_button_style, 'button', seperator='•')
        control_layout.addLayout(control_button_layout, 0, 3, alignment=AVCENTER)
        layout.addLayout(control_layout)

        l_frame.setLayout(layout)

    def create_master_layout(self, parent) -> tuple[QVBoxLayout, QFrame]:
        """
        Creates and returns the master layout for an OSCR window.

        Parameters:
        - :param parent: parent to the layout, usually a window

        :return: populated QVBoxlayout and content frame QFrame
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        bg_frame = self.create_frame(parent, 'frame', {'background': '@oscr'})
        bg_frame.setSizePolicy(SMINMIN)
        layout.addWidget(bg_frame)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        lbl = BannerLabel(get_asset_path('oscrbanner-slim-dark-label.png', self.app_dir), bg_frame)

        main_layout.addWidget(lbl)

        menu_frame = self.create_frame(bg_frame, 'frame', {'background': '@oscr'})
        menu_frame.setSizePolicy(SMAXMAX)
        menu_frame.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(menu_frame)
        menu_button_style = {
            'Overview': {'style': {'margin-left': '@isp'}},
            'Analysis': {},
            'League Standings': {},
            'Settings': {},
        }
        bt_lay, buttons = self.create_button_series(
                menu_frame, menu_button_style, style='menu_button', seperator='•', ret=True)
        menu_frame.setLayout(bt_lay)
        self.widgets.main_menu_buttons = buttons

        w = self.theme['app']['frame_thickness']
        main_frame = self.create_frame(bg_frame, 'frame', {'margin': (0, w, w, w)})
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
        scroll_frame = self.create_frame()
        scroll_area = QScrollArea()
        scroll_area.setSizePolicy(SMINMIN)
        scroll_area.setHorizontalScrollBarPolicy(SCROLLOFF)
        scroll_area.setVerticalScrollBarPolicy(SCROLLON)
        scroll_area.setAlignment(AHCENTER)
        settings_layout.addWidget(scroll_area)
        settings_frame.setLayout(settings_layout)
        col_1_frame = None  # TODO remove parent parameter from self.create_... functions
        col_2_frame = None

        # first section
        sec_1 = QGridLayout()
        sec_1.setContentsMargins(0, 0, 0, 0)
        sec_1.setVerticalSpacing(self.theme['defaults']['isp'])
        sec_1.setHorizontalSpacing(self.theme['defaults']['csp'])
        combat_delta_label = self.create_label('Seconds Between Combats:', 'label_subhead')
        sec_1.addWidget(combat_delta_label, 0, 0, alignment=ARIGHT)
        combat_delta_validator = QIntValidator()
        combat_delta_validator.setBottom(1)
        combat_delta_entry = self.create_entry(
                self.settings.value('seconds_between_combats', type=str),
                combat_delta_validator, style_override={'margin-top': 0})
        combat_delta_entry.setSizePolicy(SMIXMAX)
        combat_delta_entry.editingFinished.connect(lambda: self.settings.setValue(
                'seconds_between_combats', combat_delta_entry.text()))
        sec_1.addWidget(combat_delta_entry, 0, 1, alignment=AVCENTER)
        combat_num_label = self.create_label('Number of combats to isolate:', 'label_subhead')
        sec_1.addWidget(combat_num_label, 1, 0, alignment=ARIGHT)
        combat_num_validator = QIntValidator()
        combat_num_validator.setBottom(1)
        combat_num_entry = self.create_entry(
                self.settings.value('combats_to_parse', type=str), combat_num_validator,
                style_override={'margin-top': 0})
        combat_num_entry.setSizePolicy(SMIXMAX)
        combat_num_entry.editingFinished.connect(lambda: self.settings.setValue(
                'combats_to_parse', combat_num_entry.text()))
        sec_1.addWidget(combat_num_entry, 1, 1, alignment=AVCENTER)
        graph_resolution_label = self.create_label(
                'Graph resolution (interval in seconds):', 'label_subhead')
        sec_1.addWidget(graph_resolution_label, 2, 0, alignment=ARIGHT)
        graph_resolution_layout = self.create_annotated_slider(
                self.settings.value('graph_resolution', type=float) * 10, 1, 20,
                callback=self.set_graph_resolution_setting)
        sec_1.addLayout(graph_resolution_layout, 2, 1, alignment=ALEFT)
        split_length_label = self.create_label('Auto Split After Lines:', 'label_subhead')
        sec_1.addWidget(split_length_label, 3, 0, alignment=ARIGHT)
        split_length_validator = QIntValidator()
        split_length_validator.setBottom(1)
        split_length_entry = self.create_entry(
                self.settings.value('split_log_after', type=str), split_length_validator,
                style_override={'margin-top': 0})
        split_length_entry.setSizePolicy(SMIXMAX)
        split_length_entry.editingFinished.connect(lambda: self.settings.setValue(
                'split_log_after', split_length_entry.text()))
        sec_1.addWidget(split_length_entry, 3, 1, alignment=AVCENTER)
        overview_sort_label = self.create_label('Sort overview table by column:', 'label_subhead')
        sec_1.addWidget(overview_sort_label, 4, 0, alignment=ARIGHT)
        overview_sort_combo = self.create_combo_box(
                col_2_frame, style_override={'font': '@small_text'})
        overview_sort_combo.addItems(TABLE_HEADER)
        overview_sort_combo.setCurrentIndex(self.settings.value('overview_sort_column', type=int))
        overview_sort_combo.currentIndexChanged.connect(
                lambda new_index: self.settings.setValue('overview_sort_column', new_index))
        sec_1.addWidget(overview_sort_combo, 4, 1, alignment=ALEFT | AVCENTER)
        overview_sort_order_label = self.create_label('Overview table sort order:', 'label_subhead')
        sec_1.addWidget(overview_sort_order_label, 5, 0, alignment=ARIGHT)
        overview_sort_order_combo = self.create_combo_box(
                col_2_frame, style_override={'font': '@small_text'})
        overview_sort_order_combo.addItems(('Descending', 'Ascending'))
        overview_sort_order_combo.setCurrentText(self.settings.value('overview_sort_order'))
        overview_sort_order_combo.currentTextChanged.connect(
                lambda new_text: self.settings.setValue('overview_sort_order', new_text))
        sec_1.addWidget(overview_sort_order_combo, 5, 1, alignment=ALEFT | AVCENTER)
        auto_scan_label = self.create_label('Scan log automatically:', 'label_subhead')
        sec_1.addWidget(auto_scan_label, 6, 0, alignment=ARIGHT)
        auto_scan_button = FlipButton('Disabled', 'Enabled', col_2_frame, checkable=True)
        auto_scan_button.setStyleSheet(self.get_style_class(
                'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        auto_scan_button.setFont(self.theme_font('app', '@font'))
        auto_scan_button.r_function = lambda: self.settings.setValue('auto_scan', True)
        auto_scan_button.l_function = lambda: self.settings.setValue('auto_scan', False)
        if self.settings.value('auto_scan', type=bool):
            auto_scan_button.flip()
        sec_1.addWidget(auto_scan_button, 6, 1, alignment=ALEFT | AVCENTER)
        sto_log_path_button = self.create_button('STO Logfile:', style_override={
                'margin': 0, 'font': '@subhead', 'border-color': '@bc', 'border-style': 'solid',
                'border-width': '@bw'})
        sec_1.addWidget(sto_log_path_button, 7, 0, alignment=ARIGHT | AVCENTER)
        sto_log_path_entry = self.create_entry(
                self.settings.value('sto_log_path'), style_override={'margin-top': 0})
        sto_log_path_entry.setSizePolicy(SMIXMAX)
        sto_log_path_entry.editingFinished.connect(
                lambda: self.set_sto_logpath_setting(sto_log_path_entry))
        sec_1.addWidget(sto_log_path_entry, 7, 1, alignment=AVCENTER)
        sto_log_path_button.clicked.connect(lambda: self.browse_sto_logpath(sto_log_path_entry))
        opacity_label = self.create_label('Live Parser Opacity:', 'label_subhead')
        sec_1.addWidget(opacity_label, 8, 0, alignment=ARIGHT)
        opacity_slider_layout = self.create_annotated_slider(
                default_value=round(self.settings.value('live_parser_opacity', type=float) * 20, 0),
                min=1, max=20,
                style_override_slider={'::sub-page:horizontal': {'background-color': '@bc'}},
                callback=self.set_parser_opacity_setting)
        sec_1.addLayout(opacity_slider_layout, 8, 1, alignment=AVCENTER)
        live_graph_active_label = self.create_label('LiveParser Graph:', 'label_subhead')
        sec_1.addWidget(live_graph_active_label, 9, 0, alignment=ARIGHT)
        live_graph_active_button = FlipButton('Disabled', 'Enabled', col_2_frame, checkable=True)
        live_graph_active_button.setStyleSheet(self.get_style_class(
                'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        live_graph_active_button.setFont(self.theme_font('app', '@font'))
        live_graph_active_button.r_function = (
                lambda: self.settings.setValue('live_graph_active', True))
        live_graph_active_button.l_function = (
                lambda: self.settings.setValue('live_graph_active', False))
        if self.settings.value('live_graph_active', type=bool):
            live_graph_active_button.flip()
        sec_1.addWidget(live_graph_active_button, 9, 1, alignment=ALEFT | AVCENTER)
        live_graph_field_label = self.create_label('LiveParser Graph Field:', 'label_subhead')
        sec_1.addWidget(live_graph_field_label, 10, 0, alignment=ARIGHT)
        live_graph_field_combo = self.create_combo_box(
                col_2_frame, style_override={'font': '@small_text'})
        live_graph_field_combo.addItems(self.config['live_graph_fields'])
        live_graph_field_combo.setCurrentIndex(self.settings.value('live_graph_field', type=int))
        live_graph_field_combo.currentIndexChanged.connect(
                lambda new_index: self.settings.setValue('live_graph_field', new_index))
        sec_1.addWidget(live_graph_field_combo, 10, 1, alignment=ALEFT)
        overview_tab_label = self.create_label('Default Overview Tab:', 'label_subhead')
        sec_1.addWidget(overview_tab_label, 11, 0, alignment=ARIGHT)
        overview_tab_combo = self.create_combo_box(
                col_2_frame, style_override={'font': '@small_text'})
        overview_tab_combo.addItems(('DPS Bar', 'DPS Graph', 'Damage Graph'))
        overview_tab_combo.setCurrentIndex(self.settings.value('first_overview_tab', type=int))
        overview_tab_combo.currentIndexChanged.connect(
            lambda new_index: self.settings.setValue('first_overview_tab', new_index))
        sec_1.addWidget(overview_tab_combo, 11, 1, alignment=ALEFT)
        size_warning_label = self.create_label('Logfile Size Warning:', 'label_subhead')
        sec_1.addWidget(size_warning_label, 12, 0, alignment=ARIGHT)
        size_warning_button = FlipButton('Disabled', 'Enabled', col_2_frame, checkable=True)
        size_warning_button.setStyleSheet(self.get_style_class(
                'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        size_warning_button.setFont(self.theme_font('app', '@font'))
        size_warning_button.r_function = (
                lambda: self.settings.setValue('log_size_warning', True))
        size_warning_button.l_function = (
                lambda: self.settings.setValue('log_size_warning', False))
        if self.settings.value('log_size_warning', type=bool):
            size_warning_button.flip()
        sec_1.addWidget(size_warning_button, 12, 1, alignment=ALEFT)
        ui_scale_label = self.create_label('UI Scale:', 'label_subhead')
        sec_1.addWidget(ui_scale_label, 13, 0, alignment=ARIGHT)
        ui_scale_slider_layout = self.create_annotated_slider(
                default_value=round(self.settings.value('ui_scale', type=float) * 50, 0),
                min=25, max=75, callback=self.set_ui_scale_setting)
        sec_1.addLayout(ui_scale_slider_layout, 13, 1, alignment=ALEFT)
        ui_scale_label = self.create_label('LiveParser Scale:', 'label_subhead')
        sec_1.addWidget(ui_scale_label, 14, 0, alignment=ARIGHT)
        live_scale_slider_layout = self.create_annotated_slider(
                default_value=round(self.settings.value('live_scale', type=float) * 50, 0),
                min=25, max=75, callback=self.set_live_scale_setting)
        sec_1.addLayout(live_scale_slider_layout, 14, 1, alignment=ALEFT)
        sec_1.setAlignment(AHCENTER)
        scroll_layout.addLayout(sec_1)

        # seperator
        section_seperator = self.create_frame(
            scroll_frame, 'hr', style_override={'background-color': '@lbg'},
            size_policy=SMINMIN)
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
        dmg_hider_label = self.create_label(
            'Damage table columns:', 'label_subhead')
        sec_2.addWidget(dmg_hider_label)
        dmg_hider_layout = QVBoxLayout()
        dmg_hider_frame = self.create_frame(
                col_1_frame, size_policy=SMINMAX, style_override=hider_frame_style_override)
        dmg_hider_frame.setMinimumWidth(self.sidebar_item_width)
        self.set_buttons = list()
        for i, head in enumerate(TREE_HEADER[1:]):
            bt = self.create_button(
                    head, 'toggle_button', dmg_hider_frame,
                    toggle=self.settings.value(f'dmg_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                    lambda state, i=i: self.settings.setValue(f'dmg_columns|{i}', state))
            dmg_hider_layout.addWidget(bt, stretch=1)
        dmg_seperator = self.create_frame(
                dmg_hider_frame, 'hr', style_override={'background-color': '@lbg'},
                size_policy=SMINMIN)
        dmg_seperator.setFixedHeight(self.theme['defaults']['bw'])
        dmg_hider_layout.addWidget(dmg_seperator)
        apply_button = self.create_button('Apply', 'button', dmg_hider_frame)
        apply_button.clicked.connect(self.update_shown_columns_dmg)
        dmg_hider_layout.addWidget(apply_button, alignment=ARIGHT | ATOP)
        dmg_hider_frame.setLayout(dmg_hider_layout)
        sec_2.addWidget(dmg_hider_frame, alignment=ATOP)

        heal_hider_label = self.create_label(
                'Heal table columns:', 'label_subhead')
        sec_2.addWidget(heal_hider_label)
        heal_hider_layout = QVBoxLayout()
        heal_hider_frame = self.create_frame(
                col_1_frame, size_policy=SMINMAX, style_override=hider_frame_style_override)
        for i, head in enumerate(HEAL_TREE_HEADER[1:]):
            bt = self.create_button(
                    head, 'toggle_button', heal_hider_frame,
                    toggle=self.settings.value(f'heal_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                    lambda state, i=i: self.settings.setValue(f'heal_columns|{i}', state))
            heal_hider_layout.addWidget(bt, stretch=1)
        heal_seperator = self.create_frame(
            heal_hider_frame, 'hr', style_override={'background-color': '@lbg'},
            size_policy=SMINMIN)
        heal_seperator.setFixedHeight(self.theme['defaults']['bw'])
        heal_hider_layout.addWidget(heal_seperator)
        apply_button_2 = self.create_button('Apply', 'button', heal_hider_frame)
        apply_button_2.clicked.connect(self.update_shown_columns_heal)
        heal_hider_layout.addWidget(apply_button_2, alignment=ARIGHT | ATOP)
        heal_hider_frame.setLayout(heal_hider_layout)

        sec_2.addWidget(heal_hider_frame, alignment=ATOP)
        live_hider_label = self.create_label(
                'Live Parser columns:', 'label_subhead')
        sec_2.addWidget(live_hider_label)
        live_hider_layout = QVBoxLayout()
        live_hider_frame = self.create_frame(
                col_1_frame, size_policy=SMINMAX, style_override=hider_frame_style_override)
        for i, head in enumerate(LIVE_TABLE_HEADER):
            bt = self.create_button(
                    head, 'toggle_button', live_hider_frame,
                    toggle=self.settings.value(f'live_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                    lambda state, i=i: self.settings.setValue(f'live_columns|{i}', state))
            live_hider_layout.addWidget(bt, stretch=1)
        live_hider_frame.setLayout(live_hider_layout)
        sec_2.addWidget(live_hider_frame, alignment=ATOP)

        scroll_layout.addLayout(sec_2)

        scroll_frame.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_frame)
