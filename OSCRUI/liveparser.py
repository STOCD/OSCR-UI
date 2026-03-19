from pyqtgraph import mkPen, PlotDataItem, PlotWidget
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication, QGridLayout, QFrame, QHBoxLayout, QLabel, QSplitter, QTableView, QVBoxLayout)

from OSCR import LIVE_TABLE_HEADER, LiveParser

from .datamodels import LiveParserTableModel
from .dialogs import DialogsWrapper
from .config import OSCRSettings
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import (
    create_frame2, create_icon_button2, create_label2,
    ABOTTOM, ALEFT, ARIGHT, AVCENTER, SMAXMAX, SMINMIN, SMIXMAX, RFIXED)
from .widgetmanager import WidgetManager
from .widgets import CustomPlotAxis, FlipButton, SizeGrip


class LiveParserWindow(QFrame):
    """Manages LiveParser and its window"""
    update_table = Signal(tuple)
    update_graph = Signal(list)

    def __init__(
            self, global_settings: OSCRSettings, theme: AppTheme, dialogs: DialogsWrapper,
            widgets: WidgetManager):
        """
        Parameters:
        - :param global_settings: OSCRSettings
        - :param theme: reference to app theme
        - :param dialogs: reference to dialogs
        - :param widgets: reference to widget store
        """
        super().__init__()
        self._settings: OSCRSettings = global_settings
        self._theme: AppTheme = theme
        self._dialogs: DialogsWrapper = dialogs
        self._widgets: WidgetManager = widgets
        self._liveparser: LiveParser = LiveParser(
            update_callback=self.update_live_display, settings=self.live_parser_settings)
        self._move_start_pos: QPoint
        self._window_scale: float
        self._splitter: QSplitter
        self._graph_curves: list[PlotDataItem]
        self._table: QTableView
        self._table_model: LiveParserTableModel
        self._activate_button: FlipButton
        self._duration_label: QLabel
        self._graph_active: bool = False
        self._graph_data_buffer: list[list[int | float]] = list()
        self._graph_column: int = 0
        self.build_window()

    @property
    def live_parser_settings(self) -> dict:
        """
        Returns settings relevant to the LiveParser
        """
        return {'seconds_between_combats': self._settings.seconds_between_combats}

    def build_window(self):
        """
        Creates layout for window
        """
        self._window_scale = self._settings.liveparser__window_scale
        ui_scale_temp = self._theme.scale
        self._theme.scale = self._window_scale

        self.setStyleSheet(self._theme.get_style('live_parser'))
        self.setWindowTitle("Live Parser")
        self.setWindowIcon(self._theme.icons['oscr'])
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.FramelessWindowHint)
        if QApplication.platformName() == 'wayland':
            self.mousePressEvent = self.live_parser_move_wayland
        else:
            self.mousePressEvent = self.live_parser_press_event
            self.mouseMoveEvent = self.live_parser_move_event
        self.setSizePolicy(SMAXMAX)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setStyleSheet(self._theme.get_style_class(
            'QSplitter', 'splitter', {'border': 'none', 'margin': 0}))
        self._splitter.setChildrenCollapsible(False)
        graph_frame, self._graph_curves = self.create_live_graph()
        graph_frame.setMinimumHeight(self._window_scale * 50)
        self._splitter.addWidget(graph_frame)
        layout.addWidget(self._splitter, stretch=1)
        if not self._settings.liveparser__graph_active:
            self._splitter.widget(0).hide()

        table = QTableView()
        self._table = table
        table.setAlternatingRowColors(self._theme.opt.table_alternate)
        table.setShowGrid(self._theme.opt.table_gridline)
        table.setStyleSheet(self._theme.get_style_class('QTableView', 'live_table'))
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.horizontalHeader().setStyleSheet(
                self._theme.get_style_class('QHeaderView', 'live_table_header'))
        table.verticalHeader().setStyleSheet(
            self._theme.get_style_class('QHeaderView', 'live_table_index'))
        table.verticalHeader().setMinimumHeight(1)
        table.verticalHeader().setDefaultSectionSize(
            table.verticalHeader().fontMetrics().height() + 2)
        table.horizontalHeader().setMinimumWidth(1)
        table.horizontalHeader().setDefaultSectionSize(1)
        table.horizontalHeader().setSectionResizeMode(RFIXED)
        table.verticalHeader().setSectionResizeMode(RFIXED)
        table.setSizePolicy(SMINMIN)
        table.setSelectionMode(QTableView.SelectionMode.NoSelection)
        table.setMinimumWidth(self._window_scale * 150)
        table.setMinimumHeight(self._window_scale * 50)
        table.setSortingEnabled(True)
        graph_colors = (*self._theme['plot']['color_cycler'][:5], '#eeeeee')
        self._table_model = LiveParserTableModel(tr(LIVE_TABLE_HEADER), graph_colors)
        self._table_model.init_fonts(
            self._theme.get_font('live_table_header'), self._theme.get_font('live_table'))
        table.setModel(self._table_model)
        table.resizeRowsToContents()
        self._splitter.addWidget(table)
        if self._settings.liveparser__graph_active and self._settings.state__live_splitter:
            self._splitter.restoreState(self._settings.state__live_splitter)

        margin = self._theme.scale * 6
        bottom_layout = QGridLayout()
        bottom_layout.setContentsMargins(self._theme.scale * 4, 0, 0, 0)
        bottom_layout.setSpacing(margin)
        bottom_layout.setColumnStretch(4, 1)

        self._activate_button = FlipButton(tr('Activate'), tr('Deactivate'), checkable=True)
        self._activate_button.setStyleSheet(self._theme.get_style_class(
                'QPushButton', 'toggle_button', {'margin': (0, 0, 3, 0)}))
        self._activate_button.setFont(self._theme.get_font('app', '@subhead'))
        self._activate_button.r_function = self._liveparser.start
        self._activate_button.l_function = self._liveparser.stop
        bottom_layout.addWidget(self._activate_button, 0, 0, alignment=ALEFT | AVCENTER)
        icon_size = [self._theme.opt.default_icon_size * self._window_scale * 0.8] * 2
        copy_button = create_icon_button2(
                self._theme, 'copy', tr('Copy Result'),
                style_override={'margin': (0, 0, 3, 0)}, icon_size=icon_size)
        copy_button.clicked.connect(self.copy_live_data_callback)
        bottom_layout.addWidget(copy_button, 0, 1, alignment=ALEFT | AVCENTER)
        close_button = create_icon_button2(
                self._theme, 'close', tr('Close Live Parser'),
                style_override={'margin': (0, 0, 3, 0)}, icon_size=icon_size)
        close_button.clicked.connect(lambda: self.toggle_window(False))
        bottom_layout.addWidget(close_button, 0, 2, alignment=ALEFT | AVCENTER)
        time_label = create_label2(self._theme, 'Duration: 0s')
        bottom_layout.addWidget(time_label, 0, 3, alignment=ALEFT | AVCENTER)
        self._duration_label = time_label

        grip = SizeGrip(self)
        grip.setStyleSheet(self._theme.get_style('resize_handle'))
        bottom_layout.addWidget(grip, 0, 4, alignment=ARIGHT | ABOTTOM)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        self.update_table.connect(self.update_live_table)
        self.update_table.connect(self.init_live_table_columns)
        self.update_graph.connect(self.update_live_graph)
        self._theme.scale = ui_scale_temp

    def create_live_graph(self) -> tuple[QFrame, list[PlotDataItem]]:
        """
        Creates and styles live graph.

        :return: Frame containing the graph and list of curves that will be used to plot the data
        """
        plot_widget = PlotWidget()
        left_axis = CustomPlotAxis(
            'left', self._theme.get_font('live_plot_widget'), self._theme['defaults']['fg'],
            compressed=True)
        bottom_axis = CustomPlotAxis(
            'bottom', self._theme.get_font('plot_widget'), self._theme['defaults']['fg'], unit='s',
            no_labels=True)
        plot_widget.setAxisItems({'left': left_axis, 'bottom': bottom_axis})
        plot_widget.setStyleSheet(self._theme.get_style('plot_widget_nullifier'))
        plot_widget.setBackground(None)
        plot_widget.setMouseEnabled(False, False)
        plot_widget.setMenuEnabled(False)
        plot_widget.hideButtons()
        plot_widget.setDefaultPadding(padding=0)
        plot_widget.setXRange(-14, 0, padding=0)

        curves = list()
        for color_index in range(5):
            color = self._theme['plot']['color_cycler'][color_index]
            curves.append(plot_widget.plot([0], [0], pen=mkPen(color, width=1)))

        frame = create_frame2(self._theme, 'plot_widget', size_policy=SMIXMAX, style_override={
                'margin': 4, 'padding': 2, 'border': 'none'})
        frame.setMinimumWidth(self._window_scale * 200)
        frame.setMinimumHeight(self._window_scale * 200)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(plot_widget, stretch=1)
        frame.setLayout(layout)
        return frame, curves

    def update_shown_columns(self):
        """Shows/Hides appropriate table columns"""
        for index, state in enumerate(self._settings.liveparser__columns):
            if state:
                self._table.showColumn(index)
            else:
                self._table.hideColumn(index)
            # self._table.setColumnHidden(index, not state)
        self._table.resizeColumnsToContents()

    def update_live_display(self, player_data: dict[tuple, dict], combat_time: float):
        """
        Updates display of live parser to show the new data.

        Parameters:
        - :param player_data: dictionary containing the new data
        - :param combat_time: duration of the entire combat
        """
        cells = list()
        curves = list()
        for player, player_data in player_data.items():
            cells.append([player, *player_data.values(), 5])
        if self._graph_active:
            if len(self._graph_data_buffer) == 0:
                self._graph_data_buffer.extend(([0] * 15, [0] * 15, [0] * 15, [0] * 15, [0] * 15))
            zipper = zip(self._graph_data_buffer, cells, self._graph_curves)
            for id, (buffer_item, player_data, curve) in enumerate(zipper):
                buffer_item.pop(0)
                buffer_item.append(player_data[1 + self._graph_column])
                player_data[8] = id
                curves.append((curve, buffer_item))
            if len(curves) > 0:
                self.update_graph.emit(curves)

        if len(cells) > 0:
            self.update_table.emit(cells)
        self._duration_label.setText(f'Duration: {combat_time:.1f}s')

    def toggle_window(self, activate: bool):
        """
        Activates / Deactivates LiveParser.

        Parameters:
        - :param activate: True when parser should be shown; False when open parser should be
        closed.
        """
        if activate:
            if not self._liveparser.set_log_path(self._settings.sto_log_path):
                bad_logfile_message = tr(
                    'Make sure to set the STO Logfile setting in the settings tab to a valid '
                    'logfile before starting the live parser.')
                self._dialogs.show_message(tr('Invalid Logfile'), bad_logfile_message, 'warning')
                self._widgets.live_parser_button.setChecked(False)
                return
            if self._window_scale != self._settings.liveparser__window_scale:
                QFrame().setLayout(self.layout())
                self.build_window()
            if self._settings.state__live_geometry:
                self.restoreGeometry(self._settings.state__live_geometry)
            self._data_buffer = list()
            FIELD_INDEX_CONVERSION = {0: 0, 1: 2, 2: 3, 3: 4}
            self._graph_column = FIELD_INDEX_CONVERSION[self._settings.liveparser__graph_field]
            self._table_model.legend_column = self._graph_column
            if self._settings.liveparser__graph_active:
                self._graph_active = True
                self._splitter.widget(0).show()
                if self._settings.state__live_splitter:
                    self._splitter.restoreState(self._settings.state__live_splitter)
            else:
                self._graph_active = False
                self._splitter.widget(0).hide()
            if self._settings.liveparser__player_display == 'Handle':
                self._table_model.name_index = 1
            else:
                self._table_model.name_index = 0
            if self._settings.liveparser__auto_enabled:
                self._activate_button.flip()
            self.setWindowOpacity(self._settings.liveparser__window_opacity)
            self.update_shown_columns()
            self.show()
        else:
            self.store_window_state()
            self.hide()
            if self._activate_button.isChecked():
                self._activate_button.flip()
            self._widgets.live_parser_button.setChecked(False)

    @Slot()
    def update_live_table(self, data: list):
        """
        Updates the table of the live parser with the supplied data

        Parameters:
        - :param data: list containing the index and cell values
        """
        self._table_model.replace_data(data)
        self._table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()

    @Slot()
    def init_live_table_columns(self, _):
        """
        Triggers column visibilty update on first data insertion.
        """
        self.update_shown_columns()
        self.update_table.disconnect(self.init_live_table_columns)

    @Slot()
    def update_live_graph(self, curve_data: list[tuple[PlotDataItem, list[float]]]):
        """
        Updates the graph of the live parser with the supplied data

        Parameters:
        - :param curve_data: list containing pairs of curve items and data lists; curve items will
        be updated with the data
        """
        time_data = list(range(-14, 1))
        for curve, data_points in curve_data:
            curve.setData(time_data, data_points)

    def live_parser_press_event(self, event: QMouseEvent):
        """
        Used to start moving the parser window.
        """
        self._move_start_pos = event.globalPosition().toPoint()
        event.accept()

    def live_parser_move_event(self, event: QMouseEvent):
        """
        Used to move the parser window to new location.
        """
        pos_delta = QPoint(event.globalPosition().toPoint() - self._move_start_pos)
        self.move(self.x() + pos_delta.x(), self.y() + pos_delta.y())
        self._move_start_pos = event.globalPosition().toPoint()
        event.accept()

    def live_parser_move_wayland(self, event: QMouseEvent):
        """
        Used to move the parser window on wayland.
        """
        self.windowHandle().startSystemMove()
        event.accept()

    def store_window_state(self):
        """
        Stores state of window
        """
        self._settings.state__live_geometry = self.saveGeometry()
        if self._graph_active:
            self._settings.state__live_splitter = self._splitter.saveState()

    def copy_live_data_callback(self):
        """
        Copies the data from the live parser table.
        """
        output = list()
        name_index = 0 if self._settings.liveparser__player_display == 'Name' else 1
        if self._settings.liveparser__copy_kills:
            for row in self._table_model._data:
                output.append(f"{row[0][name_index]}: {row[1]:,.2f} ({row[6]:.0f})")
            output = '{ OSCR } DPS (Kills): ' + ' | '.join(output)
        else:
            for row in self._table_model._data:
                output.append(f"{row[0][name_index]}: {row[1]:,.2f}")
            output = '{ OSCR } DPS: ' + ' | '.join(output)
        QApplication.clipboard().setText(output)
