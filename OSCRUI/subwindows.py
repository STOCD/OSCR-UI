import os
from traceback import format_exception

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QMouseEvent, QTextOption
from PySide6.QtWidgets import (
        QDialog, QGridLayout, QHBoxLayout, QListView, QMessageBox,
        QSplitter, QTableView, QTextEdit, QVBoxLayout)

from OSCR import LiveParser, LIVE_TABLE_HEADER

from .callbacks import (
        confirm_trim_logfile, copy_live_data_callback, extract_combats, populate_split_combats_list,
        repair_logfile)
from .dialogs import show_message
from .displayer import create_live_graph, update_live_display, update_live_graph, update_live_table
from .datamodels import CombatModel, LiveParserTableModel
from .iofunctions import open_link
from .style import get_style, get_style_class, theme_font
from .textedit import format_path
from .translation import tr
from .widgetbuilder import (
        create_button, create_button_series, create_frame, create_icon_button, create_label,
        ABOTTOM, AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER, RFIXED,
        SMAXMAX, SMINMAX, SMINMIN, SMIXMIN)
from .widgets import CombatDelegate, FlipButton, LiveParserWindow, SizeGrip


def split_dialog(self):
    """
    Opens dialog to split the current logfile.
    """
    main_layout = QVBoxLayout()
    thick = self.theme['app']['frame_thickness']
    main_layout.setContentsMargins(thick, thick, thick, thick)
    content_frame = create_frame(self)
    main_layout.addWidget(content_frame)
    current_logpath = self.entry.text()
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(thick, thick, thick, thick)
    content_layout.setSpacing(thick)
    log_layout = QHBoxLayout()
    log_layout.setContentsMargins(0, 0, 0, 0)
    log_layout.setSpacing(thick)
    log_layout.setAlignment(ALEFT)
    current_log_heading = create_label(
            self, tr('Selected Logfile:'), 'label_light')
    log_layout.addWidget(current_log_heading)
    current_log_label = create_label(
            self, format_path(current_logpath), 'label_subhead', {'margin-bottom': 0})
    log_layout.addWidget(current_log_label)
    content_layout.addLayout(log_layout)
    seperator = create_frame(self, style='hr', size_policy=SMINMAX)
    seperator.setFixedHeight(self.theme['hr']['height'])
    content_layout.addWidget(seperator)
    trim_layout = QGridLayout()
    trim_layout.setContentsMargins(0, 0, 0, 0)
    trim_layout.setSpacing(thick)
    trim_layout.setColumnStretch(0, 1)
    trim_heading = create_label(self, tr('Trim Logfile:'), 'label_heading')
    trim_layout.addWidget(trim_heading, 0, 0, alignment=ALEFT)
    label_text = tr(
            'Removes all combats except for the most recent one from the selected logfile. '
            'All previous combats will be lost!')
    trim_text = create_label(self, label_text)
    trim_text.setSizePolicy(SMINMAX)
    trim_text.setWordWrap(True)
    trim_layout.addWidget(trim_text, 1, 0)
    trim_button = create_button(self, tr('Trim'))
    trim_button.clicked.connect(lambda: confirm_trim_logfile(self))
    trim_layout.addWidget(trim_button, 0, 1, alignment=ARIGHT | ABOTTOM)
    content_layout.addLayout(trim_layout)
    seperator = create_frame(self, style='hr', size_policy=SMINMAX)
    seperator.setFixedHeight(self.theme['hr']['height'])
    content_layout.addWidget(seperator)
    repair_layout = QGridLayout()
    repair_layout.setContentsMargins(0, 0, 0, 0)
    repair_layout.setSpacing(thick)
    repair_layout.setColumnStretch(0, 1)
    repair_log_heading = create_label(self, tr('Repair Logfile:'), 'label_heading')
    repair_layout.addWidget(repair_log_heading, 0, 0, alignment=ALEFT)
    label_text = tr('Attempts to repair the logfile by replacing sections known to break parsing.')
    repair_label = create_label(self, label_text)
    repair_layout.addWidget(repair_label, 1, 0)
    repair_log_button = create_button(self, tr('Repair'))
    repair_log_button.clicked.connect(lambda: repair_logfile(self))
    repair_layout.addWidget(repair_log_button, 0, 1, alignment=ARIGHT | ABOTTOM)
    content_layout.addLayout(repair_layout)
    seperator = create_frame(self, style='hr', size_policy=SMINMAX)
    seperator.setFixedHeight(self.theme['hr']['height'])
    content_layout.addWidget(seperator)

    combat_list = QListView()
    split_heading_layout = QHBoxLayout()
    split_heading_layout.setContentsMargins(0, 0, 0, 0)
    split_heading_layout.setSpacing(thick)
    split_heading = create_label(self, tr('Split Logfile:'), 'label_heading')
    split_heading_layout.addWidget(split_heading, alignment=ALEFT, stretch=1)
    split_button_style = {
        tr('Load Combats'): {'callback': lambda: populate_split_combats_list(self, combat_list)},
        tr('Split'): {'callback': lambda: extract_combats(
                self, combat_list.selectionModel().selectedIndexes())},
    }
    buttons_layout = create_button_series(self, split_button_style, 'button', seperator='•')
    split_heading_layout.addLayout(buttons_layout)
    content_layout.addLayout(split_heading_layout)
    label_text = tr('Extracts (multiple) combats from selected file and saves them to new file.')
    split_label = create_label(self, label_text)
    content_layout.addWidget(split_label)
    background_frame = create_frame(self, style='frame', style_override={
            'border-radius': self.theme['listbox']['border-radius'], 'margin-top': '@csp',
            'margin-bottom': '@csp'}, size_policy=SMINMIN)
    background_layout = QVBoxLayout()
    background_layout.setContentsMargins(0, 0, 0, 0)
    background_frame.setLayout(background_layout)
    combat_list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
    combat_list.setSelectionMode(QListView.SelectionMode.MultiSelection)
    combat_list.setStyleSheet(get_style_class(self, 'QListView', 'listbox'))
    combat_list.setFont(theme_font(self, 'listbox'))
    combat_list.setAlternatingRowColors(True)
    combat_list.setSizePolicy(SMIXMIN)
    combat_list.setModel(CombatModel())
    ui_scale = self.config['ui_scale']
    border_width = 1 * ui_scale
    padding = 4 * ui_scale
    combat_list.setItemDelegate(CombatDelegate(border_width, padding))
    background_layout.addWidget(combat_list)
    content_layout.addWidget(background_frame, alignment=AHCENTER)

    content_frame.setLayout(content_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle(tr('OSCR - Split Logfile'))
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.exec()


def uploadresult_dialog(self, result: dict):
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
    title_label = create_label(self, f"{result.detail}", 'label_heading', style_override=margin)
    content_layout.addWidget(title_label, 0, 0, 1, 4, alignment=ALEFT)
    view_button = create_button(self, 'View Online', style_override=margin)
    view_button.clicked.connect(lambda: view_upload_result(self, result.combatlog))
    if result.results:
        content_layout.addWidget(view_button, 0, 0, 1, 4, alignment=ARIGHT)
    icon_size = QSize(self.config['icon_size'] / 1.5, self.config['icon_size'] / 1.5)
    row = 0
    if result.results:
        for row, line in enumerate(result.results, 1):
            if row % 2 == 1:
                table_style = {'background-color': '@mbg', 'padding': (5, 3, 3, 3), 'margin': 0}
                icon_table_style = {'background-color': '@mbg', 'padding': 3, 'margin': 0}
            else:
                table_style = {'background-color': '@bg', 'padding': (5, 3, 3, 3), 'margin': 0}
                icon_table_style = {'background-color': '@bg', 'padding': 3, 'margin': 0}
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
    dialog.setWindowTitle(tr('OSCR - Upload Results'))
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.setFixedSize(dialog.sizeHint())
    dialog.exec()


def live_parser_toggle(self, activate: bool):
    """
    Activates / Deactivates LiveParser.

    Parameters:
    - :param activate: True when parser should be shown; False when open parser should be closed.
    """
    if activate:
        log_path = self.settings.value('sto_log_path')
        if not log_path or not os.path.isfile(log_path):
            show_message(self, tr('Invalid Logfile'), tr(
                    'Make sure to set the STO Logfile setting in the settings tab to a valid '
                    'logfile before starting the live parser.'), 'warning')
            self.widgets.live_parser_button.setChecked(False)
            return
        FIELD_INDEX_CONVERSION = {0: 0, 1: 2, 2: 3, 3: 4}
        graph_active = self.settings.value('live_graph_active', type=bool)
        data_buffer = list()
        data_field = FIELD_INDEX_CONVERSION[self.settings.value('live_graph_field', type=int)]
        self.live_parser = LiveParser(log_path, update_callback=lambda p, t: update_live_display(
                self, p, t, graph_active, data_buffer, data_field),
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
    live_window.setWindowTitle("Live Parser")
    live_window.setWindowIcon(self.icons['oscr'])
    live_window.setWindowFlags(
            live_window.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
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
        splitter.setStyleSheet(get_style_class(
                self, 'QSplitter', 'splitter', {'border': 'none', 'margin': 0}))
        splitter.setChildrenCollapsible(False)
        self.widgets.live_parser_splitter = splitter
        graph_frame, curves = create_live_graph(self)
        graph_frame.setMinimumHeight(self.sidebar_item_width * 0.1)
        splitter.addWidget(graph_frame)
        self.widgets.live_parser_curves = curves
        FIELD_INDEX_CONVERSION = {0: 0, 1: 2, 2: 3, 3: 4}
        graph_column = FIELD_INDEX_CONVERSION[self.settings.value('live_graph_field', type=int)]
        graph_colors = (*self.theme['plot']['color_cycler'][:5], '#eeeeee')
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
    table.verticalHeader().setDefaultSectionSize(table.verticalHeader().fontMetrics().height() + 2)
    table.horizontalHeader().setMinimumWidth(1)
    table.horizontalHeader().setDefaultSectionSize(1)
    table.horizontalHeader().setSectionResizeMode(RFIXED)
    table.verticalHeader().setSectionResizeMode(RFIXED)
    table.setSizePolicy(SMINMIN)
    table.setSelectionMode(QTableView.SelectionMode.NoSelection)
    table.setMinimumWidth(self.sidebar_item_width * 0.1)
    table.setMinimumHeight(self.sidebar_item_width * 0.1)
    table.setSortingEnabled(True)
    if self.settings.value('live_player', defaultValue='Handle') == 'Handle':
        name_index = 1
    else:
        name_index = 0
    placeholder = [0] * len(LIVE_TABLE_HEADER)
    model = LiveParserTableModel(
            [[('Name', '@handle'), *placeholder, 0]], tr(LIVE_TABLE_HEADER), [],
            theme_font(self, 'live_table_header'), theme_font(self, 'live_table'),
            legend_col=graph_column, colors=graph_colors, name_index=name_index)
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

    margin = self.config['ui_scale'] * 6
    bottom_layout = QGridLayout()
    bottom_layout.setContentsMargins(margin, 0, 0, 0)
    bottom_layout.setSpacing(margin)
    bottom_layout.setColumnStretch(4, 1)

    activate_button = FlipButton(tr('Activate'), tr('Deactivate'), checkable=True)
    activate_button.setStyleSheet(self.get_style_class(
            'QPushButton', 'toggle_button', {'margin': (0, 0, 3, 0)}))
    activate_button.setFont(self.theme_font('app', '@subhead'))
    activate_button.r_function = lambda: self.live_parser.start()
    activate_button.l_function = lambda: self.live_parser.stop()
    bottom_layout.addWidget(activate_button, 0, 0, alignment=ALEFT | AVCENTER)
    icon_size = [self.theme['s.c']['button_icon_size'] * self.config['live_scale'] * 0.8] * 2
    copy_button = create_icon_button(
            self, self.icons['copy'], tr('Copy Result'), style_override={'margin': (0, 0, 3, 0)},
            icon_size=icon_size)
    copy_button.clicked.connect(lambda: copy_live_data_callback(self))
    bottom_layout.addWidget(copy_button, 0, 1, alignment=ALEFT | AVCENTER)
    close_button = create_icon_button(
            self, self.icons['close'], tr('Close Live Parser'),
            style_override={'margin': (0, 0, 3, 0)}, icon_size=icon_size)
    close_button.clicked.connect(lambda: live_parser_toggle(self, False))
    bottom_layout.addWidget(close_button, 0, 2, alignment=ALEFT | AVCENTER)
    time_label = create_label(self, 'Duration: 0s')
    bottom_layout.addWidget(time_label, 0, 3, alignment=ALEFT | AVCENTER)
    self.widgets.live_parser_duration_label = time_label

    grip = SizeGrip(live_window)
    grip.setStyleSheet(get_style(self, 'resize_handle'))
    bottom_layout.addWidget(grip, 0, 4, alignment=ARIGHT | ABOTTOM)

    layout.addLayout(bottom_layout)
    live_window.setLayout(layout)
    live_window.update_table.connect(lambda data: update_live_table(self, data))
    live_window.update_graph.connect(update_live_graph)
    self.live_parser_window = live_window
    self.config['ui_scale'] = ui_scale
    live_window.show()

    if self.settings.value('live_enabled', type=bool):
        activate_button.flip()


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
    """
    Used to start moving the parser window.
    """
    self.live_parser_window.start_pos = event.globalPosition().toPoint()
    event.accept()


def live_parser_move_event(self, event: QMouseEvent):
    """
    Used to move the parser window to new location.
    """
    parser_window = self.live_parser_window
    pos_delta = QPoint(event.globalPosition().toPoint() - parser_window.start_pos)
    parser_window.move(parser_window.x() + pos_delta.x(), parser_window.y() + pos_delta.y())
    parser_window.start_pos = event.globalPosition().toPoint()
    event.accept()


def view_upload_result(self, log_id: str):
    """
    Opens webbrowser to show the uploaded combatlog on the DPS League tables.
    """
    open_link(f"https://oscr.stobuilds.com/ui/combatlog/{log_id}/")


def show_detection_info(self, combat_index: int):
    """
    Shows a subwindow containing information on the detection process

    Parameters:
    - :param combat_index: combat index in `self.parser.combats` identifying the combat to show \
    detection data on
    """
    if combat_index < 0:
        return
    dialog = QDialog(self.window)
    thick = self.theme['app']['frame_thickness']
    item_spacing = self.theme['defaults']['isp']
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(thick, thick, thick, thick)
    content_frame = create_frame(self)
    main_layout.addWidget(content_frame)
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(thick, thick, thick, thick)
    content_layout.setSpacing(item_spacing)

    for detection_info in self.parser.combats[combat_index].meta['detection_info']:
        if detection_info.success:
            if detection_info.step == 'existence':
                detection_method = tr('by checking whether the following entities exist in the log')
            elif detection_info.step == 'deaths':
                detection_method = tr('by checking the death counts of following entities')
            else:
                detection_method = tr('by checking the hull values of following entities')
            if detection_info.type == 'both':
                detected_type = tr('Map and Difficulty were')
            elif detection_info.type == 'difficulty':
                detected_type = f"{tr('Difficulty')} ({detection_info.difficulty}) {tr('was')}"
            else:
                detected_type = f"{tr('Map')} ({detection_info.map}) {tr('was')}"
            t = f"{tr('The')} {detected_type} {tr('successfully detected')} {detection_method}"
            t += ': ' + ', '.join(detection_info.identificators) + '.'
        else:
            if detection_info.type == 'both':
                detected_type = tr('Map and Difficulty')
            elif detection_info.type == 'difficulty':
                detected_type = f"{tr('Difficulty')} ({detection_info.difficulty})"
            else:
                detected_type = f"{tr('Map')} ({detection_info.map}) {tr('was')}"
            t = f"{tr('The')} {tr(detected_type)} {tr('could not be detected, because')} "
            if detection_info.step == 'existence':
                t += tr('no entity identifying a map was found in the log.')
            elif detection_info.step == 'deaths':
                t += f'{tr("the entity")} "{detection_info.identificators[0]}" {tr("was killed")} '
                t += f"{detection_info.retrieved_value} {tr('times instead of the expected')} "
                t += f"{detection_info.target_value} {tr('times')}."
            else:
                t += f'{tr("the entities")} "{detection_info.identificators[0]}" '
                t += f"{tr('average hull capacity of')} {detection_info.retrieved_value:.0f} "
                t += f"{tr('was higher than the allowed')} {detection_info.target_value:.0f}."
        info_label = create_label(self, t)
        info_label.setSizePolicy(SMINMAX)
        info_label.setWordWrap(True)
        content_layout.addWidget(info_label)

    seperator = create_frame(self, style='light_frame', size_policy=SMINMAX)
    seperator.setFixedHeight(1)
    content_layout.addWidget(seperator)
    ok_button = create_button(self, tr('OK'))
    ok_button.clicked.connect(lambda: dialog.done(0))
    content_layout.addWidget(ok_button, alignment=AHCENTER)
    content_frame.setLayout(content_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle(tr('OSCR - Map Detection Details'))
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.exec()


def show_parser_error(self, error: BaseException):
    """
    Displays subwindow showing an error message and the given error traceback.

    - :param error: captured error with optionally additional data in the error.args attribute
    """
    default_message, *additional_messages = error.args
    error.args = (default_message,)
    error_text = ''.join(format_exception(error))
    if len(additional_messages) > 0:
        error_text += '\n\n++++++++++++++++++++++++++++++++++++++++++++++++++\n\n'
        error_text += '\n'.join(additional_messages)
    dialog = QDialog(self.window)
    thick = self.theme['app']['frame_thickness']
    item_spacing = self.theme['defaults']['isp']
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(thick, thick, thick, thick)
    dialog_frame = create_frame(self, size_policy=SMINMIN)
    main_layout.addWidget(dialog_frame)
    dialog_layout = QVBoxLayout()
    dialog_layout.setContentsMargins(thick, thick, thick, thick)
    dialog_layout.setSpacing(thick)
    content_frame = create_frame(self, size_policy=SMINMIN)
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(item_spacing)
    content_layout.setAlignment(ATOP)

    top_layout = QHBoxLayout()
    top_layout.setContentsMargins(0, 0, 0, 0)
    top_layout.setSpacing(2 * thick)
    icon_label = create_label(self, '')
    icon_size = self.theme['s.c']['big_icon_size'] * self.config['ui_scale']
    icon_label.setPixmap(self.icons['error'].pixmap(icon_size))
    top_layout.addWidget(icon_label, alignment=ALEFT | AVCENTER)
    msg = tr(
            'An error occurred while parsing the selected combatlog. You can try repairing the '
            'log file using the repair functionality in the "Manage Logfile" dialog. If the error '
            'persists, please report it to the #oscr-support channel in the STOBuilds Discord.')
    message_label = create_label(self, msg)
    message_label.setWordWrap(True)
    message_label.setSizePolicy(SMINMAX)
    top_layout.addWidget(message_label, stretch=1)
    content_layout.addLayout(top_layout)
    error_field = QTextEdit()
    error_field.setSizePolicy(SMINMIN)
    error_field.setText(error_text)
    error_field.setReadOnly(True)
    error_field.setWordWrapMode(QTextOption.WrapMode.NoWrap)
    error_field.setFont(theme_font(self, 'textedit'))
    error_field.setStyleSheet(get_style_class(self, 'QTextEdit', 'textedit'))
    expand_button = FlipButton(tr('Show Error'), tr('Hide Error'))
    expand_button.set_icon_r(self.icons['chevron-right'])
    expand_button.set_icon_l(self.icons['chevron-down'])
    expand_button.r_function = error_field.show
    expand_button.l_function = error_field.hide
    expand_button.setStyleSheet(get_style_class(self, 'FlipButton', 'button'))
    expand_button.setFont(theme_font(self, 'button'))
    content_layout.addWidget(expand_button, alignment=ALEFT)
    content_layout.addWidget(error_field, stretch=1)
    error_field.hide()
    content_frame.setLayout(content_layout)
    dialog_layout.addWidget(content_frame, stretch=1)

    seperator = create_frame(self, style='light_frame', size_policy=SMINMAX)
    seperator.setFixedHeight(1)
    dialog_layout.addWidget(seperator)
    ok_button = create_button(self, tr('OK'))
    ok_button.clicked.connect(lambda: dialog.done(0))
    dialog_layout.addWidget(ok_button, alignment=AHCENTER)
    dialog_frame.setLayout(dialog_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle(tr('OSCR - Parser Error'))
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.exec()
