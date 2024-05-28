import os

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QIntValidator, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QDialog
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLineEdit
from PySide6.QtWidgets import QMessageBox, QSpacerItem, QSplitter, QTableView
from PySide6.QtWidgets import QVBoxLayout

from OSCR import LiveParser, LIVE_TABLE_HEADER
from .callbacks import (
        auto_split_callback, combat_split_callback, copy_live_data_callback, trim_logfile)
from .displayer import create_live_graph, update_live_display, update_live_graph, update_live_table
from .datamodels import LiveParserTableModel
from .style import get_style, get_style_class, theme_font
from .textedit import format_path
from .widgetbuilder import create_button, create_frame, create_icon_button, create_label
from .widgetbuilder import ABOTTOM, AHCENTER, ALEFT, ARIGHT, AVCENTER, RFIXED
from .widgetbuilder import SEXPAND, SMAX, SMAXMAX, SMINMAX, SMINMIN
from .widgets import FlipButton, LiveParserWindow, SizeGrip


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
    dialog.addButton('Trim', QMessageBox.ButtonRole.ActionRole)
    dialog.addButton('Continue', QMessageBox.ButtonRole.AcceptRole)
    dialog.setDefaultButton(default_button)
    clicked = dialog.exec()
    if clicked == 1:
        return 'split dialog'
    elif clicked == 2:
        return 'trim'
    elif clicked == 3:
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

    trim_heading = create_label(self, 'Trim Logfile:', 'label_heading')
    grid_layout.addWidget(trim_heading, 0, 0, alignment=ALEFT)
    label_text = (
            'Removes all combats but the most recent one from the selected logfile. '
            'All previous combats will be lost!')
    trim_text = create_label(self, label_text, 'label')
    trim_text.setWordWrap(True)
    trim_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(trim_text, 1, 0, alignment=ALEFT)
    trim_button = create_button(self, 'Trim')
    trim_button.clicked.connect(lambda: trim_logfile(self))
    grid_layout.addWidget(trim_button, 1, 2, alignment=ARIGHT | ABOTTOM)
    grid_layout.setRowMinimumHeight(2, item_spacing)
    seperator_8 = create_frame(self, content_frame, 'hr', size_policy=SMINMIN)
    seperator_8.setFixedHeight(self.theme['hr']['height'])
    grid_layout.addWidget(seperator_8, 3, 0, 1, 3)
    grid_layout.setRowMinimumHeight(4, item_spacing)

    auto_split_heading = create_label(self, 'Split Log Automatically:', 'label_heading')
    grid_layout.addWidget(auto_split_heading, 5, 0, alignment=ALEFT)
    label_text = (
            'Automatically splits the logfile at the next combat end after '
            f'{self.settings.value("split_log_after", type=int):,} lines until the entire file has '
            ' been split. The new files are written to the selected folder. It is advised to '
            'select an empty folder to ensure all files are saved correctly.')
    auto_split_text = create_label(self, label_text, 'label')
    auto_split_text.setWordWrap(True)
    auto_split_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(auto_split_text, 6, 0, alignment=ALEFT)
    auto_split_button = create_button(self, 'Auto Split')
    auto_split_button.clicked.connect(lambda: auto_split_callback(self, current_logpath))
    grid_layout.addWidget(auto_split_button, 6, 2, alignment=ARIGHT | ABOTTOM)
    grid_layout.setRowMinimumHeight(7, item_spacing)
    seperator_8 = create_frame(self, content_frame, 'hr', size_policy=SMINMIN)
    seperator_8.setFixedHeight(self.theme['hr']['height'])
    grid_layout.addWidget(seperator_8, 8, 0, 1, 3)
    grid_layout.setRowMinimumHeight(9, item_spacing)
    range_split_heading = create_label(self, 'Export Range of Combats:', 'label_heading')
    grid_layout.addWidget(range_split_heading, 10, 0, alignment=ALEFT)
    label_text = (
            'Exports combats including and between lower and upper limit to selected file. '
            'Both limits refer to the indexed list of all combats in the file starting with 1. '
            'An upper limit larger than the total number of combats or of "-1", is treated as '
            'being equal to the total number of combats.')
    range_split_text = create_label(self, label_text, 'label')
    range_split_text.setWordWrap(True)
    range_split_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(range_split_text, 11, 0, alignment=ALEFT)
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
    grid_layout.addLayout(range_limit_layout, 11, 1)
    range_split_button = create_button(self, 'Export Combats')
    range_split_button.clicked.connect(
            lambda le=lower_range_entry, ue=upper_range_entry:
            combat_split_callback(self, current_logpath, le.text(), ue.text()))
    grid_layout.addWidget(range_split_button, 11, 2, alignment=ARIGHT | ABOTTOM)

    content_frame.setLayout(vertical_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle('OSCR - Split Logfile')
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.exec()


def uploadresult_dialog(self, result):
    """
    Shows a dialog that informs about the result of the triggered upload.

    Paramters:
    - :param result: dict containing result
    """
    dialog = QDialog(self.window)
    main_layout = QVBoxLayout()
    thick = self.theme['app']['frame_thickness']
    main_layout.setContentsMargins(thick, thick, thick, thick)
    content_frame = create_frame(self)
    main_layout.addWidget(content_frame)
    content_layout = QGridLayout()
    content_layout.setContentsMargins(thick, thick, thick, thick)
    content_layout.setSpacing(0)
    margin = {'margin-bottom': self.theme['defaults']['isp']}
    title_label = create_label(self, 'Upload Results:', 'label_heading', style_override=margin)
    content_layout.addWidget(title_label, 0, 0, 1, 4, alignment=ALEFT)
    icon_size = QSize(self.config['icon_size'] / 1.5, self.config['icon_size'] / 1.5)
    for row, line in enumerate(result, 1):
        if row % 2 == 1:
            table_style = {'background-color': '@mbg', 'padding': (5, 3, 3, 3), 'margin': 0}
            icon_table_style = {'background-color': '@mbg', 'padding': (3, 3, 3, 3), 'margin': 0}
        else:
            table_style = {'background-color': '@bg', 'padding': (5, 3, 3, 3), 'margin': 0}
            icon_table_style = {'background-color': '@bg', 'padding': (3, 3, 3, 3), 'margin': 0}
        if line.updated:
            icon = self.icons['check'].pixmap(icon_size)
        else:
            icon = self.icons['dash'].pixmap(icon_size)
        status_label = create_label(self, '', style_override=icon_table_style)
        status_label.setPixmap(icon)
        status_label.setSizePolicy(SMINMIN)
        content_layout.addWidget(status_label, row, 0)
        name_label = create_label(self, line.name, style_override=table_style)
        name_label.setSizePolicy(SMINMAX)
        content_layout.addWidget(name_label, row, 1)
        value_label = create_label(self, str(line.value), style_override=table_style)
        value_label.setSizePolicy(SMINMAX)
        value_label.setAlignment(ARIGHT)
        content_layout.addWidget(value_label, row, 2)
        detail_label = create_label(self, line.detail, style_override=table_style)
        detail_label.setSizePolicy(SMINMAX)
        content_layout.addWidget(detail_label, row, 3)
    top_margin = {'margin-top': self.theme['defaults']['isp']}
    close_button = create_button(self, 'Close', style_override=top_margin)
    close_button.clicked.connect(dialog.close)
    content_layout.addWidget(close_button, row + 1, 0, 1, 4, alignment=AHCENTER)
    content_frame.setLayout(content_layout)

    dialog.setLayout(main_layout)
    dialog.setWindowTitle('OSCR - Upload Results')
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.setFixedSize(dialog.sizeHint())
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
                self, data, graph_active, data_buffer, data_field),
                settings=self.live_parser_settings)
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
        self.live_parser_window.update_table.disconnect()
        self.live_parser_window.update_graph.disconnect()
        self.live_parser_window.deleteLater()
        self.live_parser_window = None
        self.live_parser = None
        self.widgets.live_parser_table = None
        self.widgets.live_parser_splitter = None
        self.widgets.live_parser_button.setChecked(False)


def create_live_parser_window(self):
    """
    Creates the LiveParser window.
    """
    ui_scale = self.config['ui_scale']
    self.config['ui_scale'] = self.config['live_scale']

    live_window = LiveParserWindow()
    live_window.setStyleSheet(get_style(self, 'live_parser'))
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
    graph_active = self.settings.value('live_graph_active', type=bool)
    if graph_active:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(get_style_class(self, 'QSplitter', 'splitter'))
        splitter.setChildrenCollapsible(False)
        self.widgets.live_parser_splitter = splitter
        graph_frame, curves = create_live_graph(self)
        graph_frame.setMinimumHeight(self.sidebar_item_width * 0.1)
        splitter.addWidget(graph_frame)
        self.widgets.live_parser_curves = curves
        FIELD_INDEX_CONVERSION = {0: 0, 1: 2, 2: 3, 3: 4}
        graph_column = FIELD_INDEX_CONVERSION[self.settings.value('live_graph_field', type=int)]
        graph_colors = self.theme['plot']['color_cycler'][:5]
        layout.addWidget(splitter, stretch=1)

    table = QTableView()
    table.setAlternatingRowColors(self.theme['s.c']['table_alternate'])
    table.setShowGrid(self.theme['s.c']['table_gridline'])
    table.setStyleSheet(get_style_class(self, 'QTableView', 'live_table'))
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.horizontalHeader().setStyleSheet(
            get_style_class(self, 'QHeaderView', 'live_table_header'))
    table.verticalHeader().setStyleSheet(get_style_class(self, 'QHeaderView', 'live_table_index'))
    table.verticalHeader().setMinimumHeight(1)
    table.verticalHeader().setDefaultSectionSize(1)
    table.horizontalHeader().setMinimumWidth(1)
    table.horizontalHeader().setDefaultSectionSize(1)
    table.horizontalHeader().setSectionResizeMode(RFIXED)
    table.verticalHeader().setSectionResizeMode(RFIXED)
    table.setSizePolicy(SMINMIN)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setMinimumWidth(self.sidebar_item_width * 0.1)
    table.setMinimumHeight(self.sidebar_item_width * 0.1)
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
    if graph_active:
        splitter.addWidget(table)
        if self.settings.value('live_splitter'):
            splitter.restoreState(self.settings.value('live_splitter'))
    else:
        layout.addWidget(table, 1)

    bottom_layout = QGridLayout()
    bottom_layout.setContentsMargins(self.theme['defaults']['isp'], 0, 0, 0)
    bottom_layout.setSpacing(0)
    bottom_layout.setColumnStretch(0, 1)
    bottom_layout.setColumnStretch(2, 1)

    icon_size = [self.theme['s.c']['button_icon_size'] * self.config['live_scale'] * 0.8] * 2
    copy_button = copy_button = create_icon_button(
            self, self.icons['copy'], 'Copy Result', icon_size=icon_size)
    copy_button.clicked.connect(lambda: copy_live_data_callback(self))
    bottom_layout.addWidget(copy_button, 0, 0, alignment=ARIGHT | AVCENTER)
    activate_button = FlipButton('Activate', 'Deactivate', live_window, checkable=True)
    activate_button.setStyleSheet(self.get_style_class(
            'QPushButton', 'toggle_button', {'margin': (0, 8, 0, 8)}))
    activate_button.setFont(self.theme_font('app', '@subhead'))
    activate_button.r_function = lambda: self.live_parser.start()
    activate_button.l_function = lambda: self.live_parser.stop()
    bottom_layout.addWidget(activate_button, 0, 1, alignment=AVCENTER)
    close_button = create_icon_button(
            self, self.icons['close'], 'Close Live Parser', icon_size=icon_size)
    close_button.clicked.connect(lambda: live_parser_toggle(self, False))
    bottom_layout.addWidget(close_button, 0, 2, alignment=ALEFT | AVCENTER)

    grip = SizeGrip(live_window)
    grip.setStyleSheet(get_style(self, 'resize_handle'))
    bottom_layout.addWidget(grip, 0, 3, alignment=ARIGHT | ABOTTOM)

    layout.addLayout(bottom_layout)
    live_window.setLayout(layout)
    live_window.update_table.connect(lambda data: update_live_table(self, data))
    live_window.update_graph.connect(update_live_graph)
    self.live_parser_window = live_window
    self.config['ui_scale'] = ui_scale
    live_window.show()


def live_parser_close_callback(self, event):
    """
    Executed when application is closed.
    """
    window_geometry = self.live_parser_window.saveGeometry()
    self.settings.setValue('live_geometry', window_geometry)
    try:
        self.settings.setValue('live_splitter', self.widgets.live_parser_splitter.saveState())
    except AttributeError:
        pass
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
