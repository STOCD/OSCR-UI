import copy
from signal import signal, SIGINT, SIG_DFL
import json
from multiprocessing import Lock
import os

from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QFrame, QListWidget, QTabWidget, QTableView
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import QSize, QSettings

from OSCR import TREE_HEADER, HEAL_TREE_HEADER

from .iofunctions import load_icon_series, get_asset_path, load_icon
from .textedit import format_path
from .widgets import BannerLabel, FlipButton, WidgetStorage
from .widgetbuilder import SMAXMAX, SMAXMIN, SMINMAX, SMINMIN, ALEFT, ARIGHT, ATOP, ACENTER, AHCENTER
from .leagueconnector import OSCRClient

# only for developing; allows to terminate the qt event loop with keyboard interrupt
signal(SIGINT, SIG_DFL)

class OSCRUI():

    from .datafunctions import init_parser, copy_summary_callback
    from .datafunctions import analyze_log_callback, update_shown_columns_dmg, update_shown_columns_heal
    from .iofunctions import browse_path
    from .style import get_style_class, create_style_sheet, theme_font
    from .widgetbuilder import create_frame, create_label, create_button_series, create_icon_button
    from .widgetbuilder import create_analysis_table, create_button, create_combo_box, style_table
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
            'refresh': 'refresh-cw.svg'
        }
        self.icons = load_icon_series(icons, self.app_dir)

    def init_settings(self):
        """
        Prepares settings. Loads stored settings. Saves current settings for next startup.
        """
        settings_path = os.path.abspath(f'{self.app_dir}/{self.config["settings_path"]}')
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

        left = self.create_frame(main_frame, 'medium_frame')
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
        self.setup_left_sidebar(left)
        self.setup_main_tabber(center)
        self.setup_overview_frame()
        self.setup_analysis_frame()
        self.setup_league_standings_frame()
        self.setup_settings_frame()

    def setup_left_sidebar(self, frame:QFrame):
        """
        Sets up the sidebar used to select parses and combats

        Parameters:
        - :param frame: QFrame -> parent frame of the sidebar
        """
        left_layout = QVBoxLayout()
        m = self.theme['defaults']['margin']
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        head = self.create_label('STO Combatlog:', 'label', frame)
        left_layout.addWidget(head, alignment=ALEFT)

        self.entry = QLineEdit(self.settings.value('log_path', ''), frame)
        self.entry.setStyleSheet(self.get_style_class('QLineEdit', 'entry'))
        self.entry.setFixedWidth(self.sidebar_item_width)
        left_layout.addWidget(self.entry)
        
        button_frame = self.create_frame(frame, 'medium_frame')
        button_frame.setSizePolicy(SMINMAX)
        entry_button_config = {
            'default': {'margin-bottom': '@isp'},
            'Browse ...': {'callback': lambda: self.browse_log(self.entry), 'align': ALEFT},
            'Analyze': {'callback': lambda: self.analyze_log_callback(path=self.entry.text()), 'align': ARIGHT}
        }
        entry_buttons = self.create_button_series(button_frame, entry_button_config, 'button')
        button_frame.setLayout(entry_buttons)
        left_layout.addWidget(button_frame)

        refresh_button = self.create_icon_button(self.icons['refresh'], 'icon_button', frame)
        left_layout.addWidget(refresh_button, alignment=ARIGHT)

        background_frame = self.create_frame(frame, 'light_frame', 
                {'border-radius': self.theme['listbox']['border-radius']})
        background_frame.setSizePolicy(SMAXMIN)
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
        
        refresh_button.clicked.connect(lambda: self.analyze_log_callback(self.current_combats.currentRow()))

        frame.setLayout(left_layout)

    def setup_main_tabber(self, frame:QFrame):
        """
        Sets up the tabber switching between Overview, Analysis, League and Settings.

        Parameters:
        - :param frame: QFrame -> parent frame of the sidebar
        """
        o_frame = self.create_frame(None, 'frame')
        a_frame = self.create_frame(None, 'frame')
        l_frame = self.create_frame(None, 'frame')
        s_frame = self.create_frame(None, 'frame')

        main_tabber = QTabWidget(frame)
        main_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        main_tabber.tabBar().setStyleSheet(self.get_style_class( 'QTabBar', 'tabber_tab'))
        main_tabber.setSizePolicy(SMINMIN)
        main_tabber.addTab(o_frame, 'O')
        main_tabber.addTab(a_frame, 'A')
        main_tabber.addTab(l_frame, 'L')
        main_tabber.addTab(s_frame, 'S')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_tabber)
        frame.setLayout(layout)

        self.widgets.main_menu_buttons[0].clicked.connect(lambda: main_tabber.setCurrentIndex(0))
        self.widgets.main_menu_buttons[1].clicked.connect(lambda: main_tabber.setCurrentIndex(1))
        self.widgets.main_menu_buttons[2].clicked.connect(lambda: main_tabber.setCurrentIndex(2))
        self.widgets.main_menu_buttons[2].clicked.connect(lambda: self.establish_league_connection(True))
        self.widgets.main_menu_buttons[3].clicked.connect(lambda: main_tabber.setCurrentIndex(3))
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

        switch_frame = self.create_frame(o_frame, 'frame')
        layout.addWidget(switch_frame, alignment=ACENTER)

        o_tabber = QTabWidget(o_frame)
        o_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        o_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
        o_tabber.addTab(bar_frame, 'BAR')
        o_tabber.addTab(dps_graph_frame, 'DPS')
        o_tabber.addTab(dmg_graph_frame, 'DMG')
        layout.addWidget(o_tabber)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            'DPS Bar': {'callback': lambda: o_tabber.setCurrentIndex(0), 'align':ACENTER},
            'DPS Graph': {'callback': lambda: o_tabber.setCurrentIndex(1), 'align':ACENTER},
            'Damage Graph': {'callback': lambda: o_tabber.setCurrentIndex(2), 'align':ACENTER},
            'Copy Summary': {'callback': self.copy_summary_callback, 'align':ACENTER},
            'Upload Result': {'callback': self.upload_callback, 'align':ACENTER},
        }
        switcher, buttons = self.create_button_series(switch_frame, switch_style, 'button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        self.widgets.overview_menu_buttons = buttons
        switch_frame.setLayout(switcher)
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

        switch_frame = self.create_frame(a_frame, 'frame')
        layout.addWidget(switch_frame, alignment=ACENTER)
        
        a_tabber = QTabWidget(a_frame)
        a_tabber.setStyleSheet(self.get_style_class('QTabWidget', 'tabber'))
        a_tabber.tabBar().setStyleSheet(self.get_style_class('QTabBar', 'tabber_tab'))
        a_tabber.addTab(dout_frame, 'DOUT')
        a_tabber.addTab(dtaken_frame, 'DTAKEN')
        a_tabber.addTab(hout_frame, 'HOUT')
        a_tabber.addTab(hin_frame, 'HIN')
        self.widgets.analysis_tabber = a_tabber
        layout.addWidget(a_tabber)

        switch_style = {
            'default': {'margin-left': '@margin', 'margin-right': '@margin'},
            'Damage Out': {'callback': lambda: a_tabber.setCurrentIndex(0), 'align':ACENTER},
            'Damage Taken': {'callback': lambda: a_tabber.setCurrentIndex(1), 'align':ACENTER},
            'Heals Out': {'callback': lambda: a_tabber.setCurrentIndex(2), 'align':ACENTER},
            'Heals In': {'callback': lambda: a_tabber.setCurrentIndex(3), 'align':ACENTER}
        }
        switcher, buttons = self.create_button_series(switch_frame, switch_style, 'button', ret=True)
        switcher.setContentsMargins(0, self.theme['defaults']['margin'], 0, 0)
        self.widgets.analysis_menu_buttons = buttons
        switch_frame.setLayout(switcher)

        tabs = (
            (dout_frame, 'analysis_table_dout'), 
            (dtaken_frame, 'analysis_table_dtaken'),
            (hout_frame, 'analysis_table_hout'),
            (hin_frame, 'analysis_table_hin')
        )
        for tab, name in tabs:
            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(0)

            #graph

            tree = self.create_analysis_table(tab, 'tree_table')
            tab_layout.addWidget(tree)
            setattr(self.widgets, name, tree)
            tab.setLayout(tab_layout)
        
        a_frame.setLayout(layout)

    def setup_league_standings_frame(self):
        """
        Sets up the frame housing the detailed analysis table and graph
        """
        l_frame = self.widgets.main_tab_frames[2]
        layout = QVBoxLayout()
        margin = self.theme['defaults']['margin']
        layout.setContentsMargins(0, 0, 0, margin)
        layout.setSpacing(0)

        spacing = self.theme['defaults']['isp']
        control_frame = self.create_frame(l_frame)
        control_frame_layout = QHBoxLayout()
        control_frame_layout.setContentsMargins(margin, margin, margin, margin)
        control_frame_layout.setSpacing(spacing)

        map_selector = self.create_combo_box(control_frame)
        map_selector.addItem("Select a League")
        self.widgets.ladder_map = map_selector
        map_selector.currentIndexChanged.connect(lambda new_index: self.update_ladder_index(new_index))
        control_frame_layout.addWidget(map_selector)
        control_frame.setLayout(control_frame_layout)

        ladder_table = QTableView(l_frame)
        self.style_table(ladder_table)
        self.widgets.ladder_table = ladder_table

        layout.addWidget(control_frame, alignment=AHCENTER)
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
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(0)

        col_1_frame = self.create_frame(settings_frame)
        col_1_frame.setSizePolicy(SMINMAX)
        settings_layout.addWidget(col_1_frame, alignment=ATOP, stretch=1)
        col_2_frame = self.create_frame(settings_frame)
        col_2_frame.setSizePolicy(SMINMAX)
        settings_layout.addWidget(col_2_frame, alignment=ATOP, stretch=1)
        col_3_frame = self.create_frame(settings_frame)
        col_3_frame.setSizePolicy(SMINMAX)
        settings_layout.addWidget(col_3_frame, alignment=ATOP, stretch=1)

        col_1 = QVBoxLayout()
        col_1.setSpacing(0)
        dmg_hider_label = self.create_label('Damage table columns:', 'label', col_1_frame)
        col_1.addWidget(dmg_hider_label)
        dmg_hider_layout = QVBoxLayout()
        dmg_hider_frame = self.create_frame(col_1_frame, style_override=
                {'border-color':'@lbg', 'border-width':'@bw', 'border-style':'solid', 'border-radius': 2})
        dmg_hider_frame.setSizePolicy(SMINMAX)
        for i, head in enumerate(TREE_HEADER[1:]):
            bt = self.create_button(head, 'toggle_button', dmg_hider_frame)
            bt.setCheckable(True)
            bt.setSizePolicy(SMINMAX)
            bt.setChecked(self.settings.value(f'dmg_columns|{i}', type=bool))
            bt.clicked.connect(lambda state, i=i: self.settings.setValue(f'dmg_columns|{i}', state))
            dmg_hider_layout.addWidget(bt, stretch=1)
        dmg_hider_frame.setLayout(dmg_hider_layout)
        col_1.addWidget(dmg_hider_frame, alignment=ATOP)
        apply_button = self.create_button('Apply', 'button', col_1_frame, {'margin-top':15})
        apply_button.clicked.connect(self.update_shown_columns_dmg)
        col_1.addWidget(apply_button, alignment=ALEFT)
        col_1_frame.setLayout(col_1)

        col_2 = QVBoxLayout()
        col_2.setSpacing(0)
        heal_hider_label = self.create_label('Heal table columns:', 'label', col_2_frame)
        col_2.addWidget(heal_hider_label)
        heal_hider_layout = QVBoxLayout()
        heal_hider_frame = self.create_frame(col_2_frame, style_override=
                {'border-color':'@lbg', 'border-width':'@bw', 'border-style':'solid', 'border-radius': 2})
        heal_hider_frame.setSizePolicy(SMINMAX)
        for i, head in enumerate(HEAL_TREE_HEADER[1:]):
            bt = self.create_button(head, 'toggle_button', heal_hider_frame)
            bt.setCheckable(True)
            bt.setSizePolicy(SMINMAX)
            bt.setChecked(self.settings.value(f'heal_columns|{i}', type=bool))
            bt.clicked.connect(lambda state, i=i: self.settings.setValue(f'heal_columns|{i}', state))
            heal_hider_layout.addWidget(bt, stretch=1)
        heal_hider_frame.setLayout(heal_hider_layout)
        col_2.addWidget(heal_hider_frame, alignment=ATOP)
        apply_button_2 = self.create_button('Apply', 'button', col_2_frame, {'margin-top':15})
        apply_button_2.clicked.connect(self.update_shown_columns_heal)
        col_2.addWidget(apply_button_2, alignment=ALEFT)
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

    def set_variable(self, var_to_be_set, index, value):
        """
        Assigns value at index to variable
        """
        var_to_be_set[index] = value
