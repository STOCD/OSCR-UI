from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLineEdit, QListView, QListWidget, QListWidgetItem,
    QTabWidget, QVBoxLayout, QWidget)

from .config import OSCRConfig, OSCRSettings
from .dialogs import DetectionInfoDialog, DialogsWrapper
from .iofunctions import browse_path, open_link
from .parserbridge import ParserBridge
from .splitdialog import SplitDialog
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import (
    create_button2, create_button_series2, create_combo_box2, create_frame2, create_icon_button2,
    create_label2,
    ABOTTOM, AHCENTER, ALEFT, ARIGHT, ATOP, SMAXMIN, SMINMAX, SMINMIN, SMIXMAX, SMIXMIN)
from .widgetmanager import WidgetManager
from .widgets import CombatDelegate


class OSCRLeftSidebar():
    """Collapsible sidebar of the app"""

    def __init__(
            self, app_version: str, main_window: QWidget, parser: ParserBridge,
            detection_info: DetectionInfoDialog, dialogs: DialogsWrapper, widgets: WidgetManager,
            theme: AppTheme, config: OSCRConfig, settings: OSCRSettings):
        """
        Parameters:
        - :param app_version: version of the app for display on the sidebar
        - :param main_window: primary window of the app
        - :param parser: ParserBridge
        - :param detection_info: DetectionInfoDialog
        - :param dialogs: DialogsWrapper
        - :param widgets: WidgetManager
        - :param theme: AppTheme
        - :param config: OSCRConfig
        - :param settings: OSCRSettings
        """
        self._app_version: str = app_version
        self._parser: ParserBridge = parser
        self._detection_info: DetectionInfoDialog = detection_info
        self._dialogs: DialogsWrapper = dialogs
        self._widgets: WidgetManager = widgets
        self._theme: AppTheme = theme
        self._config: OSCRConfig = config
        self._settings: OSCRSettings = settings
        self._split_dialog: SplitDialog = SplitDialog(main_window, parser, dialogs, theme)
        self._log_path_widget: QLineEdit

    def create_sidebar(self, parent_frame: QFrame):
        """
        Creates sidebar(s) in given frame.

        Parameters:
        - :param parent_frame: frame that contains sidebar
        """
        log_frame = create_frame2(self._theme, style='medium_frame', size_policy=SMINMIN)
        league_frame = create_frame2(self._theme, style='medium_frame', size_policy=SMINMIN)
        about_frame = create_frame2(self._theme, style='medium_frame', size_policy=SMINMIN)
        sidebar_tabber = QTabWidget(parent_frame)
        sidebar_tabber.setStyleSheet(self._theme.get_style_class('QTabWidget', 'tabber'))
        sidebar_tabber.tabBar().hide()
        sidebar_tabber.setSizePolicy(SMAXMIN)
        sidebar_tabber.addTab(log_frame, tr('Log'))
        sidebar_tabber.addTab(league_frame, tr('League'))
        sidebar_tabber.addTab(about_frame, tr('About'))
        self._widgets.sidebar_tabber = sidebar_tabber
        self._widgets.sidebar_tab_frames.append(log_frame)
        self._widgets.sidebar_tab_frames.append(league_frame)
        self._widgets.sidebar_tab_frames.append(about_frame)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar_tabber)
        parent_frame.setLayout(layout)

        self.setup_left_sidebar_log(log_frame)
        self.setup_left_sidebar_league(league_frame)
        self.setup_left_sidebar_about(about_frame)

    def browse_log(self):
        """
        Callback for browse button.
        """
        current_path = Path(self._log_path_widget.text()).absolute().parent
        path = browse_path(current_path, 'Logfile (*.log);;Any File (*.*)')
        if path is not None:
            self._log_path_widget.setText(str(path))
            if self._settings.auto_scan:
                self._parser.analyze_log_file(str(path))

    def setup_left_sidebar_log(self, parent_frame: QFrame):
        """
        Sets up the log management tab of the left sidebar.

        Parameters:
        - :param parent_frame: frame that contains log management
        """
        margin = self._theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(margin, margin, margin, margin)
        left_layout.setSpacing(0)
        left_layout.setAlignment(ATOP)

        head_layout = QHBoxLayout()
        head = create_label2(self._theme, tr('STO Combatlog:'), 'label_heading')
        head_layout.addWidget(head, alignment=ALEFT | ABOTTOM)
        split_log_button = create_icon_button2(self._theme, 'edit', tr('Manage Logfile'))
        split_log_button.clicked.connect(
            lambda: self._split_dialog.show_dialog(self._log_path_widget.text()))
        head_layout.addWidget(split_log_button, alignment=ARIGHT)
        left_layout.addLayout(head_layout)

        self._log_path_widget = QLineEdit(self._settings.log_path)
        self._log_path_widget.setStyleSheet(self._theme.get_style_class('QLineEdit', 'entry'))
        self._log_path_widget.setFont(self._theme.get_font('entry'))
        self._log_path_widget.setSizePolicy(SMIXMAX)
        left_layout.addWidget(self._log_path_widget)

        entry_button_config = {
            tr('Browse ...'): {
                'callback': self.browse_log, 'align': ALEFT,
                'style': {'margin-left': 0}
            },
            tr('Default'): {
                'callback': lambda: self._log_path_widget.setText(self._settings.sto_log_path),
                'align': AHCENTER
            },
            tr('Analyze'): {
                'callback': lambda: self._parser.analyze_log_file(
                    Path(self._log_path_widget.text())),
                'align': ARIGHT, 'style': {'margin-right': 0}
            }
        }
        entry_buttons = create_button_series2(self._theme, entry_button_config, 'button')
        entry_buttons.setContentsMargins(0, 0, 0, margin)
        left_layout.addLayout(entry_buttons)

        background_frame = create_frame2(self._theme, size_policy=SMINMIN, style_override={
                'border-radius': self._theme['listbox']['border-radius'], 'margin-top': '@csp',
                'margin-bottom': '@csp'})
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        combats_list = QListView(background_frame)
        combats_list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        combats_list.setStyleSheet(self._theme.get_style_class('QListView', 'listbox'))
        combats_list.setFont(self._theme.get_font('listbox'))
        combats_list.setAlternatingRowColors(True)
        combats_list.setSizePolicy(SMIXMIN)
        combats_list.setModel(self._parser.analyzed_combats)
        border_width = 1 * self._theme.scale
        padding = 4 * self._theme.scale
        combats_list.setItemDelegate(CombatDelegate(border_width, padding))
        combats_list.doubleClicked.connect(
            lambda: self._parser.show_combat(combats_list.currentIndex().data()[0]))
        background_layout.addWidget(combats_list)
        self._widgets.combats_list = combats_list
        left_layout.addWidget(background_frame, stretch=1)

        combat_button_row = QGridLayout()
        combat_button_row.setContentsMargins(0, 0, 0, 0)
        combat_button_row.setSpacing(self._theme['defaults']['csp'])
        combat_button_row.setColumnStretch(3, 1)
        export_button = create_icon_button2(self._theme, 'export-parse', tr('Export Combat'))
        combat_button_row.addWidget(export_button, 0, 0)
        more_combats_button = create_icon_button2(
            self._theme, 'parser-down', tr('Parse Older Combats'))
        combat_button_row.addWidget(more_combats_button, 0, 1)
        json_export_button = create_icon_button2(
            self._theme, 'json', tr('Export Combat to JSON File'))
        combat_button_row.addWidget(json_export_button, 0, 2)
        left_layout.addLayout(combat_button_row)
        more_combats_button.clicked.connect(self._parser.analyze_log_background)
        export_button.clicked.connect(
                lambda: self._parser.save_combat(combats_list.currentIndex().data()))
        json_export_button.clicked.connect(
                lambda: self._parser.export_combat_json(combats_list.currentIndex().data()))

        sep = create_frame2(self._theme, 'medium_frame')
        sep.setFixedHeight(margin)
        left_layout.addWidget(sep)
        log_layout = QHBoxLayout()
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(margin)
        log_layout.setAlignment(ALEFT)
        player_duration_label = create_label2(self._theme, tr('Log Duration:'))
        log_layout.addWidget(player_duration_label)
        self._widgets.log_duration_value = create_label2(self._theme, '')
        log_layout.addWidget(self._widgets.log_duration_value)
        left_layout.addLayout(log_layout)
        player_layout = QHBoxLayout()
        player_layout.setContentsMargins(0, 0, 0, 0)
        player_layout.setSpacing(margin)
        player_layout.setAlignment(ALEFT)
        player_duration_label = create_label2(self._theme, tr('Active Player Duration:'))
        player_layout.addWidget(player_duration_label)
        self._widgets.player_duration_value = create_label2(self._theme, '')
        player_layout.addWidget(self._widgets.player_duration_value)
        left_layout.addLayout(player_layout)
        detection_button = create_button2(self._theme, tr('Map Detection Details'))
        detection_button.clicked.connect(self.show_detection_info)
        left_layout.addWidget(detection_button, alignment=AHCENTER)

        parent_frame.setLayout(left_layout)

    def setup_left_sidebar_league(self, parent_frame: QFrame):
        """
        Sets up the league table management tab of the left sidebar

        Parameters:
        - :param parent_frame: frame that contains league table sidebar
        """
        m = self._theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(self._theme['defaults']['csp'])
        left_layout.setAlignment(ATOP)

        map_layout = QHBoxLayout()
        map_label = create_label2(self._theme, tr('Available Maps:'), 'label_heading')
        map_layout.addWidget(map_label, alignment=ALEFT | ABOTTOM)
        fav_add_button = create_icon_button2(self._theme, 'star-plus', tr('Add to Favorites'))
        # fav_add_button.clicked.connect(self.add_favorite_ladder)
        map_layout.addWidget(fav_add_button, alignment=ARIGHT)
        left_layout.addLayout(map_layout)

        variant_list = create_combo_box2(self._theme)
        # variant_list.currentTextChanged.connect(lambda text: self.update_seasonal_records(text))
        left_layout.addWidget(variant_list)
        self._widgets.variant_combo = variant_list

        background_frame = create_frame2(self._theme, size_policy=SMINMIN, style_override={
                'border-radius': self._theme['listbox']['border-radius']})
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        ladder_selector = QListWidget()
        ladder_selector.setStyleSheet(self._theme.get_style_class('QListWidget', 'listbox'))
        ladder_selector.setFont(self._theme.get_font('listbox'))
        ladder_selector.setSizePolicy(SMIXMIN)
        ladder_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self._widgets.ladder_selector = ladder_selector
        # ladder_selector.itemClicked.connect(
        #         lambda clicked_item: self.slot_ladder(clicked_item))
        background_layout.addWidget(ladder_selector)
        left_layout.addWidget(background_frame, stretch=3)

        fav_layout = QHBoxLayout()
        favorites_label = create_label2(self._theme, tr('Favorites:'), 'label_heading')
        fav_layout.addWidget(favorites_label, alignment=ALEFT | ABOTTOM)
        fav_add_button = create_icon_button2(self._theme, 'star-minus', tr('Add to Favorites'))
        # fav_add_button.clicked.connect(self.remove_favorite_ladder)
        fav_layout.addWidget(fav_add_button, alignment=ARIGHT)
        left_layout.addLayout(fav_layout)

        background_frame = create_frame2(self._theme, size_policy=SMINMIN, style_override={
                'border-radius': self._theme['listbox']['border-radius']})
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        favorite_selector = QListWidget(background_frame)
        favorite_selector.setStyleSheet(self._theme.get_style_class('QListWidget', 'listbox'))
        favorite_selector.setFont(self._theme.get_font('listbox'))
        favorite_selector.setSizePolicy(SMIXMIN)
        favorite_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self._widgets.favorite_ladder_selector = favorite_selector
        for favorite_ladder in self._settings.favorite_ladders:
            if '|' not in favorite_ladder:
                self._settings.favorite_ladders = list()
                break
            ladder_text, difficulty = favorite_ladder.split('|')
            if difficulty == 'None':
                difficulty = None
            item = QListWidgetItem(ladder_text)
            item.difficulty = difficulty
            if difficulty != 'Any' and difficulty is not None:
                icon = self._theme.icons[f'TFO-{difficulty.lower()}']
                icon.addPixmap(icon.pixmap(18, 24), QIcon.Mode.Selected)
                item.setIcon(icon)
            favorite_selector.addItem(item)
        # favorite_selector.itemClicked.connect(
        #         lambda clicked_item: self.slot_ladder(clicked_item))
        background_layout.addWidget(favorite_selector)
        left_layout.addWidget(background_frame, stretch=2)

        ladder_selector.itemClicked.connect(favorite_selector.clearSelection)
        favorite_selector.itemClicked.connect(ladder_selector.clearSelection)

        parent_frame.setLayout(left_layout)

    def setup_left_sidebar_about(self, parent_frame: QFrame):
        """
        Sets up the about tab of the left sidebar

        Parameters:
        - :param parent_frame: frame that contains league table sidebar
        """
        m = self._theme['defaults']['margin']
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(m, m, m, m)
        left_layout.setSpacing(m)
        left_layout.setAlignment(ATOP)

        head_label = create_label2(self._theme, tr('About OSCR:'), 'label_heading')
        left_layout.addWidget(head_label)
        about_label = create_label2(self._theme, tr(
            'Open Source Combatlog Reader (OSCR), developed by the STO Community Developers in '
            'cooperation with the STO Builds Discord.'))
        about_label.setWordWrap(True)
        about_label.setMinimumWidth(50)  # to fix the word wrap
        about_label.setSizePolicy(SMINMAX)
        left_layout.addWidget(about_label)
        link_button_style = {
            'default': {},
            tr('Website'): {
                'callback': lambda: open_link(self._config.link_website), 'align': AHCENTER},
            tr('Github'): {
                'callback': lambda: open_link(self._config.link_github), 'align': AHCENTER},
            tr('Downloads'): {
                'callback': lambda: open_link(self._config.link_downloads), 'align': AHCENTER}
        }
        button_layout, buttons = create_button_series2(
                self._theme, link_button_style, 'button', shape='column', ret=True)
        buttons[0].setToolTip(self._config.link_website)
        buttons[1].setToolTip(self._config.link_github)
        buttons[2].setToolTip(self._config.link_downloads)
        link_button_frame = create_frame2(self._theme, 'medium_frame')
        link_button_frame.setLayout(button_layout)
        left_layout.addWidget(link_button_frame, alignment=AHCENTER)
        seperator = create_frame2(self._theme, 'light_frame', size_policy=SMINMAX)
        seperator.setFixedHeight(1)
        left_layout.addWidget(seperator)
        version_label = create_label2(
            self._theme, f"{tr('Version')}: {self._app_version}", 'label_subhead')
        left_layout.addWidget(version_label)
        logo_layout = QGridLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setColumnStretch(1, 1)
        logo_size = [self._theme.opt.icon_size * 4] * 2
        stocd_logo = create_icon_button2(
            self._theme, 'stocd', self._config.link_stocd,
            style_override={'border-style': 'none'}, icon_size=logo_size)
        stocd_logo.clicked.connect(lambda: open_link(self._config.link_stocd))
        logo_layout.addWidget(stocd_logo, 0, 0)
        stobuilds_logo = create_icon_button2(
            self._theme, 'stobuilds', self._config.link_stobuilds,
            style_override={'border-style': 'none'}, icon_size=logo_size)
        stobuilds_logo.clicked.connect(lambda: open_link(self._config.link_stobuilds))
        logo_layout.addWidget(stobuilds_logo, 0, 2)
        logo_frame = create_frame2(self._theme, 'medium_frame', size_policy=SMINMAX)
        logo_frame.setLayout(logo_layout)
        left_layout.addWidget(logo_frame, stretch=1, alignment=ABOTTOM)
        parent_frame.setLayout(left_layout)

    def show_detection_info(self):
        """
        Shows detection info dialog
        """
        current_combat_meta = self._parser.current_combat_meta()
        if current_combat_meta is not None:
            self._detection_info.show_dialog(current_combat_meta['detection_info'])
