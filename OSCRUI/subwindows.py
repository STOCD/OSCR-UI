import os

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QIntValidator, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QDialog
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLineEdit
from PySide6.QtWidgets import QMessageBox, QSpacerItem, QTableView, QWidget
from PySide6.QtWidgets import QVBoxLayout

from OSCR import LiveParser, LIVE_TABLE_HEADER
from .callbacks import auto_split_callback, combat_split_callback, copy_live_data_callback
from .displayer import create_live_graph, update_live_display
from .datamodels import LiveParserTableModel
from .style import get_style, get_style_class, theme_font
from .textedit import format_path
from .widgetbuilder import create_button, create_frame, create_icon_button, create_label
from .widgetbuilder import ABOTTOM, ALEFT, ARIGHT, AVCENTER, RFIXED
from .widgetbuilder import SEXPAND, SMAX, SMAXMAX, SMINMIN
from .widgets import FlipButton, SizeGrip


def show_warning(self, title: str, message: str):
    """
    Displays a warning in form of a message box

    Parameters:
    - :param title: title of the warning
    - :param message: message to be displayed
    """
    error = QMessageBox()
    error.setIcon(QMessageBox.Icon.Warning),
    error.setText(message)
    error.setWindowTitle(title)
    error.setStandardButtons(QMessageBox.StandardButton.Ok)
    error.setWindowIcon(self.icons['oscr'])
    error.exec()


def log_size_warning(self):
    """
    Warns user about oversized logfile.

    :return: "cancel", "split dialog", "continue"
    """
    dialog = QMessageBox()
    dialog.setIcon(QMessageBox.Icon.Warning)
    message = (
            'The combatlog file you are trying to open will impair the performance of the app '
            'due to its size. It is advised to split the log. \n\nClick "Split Dialog" to split '
            'the file, "Cancel" to abort combatlog analysis or "Continue" to analyze the log '
            'nevertheless.')
    dialog.setText(message)
    dialog.setWindowTitle('Open Source Combalog Reader')
    dialog.setWindowIcon(self.icons['oscr'])
    dialog.addButton('Cancel', QMessageBox.ButtonRole.RejectRole)
    default_button = dialog.addButton('Split Dialog', QMessageBox.ButtonRole.ActionRole)
    dialog.addButton('Continue', QMessageBox.ButtonRole.AcceptRole)
    dialog.setDefaultButton(default_button)
    clicked = dialog.exec()
    if clicked == 1:
        return 'split dialog'
    elif clicked == 2:
        return 'continue'
    else:
        return 'cancel'


def split_dialog(self):
    """
    Opens dialog to split the current logfile.
    """
    main_layout = QVBoxLayout()
    thick = self.theme['app']['frame_thickness']
    item_spacing = self.theme['defaults']['isp']
    main_layout.setContentsMargins(thick, thick, thick, thick)
    content_frame = create_frame(self)
    main_layout.addWidget(content_frame)
    current_logpath = self.entry.text()
    vertical_layout = QVBoxLayout()
    vertical_layout.setContentsMargins(thick, thick, thick, thick)
    vertical_layout.setSpacing(item_spacing)
    log_layout = QHBoxLayout()
    log_layout.setContentsMargins(0, 0, 0, 0)
    log_layout.setSpacing(item_spacing)
    current_log_heading = create_label(self, 'Selected Logfile:', 'label_subhead')
    log_layout.addWidget(current_log_heading, alignment=ALEFT)
    current_log_label = create_label(self, format_path(current_logpath), 'label')
    log_layout.addWidget(current_log_label, alignment=AVCENTER)
    log_layout.addSpacerItem(QSpacerItem(1, 1, hData=SEXPAND, vData=SMAX))
    vertical_layout.addLayout(log_layout)
    seperator_1 = create_frame(self, content_frame, 'hr', size_policy=SMINMIN)
    seperator_1.setFixedHeight(self.theme['hr']['height'])
    vertical_layout.addWidget(seperator_1)
    grid_layout = QGridLayout()
    grid_layout.setContentsMargins(0, 0, 0, 0)
    grid_layout.setVerticalSpacing(0)
    grid_layout.setHorizontalSpacing(item_spacing)
    vertical_layout.addLayout(grid_layout)
    auto_split_heading = create_label(self, 'Split Log Automatically:', 'label_heading')
    grid_layout.addWidget(auto_split_heading, 0, 0, alignment=ALEFT)
    label_text = (
            'Automatically splits the logfile at the next combat end after '
            f'{self.settings.value("split_log_after", type=int):,} lines until the entire file has '
            ' been split. The new files are written to the selected folder. It is advised to '
            'select an empty folder to ensure all files are saved correctly.')
    auto_split_text = create_label(self, label_text, 'label')
    auto_split_text.setWordWrap(True)
    auto_split_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(auto_split_text, 1, 0, alignment=ALEFT)
    auto_split_button = create_button(self, 'Auto Split')
    auto_split_button.clicked.connect(lambda: auto_split_callback(self, current_logpath))
    grid_layout.addWidget(auto_split_button, 1, 2, alignment=ARIGHT | ABOTTOM)
    grid_layout.setRowMinimumHeight(2, item_spacing)
    seperator_3 = create_frame(self, content_frame, 'hr', size_policy=SMINMIN)
    seperator_3.setFixedHeight(self.theme['hr']['height'])
    grid_layout.addWidget(seperator_3, 3, 0, 1, 3)
    grid_layout.setRowMinimumHeight(4, item_spacing)
    range_split_heading = create_label(self, 'Export Range of Combats:', 'label_heading')
    grid_layout.addWidget(range_split_heading, 5, 0, alignment=ALEFT)
    label_text = (
            'Exports combats including and between lower and upper limit to selected file. '
            'Both limits refer to the indexed list of all combats in the file starting with 1. '
            'An upper limit larger than the total number of combats or of "-1", is treated as '
            'being equal to the total number of combats.')
    range_split_text = create_label(self, label_text, 'label')
    range_split_text.setWordWrap(True)
    range_split_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(range_split_text, 6, 0, alignment=ALEFT)
    range_limit_layout = QGridLayout()
    range_limit_layout.setContentsMargins(0, 0, 0, 0)
    range_limit_layout.setSpacing(0)
    range_limit_layout.setRowStretch(0, 1)
    lower_range_label = create_label(self, 'Lower Limit:', 'label')
    range_limit_layout.addWidget(lower_range_label, 1, 0, alignment=AVCENTER)
    upper_range_label = create_label(self, 'Upper Limit:', 'label')
    range_limit_layout.addWidget(upper_range_label, 2, 0, alignment=AVCENTER)
    lower_range_entry = QLineEdit()
    lower_validator = QIntValidator()
    lower_validator.setBottom(1)
    lower_range_entry.setValidator(lower_validator)
    lower_range_entry.setText('1')
    lower_range_entry.setStyleSheet(
            get_style(self, 'entry', {'margin-top': 0, 'margin-left': '@csp'}))
    lower_range_entry.setFixedWidth(self.sidebar_item_width // 7)
    range_limit_layout.addWidget(lower_range_entry, 1, 1, alignment=AVCENTER)
    upper_range_entry = QLineEdit()
    upper_validator = QIntValidator()
    upper_validator.setBottom(-1)
    upper_range_entry.setValidator(upper_validator)
    upper_range_entry.setText('1')
    upper_range_entry.setStyleSheet(
            get_style(self, 'entry', {'margin-top': 0, 'margin-left': '@csp'}))
    upper_range_entry.setFixedWidth(self.sidebar_item_width // 7)
    range_limit_layout.addWidget(upper_range_entry, 2, 1, alignment=AVCENTER)
    grid_layout.addLayout(range_limit_layout, 6, 1)
    range_split_button = create_button(self, 'Export Combats')
    range_split_button.clicked.connect(
            lambda le=lower_range_entry, ue=upper_range_entry:
            combat_split_callback(self, current_logpath, le.text(), ue.text()))
    grid_layout.addWidget(range_split_button, 6, 2, alignment=ARIGHT | ABOTTOM)

    content_frame.setLayout(vertical_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle('OSCR - Split Logfile')
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.exec()


def live_parser_toggle(self, activate):
    """
    Activates / Deactivates LiveParser.

    Parameters:
    - :param activate: True when parser should be shown; False when open parser should be closed.
    """
    if activate:
        log_path = self.settings.value('sto_log_path')
        if not log_path or not os.path.isfile(log_path):
            show_warning(
                    self, 'Invalid Logfile', 'Make sure to set the STO Logfile setting in the '
                    'settings tab to a valid logfile before starting the live parser.')
            self.widgets.live_parser_button.setChecked(False)
            return
        FIELD_INDEX_CONVERSION = {0: 0, 1: 2, 2: 3, 3: 4}
        graph_active = self.settings.value('live_graph_active', type=bool)
        data_buffer = []
        data_field = FIELD_INDEX_CONVERSION[self.settings.value('live_graph_field', type=int)]
        self.live_parser = LiveParser(log_path, update_callback=lambda data: update_live_display(
                self, data, graph_active, data_buffer, data_field))
        create_live_parser_window(self)
    else:
        try:
            self.live_parser_window.close()
        except AttributeError:
            pass
        try:
            self.live_parser.stop()
        except AttributeError:
            pass
        self.live_parser_window = None
        self.live_parser = None
        self.widgets.live_parser_table = None
        self.widgets.live_parser_button.setChecked(False)


def create_live_parser_window(self):
    live_window = QWidget()
    live_window.setStyleSheet(self.get_style('live_parser'))
    live_window.setWindowFlags(
            live_window.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.SubWindow
            | Qt.WindowType.FramelessWindowHint)
    # live_window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
    live_window.setWindowOpacity(self.settings.value('live_parser_opacity', type=float))
    if self.settings.value('live_geometry'):
        live_window.restoreGeometry(self.settings.value('live_geometry'))
    live_window.closeEvent = lambda close_event: live_parser_close_callback(self, close_event)
    live_window.mousePressEvent = lambda press_event: live_parser_press_event(self, press_event)
    live_window.mouseMoveEvent = lambda move_event: live_parser_move_event(self, move_event)
    live_window.setSizePolicy(SMAXMAX)
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    graph_colors = None
    graph_column = None
    if self.settings.value('live_graph_active', type=bool):
        graph_frame, curves = create_live_graph(self)
        layout.addWidget(graph_frame, stretch=1)
        self.widgets.live_parser_curves = curves
        FIELD_INDEX_CONVERSION = {0: 0, 1: 2, 2: 3, 3: 4}
        graph_column = FIELD_INDEX_CONVERSION[self.settings.value('live_graph_field', type=int)]
        graph_colors = self.theme['plot']['color_cycler'][:5]

    table = QTableView()
    table.setAlternatingRowColors(self.theme['s.c']['table_alternate'])
    table.setShowGrid(self.theme['s.c']['table_gridline'])
    table.setStyleSheet(get_style_class(self, 'QTableView', 'live_table'))
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.horizontalHeader().setStyleSheet(
            get_style_class(self, 'QHeaderView', 'live_table_header'))
    table.verticalHeader().setStyleSheet(get_style_class(self, 'QHeaderView', 'live_table_index'))
    table.horizontalHeader().setSectionResizeMode(RFIXED)
    table.verticalHeader().setSectionResizeMode(RFIXED)
    table.setSizePolicy(SMINMIN)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setMinimumWidth(self.sidebar_item_width * 0.25)
    table.setMinimumHeight(self.sidebar_item_width * 0.25)
    model = LiveParserTableModel(
            [[0] * len(LIVE_TABLE_HEADER)], LIVE_TABLE_HEADER, [''],
            theme_font(self, 'live_table_header'), theme_font(self, 'live_table'),
            legend_col=graph_column, colors=graph_colors)
    table.setModel(model)
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    for index in range(len(LIVE_TABLE_HEADER)):
        if not self.settings.value(f'live_columns|{index}', type=bool):
            table.hideColumn(index)
    self.widgets.live_parser_table = table
    layout.addWidget(table, stretch=1)

    bottom_layout = QGridLayout()
    bottom_layout.setContentsMargins(self.theme['defaults']['isp'], 0, 0, 0)
    bottom_layout.setSpacing(0)
    bottom_layout.setColumnStretch(0, 1)
    bottom_layout.setColumnStretch(2, 1)

    copy_button = copy_button = create_icon_button(
            self, self.icons['copy'], 'Copy Result', style_override={'margin-bottom': '@margin'},
            icon_size=[self.theme['s.c']['button_icon_size'] * 0.8] * 2)
    copy_button.clicked.connect(lambda: copy_live_data_callback(self))
    bottom_layout.addWidget(copy_button, 0, 0, alignment=ARIGHT | AVCENTER)
    activate_button = FlipButton('Activate', 'Deactivate', live_window, checkable=True)
    activate_button.setStyleSheet(self.get_style_class(
            'QPushButton', 'toggle_button', {'margin': (1, 8, 10, 8)}))
    activate_button.setFont(self.theme_font('app', '@subhead'))
    activate_button.set_func_r(lambda: self.live_parser.start())
    activate_button.set_func_l(lambda: self.live_parser.stop())
    bottom_layout.addWidget(activate_button, 0, 1, alignment=AVCENTER)
    close_button = create_icon_button(
            self, self.icons['close'], 'Close Live Parser',
            style_override={'margin-bottom': '@margin'},
            icon_size=[self.theme['s.c']['button_icon_size'] * 0.8] * 2)
    close_button.clicked.connect(lambda: live_parser_toggle(self, False))
    bottom_layout.addWidget(close_button, 0, 2, alignment=ALEFT | AVCENTER)

    grip = SizeGrip(live_window)
    grip.setStyleSheet(get_style(self, 'resize_handle'))
    bottom_layout.addWidget(grip, 0, 3, alignment=ARIGHT | ABOTTOM)

    layout.addLayout(bottom_layout)
    live_window.setLayout(layout)
    live_window.show()
    self.live_parser_window = live_window


def live_parser_close_callback(self, event):
    """
    Executed when application is closed.
    """
    window_geometry = self.live_parser_window.saveGeometry()
    self.settings.setValue('live_geometry', window_geometry)
    event.accept()


def live_parser_press_event(self, event: QMouseEvent):
    self.live_parser_window.start_pos = event.globalPosition().toPoint()
    event.accept()


def live_parser_move_event(self, event: QMouseEvent):
    parser_window = self.live_parser_window
    pos_delta = QPoint(event.globalPosition().toPoint() - parser_window.start_pos)
    parser_window.move(parser_window.x() + pos_delta.x(), parser_window.y() + pos_delta.y())
    parser_window.start_pos = event.globalPosition().toPoint()
    event.accept()
