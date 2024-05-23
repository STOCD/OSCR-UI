from typing import Callable, Iterable

import numpy as np
from pyqtgraph import BarGraphItem, mkPen, PlotWidget, setConfigOptions
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableView, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Slot

from OSCR import TABLE_HEADER
from OSCR.combat import Combat

from .datamodels import OverviewTableModel, SortingProxy
from .widgetbuilder import ACENTER, AVCENTER, SMINMIN, SMIXMAX
from .widgetbuilder import create_frame, create_label, style_table
from .widgets import CustomPlotAxis
from .style import get_style, theme_font

setConfigOptions(antialias=True)


def setup_plot(plot_function: Callable) -> Callable:
    '''
    sets up Plot item and puts it into layout
    '''
    def plot_wrapper(self, data, time_reference=None):
        plot_widget = PlotWidget()
        plot_widget.setAxisItems({'left': CustomPlotAxis('left')})
        plot_widget.setAxisItems({'bottom': CustomPlotAxis('bottom')})
        plot_widget.setStyleSheet(get_style(self, 'plot_widget_nullifier'))
        plot_widget.setBackground(None)
        plot_widget.setMouseEnabled(False, False)
        plot_widget.setMenuEnabled(False)
        plot_widget.hideButtons()
        plot_widget.setDefaultPadding(padding=0)
        left_axis = plot_widget.getAxis('left')
        left_axis.setTickFont(theme_font(self, 'plot_widget'))
        left_axis.setTextPen(color=self.theme['defaults']['fg'])
        bottom_axis = plot_widget.getAxis('bottom')
        bottom_axis.setTickFont(theme_font(self, 'plot_widget'))
        bottom_axis.setTextPen(color=self.theme['defaults']['fg'])

        if time_reference is None:
            legend_data = plot_function(self, data, plot_widget)
        else:
            legend_data = plot_function(self, data, time_reference, plot_widget)

        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(self.theme['defaults']['isp'])
        inner_layout.addWidget(plot_widget)
        if legend_data is not None:
            legend_frame = create_legend(self, legend_data)
            inner_layout.addWidget(legend_frame, alignment=ACENTER)
        frame = create_frame(self, None, 'plot_widget', size_policy=SMINMIN)
        frame.setLayout(inner_layout)
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(frame)
        return outer_layout
    return plot_wrapper


def extract_overview_data(combat: Combat) -> tuple:
    '''
    converts dictionary containing player data to table data for the front page
    '''
    table = list()

    DPS_graph_data = dict()
    DMG_graph_data = dict()
    graph_time = dict()

    for player in combat.player_dict.values():
        table.append((*player,))

        DPS_graph_data[player.handle] = player.DPS_graph_data
        DMG_graph_data[player.handle] = player.DMG_graph_data
        graph_time[player.handle] = player.graph_time
    table.sort(key=lambda x: x[0])
    return (graph_time, DPS_graph_data, DMG_graph_data, table)


def create_overview(self):
    """
    creates the main Parse Overview including graphs and table
    """
    # clear graph frames
    for frame in self.widgets.overview_tab_frames:
        if frame.layout():
            QWidget().setLayout(frame.layout())
    if self.widgets.overview_table_frame.layout():
        QWidget().setLayout(self.widgets.overview_table_frame.layout())

    time_data, DPS_graph_data, DMG_graph_data, current_table = extract_overview_data(
            self.parser1.active_combat)

    line_layout = create_line_graph(self, DPS_graph_data, time_data)
    self.widgets.overview_tab_frames[1].setLayout(line_layout)

    group_bar_layout = create_grouped_bar_plot(self, DMG_graph_data, time_data)
    self.widgets.overview_tab_frames[2].setLayout(group_bar_layout)

    bar_layout = create_horizontal_bar_graph(self, current_table)
    self.widgets.overview_tab_frames[0].setLayout(bar_layout)

    table_layout = QVBoxLayout()
    table_layout.setContentsMargins(0, 0, 0, 0)
    table = create_overview_table(self, current_table)
    table_layout.addWidget(table)
    self.widgets.overview_table_frame.setLayout(table_layout)
    table.resizeColumnsToContents()


@setup_plot
def create_grouped_bar_plot(
        self, data: dict[str, tuple], time_reference: dict[str, tuple],
        bar_widget: PlotWidget) -> QVBoxLayout:
    """
    Creates a bar plot with grouped bars.

    Parameters:
    - :param data: dictionary containing the data to be plotted
    - :param time_reference: contains the time values for the data points
    - :param bar_widget: bar widget that will be plotted to (supplied by decorator)

    :return: layout containing the graph
    """
    bottom_axis = bar_widget.getAxis('bottom')
    bottom_axis.unit = 's'
    legend_data = list()

    group_width = 0.18
    player_num = len(data)
    if player_num == 0:
        return
    bar_width = group_width / player_num
    relative_bar_positions = np.linspace(0 + bar_width / 2, group_width - bar_width / 2, player_num)
    bar_position_offsets = relative_bar_positions - np.median(relative_bar_positions)

    zipper = zip(data.items(), self.theme['plot']['color_cycler'], bar_position_offsets)
    for (player, graph_data), color, offset in zipper:
        if player in time_reference:
            time_data = np.subtract(time_reference[player], offset)
            bars = BarGraphItem(
                    x=time_data, width=bar_width, height=graph_data, brush=color, pen=None,
                    name=player)
            bar_widget.addItem(bars)
            legend_data.append((color, player))
    return legend_data


@setup_plot
def create_horizontal_bar_graph(self, table: list[list], bar_widget: PlotWidget) -> QVBoxLayout:
    """
    Creates bar plot from table and returns layout in which the graph was inserted.

    Parameters:
    - :param table: overview table as generated by the parser
    - :param bar_widget: bar widget that will be plotted to (supplied by decorator)

    :return: layout containing the graph (returned by decorator)
    """
    left_axis = bar_widget.getAxis('left')
    left_axis.setTickFont(theme_font(self, 'app'))
    bar_widget.setDefaultPadding(padding=0.01)

    table.sort(key=lambda line: line[3], reverse=True)
    y_annotations = (tuple((index + 1, line[0] + line[1]) for index, line in enumerate(table)),)
    bar_widget.getAxis('left').setTicks(y_annotations)
    x = tuple(line[3] for line in table)
    y = tuple(range(1, len(x) + 1))
    bar_widget.setXRange(0, max(x) * 1.05, padding=0)
    bars = BarGraphItem(
            x0=0, y=y, height=0.75, width=x, brush=self.theme['defaults']['mfg'], pen=None)
    bar_widget.addItem(bars)


@setup_plot
def create_line_graph(
        self, data: dict[str, tuple], time_reference: dict[str, tuple],
        graph_widget: PlotWidget) -> QVBoxLayout:
    """
    Creates line plot from data and returns layout that countins the plot.

    Parameters:
    - :param data: dictionary containing the data to be plotted
    - :param time_reference: contains the time values for the data points
    - :param graph_widget: graph widget that will be plotted to (supplied by decorator)

    :return: layout containing the graph (returned by decorator)
    """
    bottom_axis = graph_widget.getAxis('bottom')
    bottom_axis.unit = 's'
    legend_data = list()

    for (player, graph_data), color in zip(data.items(), self.theme['plot']['color_cycler']):
        if player in time_reference:
            time_data = time_reference[player]
            graph_widget.plot(time_data, graph_data, pen=mkPen(color, width=1.5), name=player)
            legend_data.append((color, player))
    return legend_data


def create_legend(self, colors_and_names: Iterable[tuple]) -> QFrame:
    """
    Creates Legend from color / name pairs and returns frame containing it.

    Parameters:
    - :param colors_and_names: Iterable containing color / name pairs : [('#9f9f00', 'Line 1'),
    ('#0000ff', 'Line 2'), (...), ...]

    :return: frame containing the legend
    """
    frame = create_frame(self, style='plot_legend')
    upper_frame = create_frame(self, style='plot_legend')
    lower_frame = create_frame(self, style='plot_legend')
    frame_layout = QVBoxLayout()
    upper_layout = QHBoxLayout()
    lower_layout = QHBoxLayout()
    margin = self.theme['defaults']['margin']
    frame_layout.setContentsMargins(0, 0, 0, 0)
    frame_layout.setSpacing(margin)
    upper_layout.setContentsMargins(0, 0, 0, 0)
    upper_layout.setSpacing(2 * margin)
    lower_layout.setContentsMargins(0, 0, 0, 0)
    lower_layout.setSpacing(2 * margin)
    second_row = False
    for num, (color, name) in enumerate(colors_and_names, 1):
        legend_item = create_legend_item(self, color, name)
        if num <= 5:
            upper_layout.addWidget(legend_item)
        else:
            second_row = True
            lower_layout.addWidget(legend_item)
    upper_frame.setLayout(upper_layout)
    frame_layout.addWidget(upper_frame, alignment=ACENTER)
    if second_row:
        lower_frame.setLayout(lower_layout)
        frame_layout.addWidget(lower_frame, alignment=ACENTER)
    frame.setLayout(frame_layout)
    return frame


def create_legend_item(self, color: str, name: str) -> QFrame:
    """
    Creates a colored patch next to a label inside a frame

    Parameters:
    - :param color: patch color
    - :param name: text of the label

    :return: frame containing the legend item
    """
    frame = create_frame(self, style='plot_legend')
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(self.theme['defaults']['margin'])
    colored_patch = QLabel()
    colored_patch.setStyleSheet(get_style(self, 'plot_legend', {'background-color': color}))
    patch_height = self.theme['app']['frame_thickness']
    colored_patch.setFixedSize(2 * patch_height, patch_height)
    layout.addWidget(colored_patch, alignment=AVCENTER)
    label = create_label(
            self, name, 'label', style_override={'font': self.theme['plot_legend']['font']})
    layout.addWidget(label)
    frame.setLayout(layout)
    return frame


def create_overview_table(self, table_data) -> QTableView:
    """
    Creates the overview table and returns it.

    :return: Overview Table
    """
    table_cell_data = tuple(tuple(line[2:]) for line in table_data)
    table_index = tuple(line[0] + line[1] for line in table_data)
    model = OverviewTableModel(
            table_cell_data, TABLE_HEADER, table_index, self.theme_font('table_header'),
            self.theme_font('table'))
    sort = SortingProxy()
    sort.setSourceModel(model)
    table = QTableView(self.widgets.overview_tab_frames[0])
    table.setModel(sort)
    style_table(self, table)
    if self.settings.value('overview_sort_order') == 'Descending':
        sort_order = Qt.SortOrder.AscendingOrder
    else:
        sort_order = Qt.SortOrder.DescendingOrder
    table.sortByColumn(self.settings.value('overview_sort_column', type=int), sort_order)
    return table


def create_live_graph(self) -> tuple[QFrame, list]:
    """
    Creates and styles live graph.

    :return: Frame containing the graph and list of curves that will be used to plot the data
    """
    plot_widget = PlotWidget()
    plot_widget.setAxisItems({'left': CustomPlotAxis('left', compressed=True)})
    plot_widget.setAxisItems({'bottom': CustomPlotAxis('bottom', unit='s', no_labels=True)})
    plot_widget.setStyleSheet(get_style(self, 'plot_widget_nullifier'))
    plot_widget.setBackground(None)
    plot_widget.setMouseEnabled(False, False)
    plot_widget.setMenuEnabled(False)
    plot_widget.hideButtons()
    plot_widget.setDefaultPadding(padding=0)
    plot_widget.setXRange(-14, 0, padding=0)
    left_axis = plot_widget.getAxis('left')
    left_axis.setTickFont(theme_font(self, 'live_plot_widget'))
    left_axis.setTextPen(color=self.theme['defaults']['fg'])
    # left_axis.setTickDensity(0.1)
    bottom_axis = plot_widget.getAxis('bottom')
    bottom_axis.setTickFont(theme_font(self, 'plot_widget'))
    bottom_axis.setTextPen(color=self.theme['defaults']['fg'])

    curves = list()
    for color_index in range(5):
        color = self.theme['plot']['color_cycler'][color_index]
        curves.append(plot_widget.plot([0], [0], pen=mkPen(color, width=1)))

    frame = create_frame(self, None, 'plot_widget', size_policy=SMIXMAX, style_override={
            'margin': 4, 'padding': 2})
    frame.setMinimumWidth(self.sidebar_item_width * 0.25)
    frame.setMinimumHeight(self.sidebar_item_width * 0.25)
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(plot_widget, stretch=1)
    frame.setLayout(layout)
    return frame, curves


def update_live_display(
        self, data: dict, graph_active: bool = False, graph_data_buffer: list = [],
        graph_data_field: int = 0):
    """
    Updates display of live parser to show the new data.

    Parameters:
    - :param data: dictionary containing the new data
    - :param graph_active: Set to True to update the graph as well
    - :param graph_data_buffer: contains the past graph data
    """
    index = list()
    cells = list()
    curves = list()
    for player, player_data in data.items():
        index.append(player)
        cells.append(list(player_data.values()))
    if graph_active:
        if len(graph_data_buffer) == 0:
            graph_data_buffer.extend(([0] * 15, [0] * 15, [0] * 15, [0] * 15, [0] * 15))
        zipper = zip(graph_data_buffer, cells, self.widgets.live_parser_curves)
        for buffer_item, player_data, curve in zipper:
            buffer_item.pop(0)
            buffer_item.append(player_data[graph_data_field])
            curves.append((curve, buffer_item))
        if len(curves) > 0:
            self.live_parser_window.update_graph.emit(curves)

    if len(index) > 0 and len(cells) > 0:
        self.live_parser_window.update_table.emit((index, cells))


@Slot()
def update_live_table(self, data: tuple):
    """
    Updates the table of the live parser with the supplied data

    Parameters:
    - :param data: tuple containing two lists, that contain the index and cell values respectively
    """
    table = self.widgets.live_parser_table
    table.model().replace_data(*data)
    table.resizeColumnsToContents()
    table.resizeRowsToContents()


@Slot()
def update_live_graph(curve_data: list):
    """
    Updates the graph of the live parser with the supplied data

    Parameters:
    - :param curve_data: list containing pairs of curve items and data lists; curve items will be
    updated with the data
    """
    time_data = list(range(-14, 1))
    for curve, data_points in curve_data:
        curve.setData(time_data, data_points)
