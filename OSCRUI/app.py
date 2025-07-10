import os

from PySide6.QtWidgets import (
        QApplication, QWidget, QLayout, QLineEdit, QFrame, QListView, QListWidget, QListWidgetItem,
        QScrollArea, QSplitter, QTabWidget, QTableView, QVBoxLayout, QHBoxLayout, QGridLayout)
from PySide6.QtCore import QSize, QSettings, Qt, QTimer, QThread
from PySide6.QtGui import QFontDatabase, QIcon, QIntValidator, QKeySequence, QShortcut

from OSCR import LIVE_TABLE_HEADER, OSCR, TABLE_HEADER, TREE_HEADER, HEAL_TREE_HEADER
from .datamodels import CombatModel
from .iofunctions import get_asset_path, load_icon_series, load_icon, open_link
from .leagueconnector import OSCRClient
from .textedit import format_path
from .translation import init_translation, tr
from .widgetbuilder import (
        ABOTTOM, ACENTER, AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER, OVERTICAL,
        SMAXMAX, SMAXMIN, SMINMAX, SMINMIN, SMIXMAX, SMIXMIN,
        SCROLLOFF, SCROLLON)
from .widgets import (
        AnalysisPlot, BannerLabel, CombatDelegate, FlipButton, ParserSignals, WidgetStorage)

# only for developing; allows to terminate the qt event loop with keyboard interrupt
# from signal import signal, SIGINT, SIG_DFL
# signal(SIGINT, SIG_DFL)


class OSCRUI():

    from .callbacks import (
            add_favorite_ladder, browse_log, browse_sto_logpath, collapse_analysis_graph,
            collapse_overview_table, expand_analysis_graph, expand_overview_table,
            remove_favorite_ladder, save_combat, set_live_scale_setting, set_parser_opacity_setting,
            set_graph_resolution_setting, set_sto_logpath_setting, set_ui_scale_setting,
            switch_analysis_tab, switch_main_tab, switch_overview_tab)
    from .datafunctions import (
            analysis_data_slot, analyze_log_background, analyze_log_callback,
            copy_analysis_callback, copy_analysis_table_callback, copy_summary_callback,
            insert_combat, update_shown_columns_dmg, update_shown_columns_heal)
    from .displayer import create_legend_item
    from .iofunctions import browse_path
    from .style import get_style_class, create_style_sheet, theme_font, get_style
    from .subwindows import live_parser_toggle, show_detection_info, show_parser_error, split_dialog
    from .widgetbuilder import create_analysis_table, create_annotated_slider, create_button
    from .widgetbuilder import create_button_series, create_combo_box, create_entry, create_frame
    from .widgetbuilder import create_icon_button, create_label, style_table
    from .leagueconnector import apply_league_table_filter, download_and_view_combat
    from .leagueconnector import (
            establish_league_connection, extend_ladder, slot_ladder,
            update_seasonal_records)
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
        self.live_parser_window = None
        self.live_parser = None
        self.init_settings()
        self.init_config()

        init_translation(self.settings.value('language'))
        self.league_api = None

        self.app, self.window = self.create_main_window()
        self.copy_shortcut = QShortcut(
                QKeySequence.StandardKey.Copy, self.window, self.copy_analysis_table_callback)
        self.init_parser()
        self.cache_assets()
        self.setup_main_layout()

        self.window.show()
        if self.settings.value('auto_scan', type=bool):
            QTimer.singleShot(
                    100,
                    lambda: self.analyze_log_callback(path=self.entry.text()))

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
            'TFO-elite': 'TFO_elite.png'
        }
        self.icons = load_icon_series(icons, self.app_dir)

    def init_settings(self):
        """
        Prepares settings. Loads stored settings. Saves current settings for next startup.
        """

        # For Windows, Keep the Local settings for now as people are more familiar with that.
        if os.name == "nt":
            settings_path = os.path.abspath(self.app_dir + self.config["settings_path"])
            self.settings = QSettings(settings_path, QSettings.Format.IniFormat)
        else:
            self.settings = QSettings("OSCR", "OSCR-UI")

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
        self.config['ui_scale'] = self.settings.value('ui_scale', type=float)
        self.config['live_scale'] = self.settings.value('live_scale', type=float)
        self.config['icon_size'] = round(
                self.config['ui_scale'] * self.theme['s.c']['button_icon_size'])
        self.config['settings_path'] = os.path.abspath(self.app_dir + self.config['settings_path'])
        self.config['templog_folder_path'] = os.path.abspath(
                self.app_dir + self.config['templog_folder_path'])

    def init_parser(self):
        """
        Initializes Parser.
        """
        self.parser = OSCR(settings=self.parser_settings)
        self.parser_signals = ParserSignals()
        self.parser_signals.analyzed_combat.connect(self.insert_combat)
        self.parser_signals.parser_error.connect(self.show_parser_error)
        self.parser.combat_analyzed_callback = lambda c: self.parser_signals.analyzed_combat.emit(c)
        self.parser.error_callback = lambda e: self.parser_signals.parser_error.emit(e)
        self.thread = None  # used for logfile analyzation

    @property
    def parser_settings(self) -> dict:
        """
        Returns settings relevant to the parser
        """
        relevant_settings = (
                ('combats_to_parse', int), ('seconds_between_combats', int),
                ('excluded_event_ids', list), ('graph_resolution', float),
                ('combat_min_lines', int))
        settings = dict()
        for setting_key, settings_type in relevant_settings:
            setting = self.settings.value(setting_key, type=settings_type, defaultValue='')
            if setting != '':
                settings[setting_key] = setting
        settings['templog_folder_path'] = self.config['templog_folder_path']
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
        self.settings.setValue('overview_splitter', self.widgets.overview_splitter.saveState())
        self.settings.setValue('analysis_splitter', self.widgets.analysis_splitter.saveState())
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
        QThread.currentThread().setPriority(QThread.Priority.TimeCriticalPriority)
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

        margin = self.theme['defaults']['margin']
        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, margin, 0)
        main_layout.setSpacing(0)

        left = self.create_frame()
        left.setSizePolicy(SMAXMIN)
        main_layout.addWidget(left, 0, 0)

        button_column = QGridLayout()
        csp = self.theme['defaults']['csp']
        button_column.setContentsMargins(csp, csp, csp, csp)
        button_column.setRowStretch(0, 1)
        main_layout.addLayout(button_column, 0, 1)
        icon_size = self.config['icon_size']
        left_flip_config = {
            'icon_r': self.icons['collapse-left'], 'func_r': left.hide,
            'icon_l': self.icons['expand-left'], 'func_l': left.show,
            'tooltip_r': tr('Collapse Sidebar'), 'tooltip_l': tr('Expand Sidebar')
        }
        sidebar_flip_button = FlipButton('', '')
        sidebar_flip_button.configure(left_flip_config)
        sidebar_flip_button.setIconSize(QSize(icon_size, icon_size))
        sidebar_flip_button.setStyleSheet(self.get_style_class('QPushButton', 'small_button'))
        sidebar_flip_button.setSizePolicy(SMAXMAX)
        button_column.addWidget(sidebar_flip_button, 0, 0, alignment=ATOP)

        graph_flip_config = {
            'icon_r': self.icons['collapse-top'], 'tooltip_r': tr('Collapse Graph'),
            'func_r': self.collapse_analysis_graph,
            'icon_l': self.icons['expand-top'], 'tooltip_l': tr('Expand Graph'),
            'func_l': self.expand_analysis_graph
        }
        graph_button = FlipButton('', '')
        graph_button.configure(graph_flip_config)
        graph_button.setIconSize(QSize(icon_size, icon_size))
        graph_button.setStyleSheet(self.get_style_class('QPushButton', 'small_button'))
        graph_button.setSizePolicy(SMAXMAX)
        button_column.addWidget(graph_button, 2, 0)
        graph_button.hide()
        self.widgets.analysis_graph_button = graph_button

        table_flip_config = {
            'icon_r': self.icons['collapse-bottom'], 'tooltip_r': tr('Collapse Table'),
            'func_r': self.collapse_overview_table,
            'icon_l': self.icons['expand-bottom'], 'tooltip_l': tr('Expand Table'),
            'func_l': self.expand_overview_table
        }
        table_button = FlipButton('', '')
        table_button.configure(table_flip_config)
        table_button.setIconSize(QSize(icon_size, icon_size))
        table_button.setStyleSheet(self.get_style_class('QPushButton', 'small_button'))
        table_button.setSizePolicy(SMAXMAX)
        button_column.addWidget(table_button, 3, 0)
        self.widgets.overview_table_button = table_button

        center = self.create_frame()
        center.setSizePolicy(SMINMIN)
        main_layout.addWidget(center, 0, 2)

        main_frame.setLayout(main_layout)
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
        left_layout.setSpacing(self.theme['defaults']['csp'])
        left_layout.setAlignment(ATOP)

        map_layout = QHBoxLayout()
        map_label = self.create_label(tr('Available Maps:'), 'label_heading')
        map_layout.addWidget(map_label, alignment=ALEFT | ABOTTOM)
        fav_add_button = self.create_icon_button(
                self.icons['star-plus'], tr('Add to Favorites'))
        fav_add_button.clicked.connect(self.add_favorite_ladder)
        map_layout.addWidget(fav_add_button, alignment=ARIGHT)
        left_layout.addLayout(map_layout)

        variant_list = self.create_combo_box()
        variant_list.currentTextChanged.connect(lambda text: self.update_seasonal_records(text))
        left_layout.addWidget(variant_list)
        self.widgets.variant_combo = variant_list

        background_frame = self.create_frame(size_policy=SMINMIN, style_override={
                'border-radius': self.theme['listbox']['border-radius']})
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        ladder_selector = QListWidget(background_frame)
        ladder_selector.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        ladder_selector.setFont(self.theme_font('listbox'))
        ladder_selector.setSizePolicy(SMIXMIN)
        ladder_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.widgets.ladder_selector = ladder_selector
        ladder_selector.itemClicked.connect(
                lambda clicked_item: self.slot_ladder(clicked_item))
        background_layout.addWidget(ladder_selector)
        left_layout.addWidget(background_frame, stretch=3)

        fav_layout = QHBoxLayout()
        favorites_label = self.create_label(tr('Favorites:'), 'label_heading')
        fav_layout.addWidget(favorites_label, alignment=ALEFT | ABOTTOM)
        fav_add_button = self.create_icon_button(
                self.icons['star-minus'], tr('Add to Favorites'))
        fav_add_button.clicked.connect(self.remove_favorite_ladder)
        fav_layout.addWidget(fav_add_button, alignment=ARIGHT)
        left_layout.addLayout(fav_layout)

        background_frame = self.create_frame(size_policy=SMINMIN, style_override={
                'border-radius': self.theme['listbox']['border-radius']})
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        favorite_selector = QListWidget(background_frame)
        favorite_selector.setStyleSheet(self.get_style_class('QListWidget', 'listbox'))
        favorite_selector.setFont(self.theme_font('listbox'))
        favorite_selector.setSizePolicy(SMIXMIN)
        favorite_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.widgets.favorite_ladder_selector = favorite_selector
        for favorite_ladder in self.settings.value('favorite_ladders', type=list):
            if '|' not in favorite_ladder:
                self.settings.setValue('favorite_ladders', list())
                break
            ladder_text, difficulty = favorite_ladder.split('|')
            if difficulty == 'None':
                difficulty = None
            item = QListWidgetItem(ladder_text)
            item.difficulty = difficulty
            if difficulty != 'Any' and difficulty is not None:
                icon = self.icons[f'TFO-{difficulty.lower()}']
                icon.addPixmap(icon.pixmap(18, 24), QIcon.Mode.Selected)
                item.setIcon(icon)
            favorite_selector.addItem(item)
        favorite_selector.itemClicked.connect(
                lambda clicked_item: self.slot_ladder(clicked_item))
        background_layout.addWidget(favorite_selector)
        left_layout.addWidget(background_frame, stretch=2)

        ladder_selector.itemClicked.connect(favorite_selector.clearSelection)
        favorite_selector.itemClicked.connect(ladder_selector.clearSelection)

        frame.setLayout(left_layout)

    def setup_left_sidebar_log(self):
        """
        Sets up the log management tab of the left sidebar
        """
        frame = self.widgets.sidebar_tab_frames[0]
        margin = self.theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(margin, margin, margin, margin)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        head_layout = QHBoxLayout()
        head = self.create_label(tr('STO Combatlog:'), 'label_heading')
        head_layout.addWidget(head, alignment=ALEFT | ABOTTOM)
        cut_log_button = self.create_icon_button(
                self.icons['edit'], tr('Manage Logfile'))
        cut_log_button.clicked.connect(self.split_dialog)
        head_layout.addWidget(cut_log_button, alignment=ARIGHT)
        left_layout.addLayout(head_layout)

        self.entry = QLineEdit(self.settings.value('log_path', ''))
        self.entry.setStyleSheet(self.get_style_class('QLineEdit', 'entry'))
        self.entry.setFont(self.theme_font('entry'))
        self.entry.setSizePolicy(SMIXMAX)
        left_layout.addWidget(self.entry)

        entry_button_config = {
            tr('Browse ...'): {
                'callback': lambda: self.browse_log(self.entry), 'align': ALEFT,
                'style': {'margin-left': 0}
            },
            tr('Default'): {
                'callback': lambda: self.entry.setText(self.settings.value('sto_log_path')),
                'align': AHCENTER
            },
            tr('Analyze'): {
                'callback': lambda: self.analyze_log_callback(path=self.entry.text()),
                'align': ARIGHT, 'style': {'margin-right': 0}
            }
        }
        entry_buttons = self.create_button_series(entry_button_config, 'button')
        entry_buttons.setContentsMargins(0, 0, 0, self.theme['defaults']['margin'])
        left_layout.addLayout(entry_buttons)

        background_frame = self.create_frame(size_policy=SMINMIN, style_override={
                'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp',
                'margin-bottom': '@csp'})
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        self.current_combats = QListView(background_frame)
        self.current_combats.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.current_combats.setStyleSheet(self.get_style_class('QListView', 'listbox'))
        self.current_combats.setFont(self.theme_font('listbox'))
        self.current_combats.setAlternatingRowColors(True)
        self.current_combats.setSizePolicy(SMIXMIN)
        self.current_combats.setModel(CombatModel())
        ui_scale = self.config['ui_scale']
        border_width = 1 * ui_scale
        padding = 4 * ui_scale
        self.current_combats.setItemDelegate(CombatDelegate(border_width, padding))
        self.current_combats.doubleClicked.connect(
            lambda: self.analysis_data_slot(self.current_combats.currentIndex().data()[0]))
        background_layout.addWidget(self.current_combats)
        left_layout.addWidget(background_frame, stretch=1)

        combat_button_row = QGridLayout()
        combat_button_row.setContentsMargins(0, 0, 0, 0)
        combat_button_row.setSpacing(self.theme['defaults']['csp'])
        combat_button_row.setColumnStretch(2, 1)
        export_button = self.create_icon_button(
                self.icons['export-parse'], tr('Export Combat'), parent=frame)
        combat_button_row.addWidget(export_button, 0, 0)
        more_combats_button = self.create_icon_button(
                self.icons['parser-down'], tr('Parse Older Combats'), parent=frame)
        combat_button_row.addWidget(more_combats_button, 0, 1)
        left_layout.addLayout(combat_button_row)
        more_combats_button.clicked.connect(lambda: self.analyze_log_background(
                self.settings.value('combats_to_parse', type=int)))
        export_button.clicked.connect(
                lambda: self.save_combat(self.current_combats.currentIndex().data()[0]))

        sep = self.create_frame(style='medium_frame')
        sep.setFixedHeight(margin)
        left_layout.addWidget(sep)
        log_layout = QHBoxLayout()
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(margin)
        log_layout.setAlignment(ALEFT)
        player_duration_label = self.create_label(tr('Log Duration:'))
        log_layout.addWidget(player_duration_label)
        self.widgets.log_duration_value = self.create_label('')
        log_layout.addWidget(self.widgets.log_duration_value)
        left_layout.addLayout(log_layout)
        player_layout = QHBoxLayout()
        player_layout.setContentsMargins(0, 0, 0, 0)
        player_layout.setSpacing(margin)
        player_layout.setAlignment(ALEFT)
        player_duration_label = self.create_label(tr('Active Player Duration:'))
        player_layout.addWidget(player_duration_label)
        self.widgets.player_duration_value = self.create_label('')
        player_layout.addWidget(self.widgets.player_duration_value)
        left_layout.addLayout(player_layout)
        detection_button = self.create_button(tr('Map Detection Details'))
        detection_button.clicked.connect(
                lambda: self.show_detection_info(self.current_combats.currentIndex().data()[0]))
        left_layout.addWidget(detection_button, alignment=AHCENTER)

        frame.setLayout(left_layout)

    def setup_left_sidebar_about(self):
        """
        Sets up the about tab of the left sidebar
        """
        frame = self.widgets.sidebar_tab_frames[2]
        m = self.theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(m)
        left_layout.setAlignment(ATOP)

        head_label = self.create_label(tr('About OSCR:'), 'label_heading')
        left_layout.addWidget(head_label)
        about_label = self.create_label(tr(
                'Open Source Combatlog Reader (OSCR), developed by the STO Community '
                'Developers in cooperation with the STO Builds Discord.'))
        about_label.setWordWrap(True)
        about_label.setMinimumWidth(50)  # to fix the word wrap
        about_label.setSizePolicy(SMINMAX)
        left_layout.addWidget(about_label)
        link_button_style = {
            'default': {},
            tr('Website'): {
                'callback': lambda: open_link(self.config['link_website']), 'align': AHCENTER},
            tr('Github'): {
                'callback': lambda: open_link(self.config['link_github']), 'align': AHCENTER},
            tr('Downloads'): {
                'callback': lambda: open_link(self.config['link_downloads']), 'align': AHCENTER}
        }
        button_layout, buttons = self.create_button_series(
                link_button_style, 'button', shape='column', ret=True)
        buttons[0].setToolTip(self.config['link_website'])
        buttons[1].setToolTip(self.config['link_github'])
        buttons[2].setToolTip(self.config['link_downloads'])
        link_button_frame = self.create_frame(style='medium_frame')
        link_button_frame.setLayout(button_layout)
        left_layout.addWidget(link_button_frame, alignment=AHCENTER)
        seperator = self.create_frame(style='light_frame', size_policy=SMINMAX)
        seperator.setFixedHeight(1)
        left_layout.addWidget(seperator)
        version_label = self.create_label(
                f'{tr("Version")}: {self.versions[0]} ({self.versions[1]})', 'label_subhead')
        left_layout.addWidget(version_label)
        logo_layout = QGridLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setColumnStretch(1, 1)
        logo_size = [self.config['icon_size'] * 4] * 2
        stocd_logo = self.create_icon_button(
                self.icons['stocd'], self.config['link_stocd'],
                style_override={'border-style': 'none'}, icon_size=logo_size)
        stocd_logo.clicked.connect(lambda: open_link(self.config['link_stocd']))
        logo_layout.addWidget(stocd_logo, 0, 0)
        stobuilds_logo = self.create_icon_button(
                self.icons['stobuilds'], self.config['link_stobuilds'],
                style_override={'border-style': 'none'}, icon_size=logo_size)
        stobuilds_logo.clicked.connect(lambda: open_link(self.config['link_stobuilds']))
        logo_layout.addWidget(stobuilds_logo, 0, 2)
        logo_frame = self.create_frame(style='medium_frame', size_policy=SMINMAX)
        logo_frame.setLayout(logo_layout)
        left_layout.addWidget(logo_frame, stretch=1, alignment=ABOTTOM)
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
        sidebar_tabber.tabBar().hide()
        sidebar_tabber.setSizePolicy(SMAXMIN)
        sidebar_tabber.addTab(log_frame, tr('Log'))
        sidebar_tabber.addTab(league_frame, tr('League'))
        sidebar_tabber.addTab(about_frame, tr('About'))
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
        splitter = QSplitter(OVERTICAL)
        splitter.setStyleSheet(self.get_style_class('QSplitter', 'splitter'))
        splitter.setChildrenCollapsible(False)
        self.widgets.overview_splitter = splitter
        layout.addWidget(splitter)

        o_tabber = QTabWidget(o_frame)
        o_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        o_tabber.tabBar().hide()
        o_tabber.addTab(bar_frame, 'BAR')
        o_tabber.addTab(dps_graph_frame, 'DPS')
        o_tabber.addTab(dmg_graph_frame, 'DMG')
        o_tabber.setMinimumHeight(self.sidebar_item_width * 0.8)
        splitter.addWidget(o_tabber)
        splitter.setStretchFactor(0, self.theme['s.c']['overview_graph_stretch'])

        switch_layout.setColumnStretch(0, 1)
        switch_frame = self.create_frame()
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 2)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            tr('DPS Bar'): {
                'callback': lambda: self.switch_overview_tab(0), 'align': ACENTER, 'toggle': True},
            tr('DPS Graph'): {
                'callback': lambda: self.switch_overview_tab(1), 'align': ACENTER, 'toggle': False},
            tr('Damage Graph'): {
                'callback': lambda: self.switch_overview_tab(2), 'align': ACENTER, 'toggle': False}
        }
        switcher, buttons = self.create_button_series(
                switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.overview_menu_buttons = buttons
        icon_layout = QHBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(self.theme['defaults']['csp'])
        copy_button = self.create_icon_button(self.icons['copy'], tr('Copy Result'))
        copy_button.clicked.connect(self.copy_summary_callback)
        icon_layout.addWidget(copy_button)
        ladder_button = self.create_icon_button(self.icons['ladder'], tr('Upload Result'))
        ladder_button.clicked.connect(self.upload_callback)
        icon_layout.addWidget(ladder_button)
        switch_layout.addLayout(icon_layout, 0, 2, alignment=ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)
        table_frame = self.create_frame(size_policy=SMINMIN)
        table_frame.setMinimumHeight(self.sidebar_item_width * 0.4)
        splitter.addWidget(table_frame)
        self.widgets.overview_table_frame = table_frame
        o_frame.setLayout(layout)
        if self.settings.value('overview_splitter'):
            splitter.restoreState(self.settings.value('overview_splitter'))
        else:
            h = splitter.height()
            splitter.setSizes((h * 0.5, h * 0.5))
        self.widgets.overview_tabber = o_tabber

    def setup_analysis_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        a_frame = self.widgets.main_tab_frames[1]
        dout_graph_frame = self.create_frame()
        dtaken_graph_frame = self.create_frame()
        hout_graph_frame = self.create_frame()
        hin_graph_frame = self.create_frame()
        self.widgets.analysis_graph_frames.extend(
                (dout_graph_frame, dtaken_graph_frame, hout_graph_frame, hin_graph_frame))
        dout_tree_frame = self.create_frame()
        dtaken_tree_frame = self.create_frame()
        hout_tree_frame = self.create_frame()
        hin_tree_frame = self.create_frame()
        self.widgets.analysis_tree_frames.extend(
                (dout_tree_frame, dtaken_tree_frame, hout_tree_frame, hin_tree_frame))
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        switch_layout = QGridLayout()
        switch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(switch_layout)
        splitter = QSplitter(OVERTICAL)
        splitter.setStyleSheet(self.get_style_class('QSplitter', 'splitter'))
        splitter.setChildrenCollapsible(False)
        self.widgets.analysis_splitter = splitter
        layout.addWidget(splitter)

        a_graph_tabber = QTabWidget(a_frame)
        a_graph_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        a_graph_tabber.tabBar().hide()
        a_graph_tabber.addTab(dout_graph_frame, 'DOUT')
        a_graph_tabber.addTab(dtaken_graph_frame, 'DTAKEN')
        a_graph_tabber.addTab(hout_graph_frame, 'HOUT')
        a_graph_tabber.addTab(hin_graph_frame, 'HIN')
        self.widgets.analysis_graph_tabber = a_graph_tabber
        splitter.addWidget(a_graph_tabber)
        if not self.settings.value('analysis_graph', type=bool):
            self.widgets.analysis_graph_button.flip()
        a_tree_tabber = QTabWidget(a_frame)
        a_tree_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        a_tree_tabber.tabBar().hide()
        a_tree_tabber.addTab(dout_tree_frame, 'DOUT')
        a_tree_tabber.addTab(dtaken_tree_frame, 'DTAKEN')
        a_tree_tabber.addTab(hout_tree_frame, 'HOUT')
        a_tree_tabber.addTab(hin_tree_frame, 'HIN')
        self.widgets.analysis_tree_tabber = a_tree_tabber
        splitter.addWidget(a_tree_tabber)

        switch_layout.setColumnStretch(0, 1)
        switch_frame = self.create_frame()
        switch_layout.addWidget(switch_frame, 0, 1, alignment=ACENTER)
        switch_layout.setColumnStretch(1, 1)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            tr('Damage Out'): {
                'callback': lambda state: self.switch_analysis_tab(0), 'align': ACENTER,
                'toggle': True},
            tr('Damage Taken'): {
                'callback': lambda state: self.switch_analysis_tab(1), 'align': ACENTER,
                'toggle': False},
            tr('Heals Out'): {
                'callback': lambda state: self.switch_analysis_tab(2), 'align': ACENTER,
                'toggle': False},
            tr('Heals In'): {
                'callback': lambda state: self.switch_analysis_tab(3), 'align': ACENTER,
                'toggle': False}
        }
        switcher, buttons = self.create_button_series(
                switch_style, 'tab_button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        switch_frame.setLayout(switcher)
        self.widgets.analysis_menu_buttons = buttons
        copy_layout = QHBoxLayout()
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(self.theme['defaults']['csp'])
        copy_combobox = self.create_combo_box()
        copy_combobox.addItems((
                tr('Selection'), tr('Global Max One Hit'), tr('Max One Hit'), tr('Magnitude'),
                tr('Magnitude / s')))
        copy_layout.addWidget(copy_combobox)
        self.widgets.analysis_copy_combobox = copy_combobox
        copy_button = self.create_icon_button(self.icons['copy'], 'Copy Data')
        copy_button.clicked.connect(self.copy_analysis_callback)
        copy_layout.addWidget(copy_button)
        switch_layout.addLayout(copy_layout, 0, 2, alignment=ARIGHT | ABOTTOM)
        switch_layout.setColumnStretch(2, 1)

        tabs = (
            (dout_graph_frame, dout_tree_frame, 'analysis_table_dout', 'analysis_plot_dout'),
            (dtaken_graph_frame, dtaken_tree_frame, 'analysis_table_dtaken',
             'analysis_plot_dtaken'),
            (hout_graph_frame, hout_tree_frame, 'analysis_table_hout', 'analysis_plot_hout'),
            (hin_graph_frame, hin_tree_frame, 'analysis_table_hin', 'analysis_plot_hin')
        )
        csp = self.theme['defaults']['csp'] * self.config['ui_scale']
        for graph_frame, tree_frame, table_name, plot_name in tabs:
            graph_layout = QHBoxLayout()
            graph_layout.setContentsMargins(csp, csp, csp, 0)
            graph_layout.setSpacing(csp)

            plot_bundle_frame = self.create_frame(size_policy=SMINMAX)
            plot_bundle_layout = QVBoxLayout()
            plot_bundle_layout.setContentsMargins(0, 0, 0, 0)
            plot_bundle_layout.setSpacing(0)
            plot_bundle_layout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
            plot_legend_frame = self.create_frame()
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
            graph_layout.addWidget(plot_bundle_frame, stretch=1)

            plot_button_frame = self.create_frame(size_policy=SMAXMIN)
            plot_button_layout = QVBoxLayout()
            plot_button_layout.setContentsMargins(0, 0, 0, 0)
            plot_button_layout.setSpacing(0)
            plot_button_layout.setAlignment(AVCENTER)
            freeze_button = self.create_icon_button(self.icons['freeze'], tr('Freeze Graph'))
            freeze_button.setCheckable(True)
            freeze_button.setChecked(True)
            freeze_button.clicked.connect(plot_widget.toggle_freeze)
            plot_button_layout.addWidget(freeze_button, alignment=ABOTTOM)
            clear_button = self.create_icon_button(self.icons['clear-plot'], tr('Clear Graph'))
            clear_button.clicked.connect(plot_widget.clear_plot)
            plot_button_layout.addWidget(clear_button, alignment=ATOP)
            plot_button_frame.setLayout(plot_button_layout)
            graph_layout.addWidget(plot_button_frame, stretch=0)
            graph_frame.setLayout(graph_layout)

            tree_layout = QVBoxLayout()
            tree_layout.setContentsMargins(0, 0, 0, 0)
            tree_layout.setSpacing(0)
            tree = self.create_analysis_table('tree_table')
            setattr(self.widgets, table_name, tree)
            tree.clicked.connect(lambda index, pw=plot_widget: self.slot_analysis_graph(index, pw))
            tree_layout.addWidget(tree)
            tree_frame.setLayout(tree_layout)

        a_frame.setLayout(layout)
        if self.settings.value('analysis_splitter'):
            splitter.restoreState(self.settings.value('analysis_splitter'))
        else:
            h = splitter.height()
            splitter.setSizes((h * 0.5, h * 0.5))

    def slot_analysis_graph(self, index, plot_widget: AnalysisPlot):
        item = index.internalPointer()
        color = plot_widget.add_bar(item)
        if color is None:
            return
        name = item.data[0]
        if isinstance(name, tuple):
            name = name[0] + name[1]
        legend_item = self.create_legend_item(color, name)
        plot_widget.add_legend_item(legend_item)

    def setup_league_standings_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        l_frame = self.widgets.main_tab_frames[2]
        m = self.theme['defaults']['csp']
        layout = QVBoxLayout()
        layout.setContentsMargins(0, m, 0, m)
        layout.setSpacing(m)

        ladder_table = QTableView(l_frame)
        table_style = {
                'border-style': 'solid', 'border-width': '@bw',
                'border-color': '@bc'}
        self.style_table(ladder_table, table_style, single_row_selection=True)
        self.widgets.ladder_table = ladder_table
        layout.addWidget(ladder_table, stretch=1)

        control_layout = QGridLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(0)
        control_layout.setColumnStretch(2, 1)
        search_label = self.create_label(
                tr('Search:'), 'label_subhead', style_override={'margin-bottom': 0})
        control_layout.addWidget(search_label, 0, 0, alignment=AVCENTER)
        search_bar = self.create_entry(
                placeholder=tr('name@handle'),
                style_override={'margin-left': '@isp', 'margin-top': 0})
        search_bar.textChanged.connect(lambda text: self.apply_league_table_filter(text))
        control_layout.addWidget(search_bar, 0, 1, alignment=AVCENTER)
        control_button_style = {
            tr('View Parse'): {'callback': self.download_and_view_combat},
            tr('More'): {'callback': self.extend_ladder, 'style': {'margin-right': 0}}
        }
        control_button_layout = self.create_button_series(
                control_button_style, 'button', seperator='•')
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
        bg_frame = self.create_frame(style_override={'background-color': '@oscr'})
        bg_frame.setSizePolicy(SMINMIN)
        layout.addWidget(bg_frame)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        lbl = BannerLabel(get_asset_path('oscrbanner-slim-dark-label.png', self.app_dir), bg_frame)
        main_layout.addWidget(lbl)

        menu_frame = self.create_frame(style_override={'background-color': '@oscr'})
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
        bt_lay, buttons = self.create_button_series(
                menu_button_style, style='menu_button', seperator='•', ret=True)
        menu_layout.addLayout(bt_lay, 0, 0)
        self.widgets.main_menu_buttons = buttons

        size = [self.config['icon_size'] * 1.3] * 2
        live_parser_button = self.create_icon_button(
                self.icons['live-parser'], tr('Live Parser'), 'live_icon_button', icon_size=size)
        live_parser_button.setCheckable(True)
        live_parser_button.clicked[bool].connect(lambda checked: self.live_parser_toggle(checked))
        menu_layout.addWidget(live_parser_button, 0, 2)
        self.widgets.live_parser_button = live_parser_button
        menu_frame.setLayout(menu_layout)

        w = self.theme['app']['frame_thickness']
        main_frame = self.create_frame(style_override={'margin': (0, w, w, w)})
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

        # first section
        sec_1 = QGridLayout()
        sec_1.setContentsMargins(0, 0, 0, 0)
        sec_1.setVerticalSpacing(self.theme['defaults']['isp'])
        sec_1.setHorizontalSpacing(self.theme['defaults']['csp'])

        combat_delta_label = self.create_label(tr('Seconds Between Combats:'), 'label_subhead')
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

        combat_num_label = self.create_label(tr('Number of combats to isolate:'), 'label_subhead')
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

        combat_lines_label = self.create_label(
                tr('Minimum number of lines per combat:'), 'label_subhead')
        sec_1.addWidget(combat_lines_label, 2, 0, alignment=ARIGHT)
        combat_lines_validator = QIntValidator()
        combat_lines_validator.setBottom(1)
        combat_lines_entry = self.create_entry(
                self.settings.value('combat_min_lines', type=str), combat_lines_validator,
                style_override={'margin-top': 0})
        combat_lines_entry.setSizePolicy(SMIXMAX)
        combat_lines_entry.editingFinished.connect(lambda: self.settings.setValue(
                'combat_min_lines', combat_lines_entry.text()))
        sec_1.addWidget(combat_lines_entry, 2, 1, alignment=AVCENTER)

        graph_resolution_label = self.create_label(
                tr('Graph resolution (interval in seconds):'), 'label_subhead')
        sec_1.addWidget(graph_resolution_label, 3, 0, alignment=ARIGHT)
        graph_resolution_layout = self.create_annotated_slider(
                self.settings.value('graph_resolution', type=float) * 10, 1, 20,
                callback=self.set_graph_resolution_setting)
        sec_1.addLayout(graph_resolution_layout, 3, 1, alignment=ALEFT)

        overview_sort_label = self.create_label(
                tr('Sort overview table by column:'), 'label_subhead')
        sec_1.addWidget(overview_sort_label, 4, 0, alignment=ARIGHT)
        overview_sort_combo = self.create_combo_box(style_override={'font': '@small_text'})
        overview_sort_combo.addItems(TABLE_HEADER)
        overview_sort_combo.setCurrentIndex(self.settings.value('overview_sort_column', type=int))
        overview_sort_combo.currentIndexChanged.connect(
                lambda new_index: self.settings.setValue('overview_sort_column', new_index))
        sec_1.addWidget(overview_sort_combo, 4, 1, alignment=ALEFT | AVCENTER)

        overview_sort_order_label = self.create_label(
                tr('Overview table sort order:'), 'label_subhead')
        sec_1.addWidget(overview_sort_order_label, 5, 0, alignment=ARIGHT)
        overview_sort_order_combo = self.create_combo_box(style_override={'font': '@small_text'})
        overview_sort_order_combo.addItems((tr('Descending'), tr('Ascending')))
        overview_sort_order_combo.setCurrentText(self.settings.value('overview_sort_order'))
        overview_sort_order_combo.currentTextChanged.connect(
                lambda new_text: self.settings.setValue('overview_sort_order', new_text))
        sec_1.addWidget(overview_sort_order_combo, 5, 1, alignment=ALEFT | AVCENTER)

        auto_scan_label = self.create_label(tr('Scan log automatically:'), 'label_subhead')
        sec_1.addWidget(auto_scan_label, 6, 0, alignment=ARIGHT)
        auto_scan_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
        auto_scan_button.setStyleSheet(self.get_style_class(
                'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        auto_scan_button.setFont(self.theme_font('app', '@font'))
        auto_scan_button.r_function = lambda: self.settings.setValue('auto_scan', True)
        auto_scan_button.l_function = lambda: self.settings.setValue('auto_scan', False)
        if self.settings.value('auto_scan', type=bool):
            auto_scan_button.flip()
        sec_1.addWidget(auto_scan_button, 6, 1, alignment=ALEFT | AVCENTER)
        sto_log_path_button = self.create_button(tr('STO Logfile:'), style_override={
                'margin': 0, 'font': ('Overpass', 11, 'medium'), 'border-color': '@bc',
                'border-style': 'solid', 'border-width': '@bw', 'padding-bottom': 1})
        sec_1.addWidget(sto_log_path_button, 7, 0, alignment=ARIGHT | AVCENTER)
        sto_log_path_entry = self.create_entry(
                self.settings.value('sto_log_path'), style_override={'margin-top': 0})
        sto_log_path_entry.setSizePolicy(SMIXMAX)
        sto_log_path_entry.editingFinished.connect(
                lambda: self.set_sto_logpath_setting(sto_log_path_entry))
        sec_1.addWidget(sto_log_path_entry, 7, 1, alignment=AVCENTER)
        sto_log_path_button.clicked.connect(lambda: self.browse_sto_logpath(sto_log_path_entry))

        opacity_label = self.create_label(tr('Live Parser Opacity:'), 'label_subhead')
        sec_1.addWidget(opacity_label, 8, 0, alignment=ARIGHT)
        opacity_slider_layout = self.create_annotated_slider(
                default_value=round(self.settings.value('live_parser_opacity', type=float) * 20, 0),
                min=1, max=20,
                style_override_slider={'::sub-page:horizontal': {'background-color': '@bc'}},
                callback=self.set_parser_opacity_setting)
        sec_1.addLayout(opacity_slider_layout, 8, 1, alignment=AVCENTER)

        live_graph_active_label = self.create_label(tr('LiveParser Graph:'), 'label_subhead')
        sec_1.addWidget(live_graph_active_label, 9, 0, alignment=ARIGHT)
        live_graph_active_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
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

        live_graph_field_label = self.create_label(tr('LiveParser Graph Field:'), 'label_subhead')
        sec_1.addWidget(live_graph_field_label, 10, 0, alignment=ARIGHT)
        live_graph_field_combo = self.create_combo_box(style_override={'font': '@small_text'})
        live_graph_field_combo.addItems(self.config['live_graph_fields'])
        live_graph_field_combo.setCurrentIndex(self.settings.value('live_graph_field', type=int))
        live_graph_field_combo.currentIndexChanged.connect(
                lambda new_index: self.settings.setValue('live_graph_field', new_index))
        sec_1.addWidget(live_graph_field_combo, 10, 1, alignment=ALEFT)

        live_name_label = self.create_label(tr('LiveParser Player:'), 'label_subhead')
        sec_1.addWidget(live_name_label, 11, 0, alignment=ARIGHT)
        live_player_combo = self.create_combo_box(style_override={'font': '@small_text'})
        live_player_combo.addItems(('Name', 'Handle'))
        live_player_combo.setCurrentText(self.settings.value('live_player', type=str))
        live_player_combo.currentTextChanged.connect(
                lambda new_text: self.settings.setValue('live_player', new_text))
        sec_1.addWidget(live_player_combo, 11, 1, alignment=ALEFT)

        overview_tab_label = self.create_label(tr('Default Overview Tab:'), 'label_subhead')
        sec_1.addWidget(overview_tab_label, 12, 0, alignment=ARIGHT)
        overview_tab_combo = self.create_combo_box(style_override={'font': '@small_text'})
        overview_tab_combo.addItems((tr('DPS Bar'), tr('DPS Graph'), tr('Damage Graph')))
        overview_tab_combo.setCurrentIndex(self.settings.value('first_overview_tab', type=int))
        overview_tab_combo.currentIndexChanged.connect(
            lambda new_index: self.settings.setValue('first_overview_tab', new_index))
        sec_1.addWidget(overview_tab_combo, 12, 1, alignment=ALEFT)

        ui_scale_label = self.create_label(tr('UI Scale:'), 'label_subhead')
        sec_1.addWidget(ui_scale_label, 13, 0, alignment=ARIGHT)
        ui_scale_slider_layout = self.create_annotated_slider(
                default_value=round(self.settings.value('ui_scale', type=float) * 50, 0),
                min=25, max=75, callback=self.set_ui_scale_setting)
        sec_1.addLayout(ui_scale_slider_layout, 13, 1, alignment=ALEFT)

        ui_scale_label = self.create_label(tr('LiveParser Scale:'), 'label_subhead')
        sec_1.addWidget(ui_scale_label, 14, 0, alignment=ARIGHT)
        live_scale_slider_layout = self.create_annotated_slider(
                default_value=round(self.settings.value('live_scale', type=float) * 50, 0),
                min=25, max=75, callback=self.set_live_scale_setting)
        sec_1.addLayout(live_scale_slider_layout, 14, 1, alignment=ALEFT)
        sec_1.setAlignment(AHCENTER)

        live_enabled_label = self.create_label(tr('LiveParser default state:'), 'label_subhead')
        sec_1.addWidget(live_enabled_label, 15, 0, alignment=ARIGHT)
        live_enabled_button = FlipButton(tr('Disabled'), tr('Enabled'), checkable=True)
        live_enabled_button.setStyleSheet(self.get_style_class(
                'QPushButton', 'toggle_button', override={'margin-top': 0, 'margin-left': 0}))
        live_enabled_button.setFont(self.theme_font('app', '@font'))
        live_enabled_button.r_function = (
                lambda: self.settings.setValue('live_enabled', True))
        live_enabled_button.l_function = (
                lambda: self.settings.setValue('live_enabled', False))
        if self.settings.value('live_enabled', type=bool):
            live_enabled_button.flip()
        sec_1.addWidget(live_enabled_button, 15, 1, alignment=ALEFT)

        result_format_label = self.create_label(tr('Result Clipboard Format:'), 'label_subhead')
        sec_1.addWidget(result_format_label, 16, 0, alignment=ARIGHT)
        result_format_combo = self.create_combo_box(style_override={'font': '@small_text'})
        result_format_combo.addItems(('Compact', 'Verbose', 'CSV'))
        result_format_combo.setCurrentText(self.settings.value('result_format', type=str))
        result_format_combo.currentTextChanged.connect(
                lambda new_text: self.settings.setValue('result_format', new_text))
        sec_1.addWidget(result_format_combo, 16, 1, alignment=ALEFT)

        languages = ('English',)  # 'Chinese', 'German')
        language_codes = ('en',)  # 'zh', 'de')
        language_label = self.create_label(tr('Language:'), 'label_subhead')
        sec_1.addWidget(language_label, 17, 0, alignment=ARIGHT)
        language_combo = self.create_combo_box(style_override={'font': '@small_text'})
        language_combo.addItems(languages)
        current_language_code = self.settings.value('language')
        language_combo.setCurrentText(languages[language_codes.index(current_language_code)])
        language_combo.currentIndexChanged.connect(
                lambda index: self.settings.setValue('language', language_codes[index]))
        sec_1.addWidget(language_combo, 17, 1, alignment=ALEFT | AVCENTER)
        scroll_layout.addLayout(sec_1)

        # seperator
        section_seperator = self.create_frame(
            'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
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
            tr('Damage table columns:'), 'label_subhead')
        sec_2.addWidget(dmg_hider_label)
        dmg_hider_layout = QVBoxLayout()
        dmg_hider_frame = self.create_frame(
                size_policy=SMINMAX, style_override=hider_frame_style_override)
        dmg_hider_frame.setMinimumWidth(self.sidebar_item_width)
        self.set_buttons = list()
        for i, head in enumerate(tr(TREE_HEADER)[1:]):
            bt = self.create_button(
                    head, 'toggle_button',
                    toggle=self.settings.value(f'dmg_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                    lambda state, i=i: self.settings.setValue(f'dmg_columns|{i}', state))
            dmg_hider_layout.addWidget(bt, stretch=1)
        dmg_seperator = self.create_frame(
                'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
        dmg_seperator.setFixedHeight(self.theme['defaults']['bw'])
        dmg_hider_layout.addWidget(dmg_seperator)
        apply_button = self.create_button(tr('Apply'), 'button')
        apply_button.clicked.connect(self.update_shown_columns_dmg)
        dmg_hider_layout.addWidget(apply_button, alignment=ARIGHT | ATOP)
        dmg_hider_frame.setLayout(dmg_hider_layout)
        sec_2.addWidget(dmg_hider_frame, alignment=ATOP)

        heal_hider_label = self.create_label(
                tr('Heal table columns:'), 'label_subhead')
        sec_2.addWidget(heal_hider_label)
        heal_hider_layout = QVBoxLayout()
        heal_hider_frame = self.create_frame(
                size_policy=SMINMAX, style_override=hider_frame_style_override)
        for i, head in enumerate(tr(HEAL_TREE_HEADER)[1:]):
            bt = self.create_button(
                    head, 'toggle_button',
                    toggle=self.settings.value(f'heal_columns|{i}', type=bool))
            bt.setSizePolicy(SMINMAX)
            bt.clicked[bool].connect(
                    lambda state, i=i: self.settings.setValue(f'heal_columns|{i}', state))
            heal_hider_layout.addWidget(bt, stretch=1)
        heal_seperator = self.create_frame(
            'hr', style_override={'background-color': '@lbg'}, size_policy=SMINMIN)
        heal_seperator.setFixedHeight(self.theme['defaults']['bw'])
        heal_hider_layout.addWidget(heal_seperator)
        apply_button_2 = self.create_button(tr('Apply'), 'button')
        apply_button_2.clicked.connect(self.update_shown_columns_heal)
        heal_hider_layout.addWidget(apply_button_2, alignment=ARIGHT | ATOP)
        heal_hider_frame.setLayout(heal_hider_layout)

        sec_2.addWidget(heal_hider_frame, alignment=ATOP)
        live_hider_label = self.create_label(
                tr('Live Parser columns:'), 'label_subhead')
        sec_2.addWidget(live_hider_label)
        live_hider_layout = QVBoxLayout()
        live_hider_frame = self.create_frame(
                size_policy=SMINMAX, style_override=hider_frame_style_override)
        for i, head in enumerate(tr(LIVE_TABLE_HEADER)):
            bt = self.create_button(
                    head, 'toggle_button',
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
