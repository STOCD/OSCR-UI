from typing import Callable, Iterable

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QTableView, QFrame, QLabel
from pyqtgraph import PlotWidget, BarGraphItem, setConfigOptions, mkPen
import numpy as np

from OSCR import TABLE_HEADER
from OSCR.combat import Combat

from .datamodels import OverviewTableModel, SortingProxy
from .widgetbuilder import SMINMIN, AVCENTER, ACENTER, create_frame, create_label, style_table
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
        frame = create_frame(self, None, 'plot_widget')
        frame.setSizePolicy(SMINMIN)
        frame.setLayout(inner_layout)
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        # if stretch ever needs to be variable, create argument for decorator
        outer_layout.addWidget(frame, stretch=11)
        return outer_layout
    return plot_wrapper


def _create_overview(combat: Combat) -> tuple:
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

    time_data, DPS_graph_data, DMG_graph_data, current_table = _create_overview(self.parser1.active_combat)

    line_layout = create_line_graph(self, DPS_graph_data, time_data)
    self.widgets.overview_tab_frames[1].setLayout(line_layout)

    group_bar_layout = create_grouped_bar_plot(self, DMG_graph_data, time_data)
    self.widgets.overview_tab_frames[2].setLayout(group_bar_layout)

    bar_layout = create_horizontal_bar_graph(self, current_table)
    self.widgets.overview_tab_frames[0].setLayout(bar_layout)

    tbl = create_overview_table(self, current_table)
    bar_layout.addWidget(tbl, stretch=4)


@setup_plot
def create_grouped_bar_plot(self, data: dict[str, tuple], time_reference: dict[str, tuple], 
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
    bar_width = group_width / player_num
    relative_bar_positions = np.linspace(0+bar_width/2, group_width-bar_width/2, player_num)
    bar_position_offsets = relative_bar_positions - np.median(relative_bar_positions)

    zipper = zip(data.items(), self.theme['plot']['color_cycler'], bar_position_offsets)
    for (player, graph_data), color, offset in zipper:
        if player in time_reference:
            time_data = np.subtract(time_reference[player], offset)
            bars = BarGraphItem(x=time_data, width=bar_width, height=graph_data, brush=color, pen=None, 
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

    y_annotations = (tuple((index+1, line[0]+line[1]) for index, line in enumerate(table)),)
    bar_widget.getAxis('left').setTicks(y_annotations)
    x = tuple(line[3] for line in table)
    y = tuple(range(1, len(x) + 1))
    bar_widget.setXRange(0, max(x) * 1.05, padding=0)
    bars = BarGraphItem(x0=0, y=y, height=0.75, width=x, brush=self.theme['defaults']['mfg'], pen=None)
    bar_widget.addItem(bars)

@setup_plot
def create_line_graph(self, data: dict[str, tuple], time_reference: dict[str, tuple], 
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
    colored_patch.setFixedSize(2*patch_height, patch_height)
    layout.addWidget(colored_patch, alignment=AVCENTER)
    label = create_label(self, name, 'label', style_override={'font': self.theme['plot_legend']['font']})
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
    model = OverviewTableModel(table_cell_data, TABLE_HEADER, table_index, 
            self.theme_font('table_header'), self.theme_font('table'))
    sort = SortingProxy()
    sort.setSourceModel(model)
    table = QTableView(self.widgets.overview_tab_frames[0])
    table.setModel(sort)
    style_table(self, table)
    for col in range(len(model._header)):
        table.horizontalHeader().resizeSection(col, table.horizontalHeader().sectionSize(col) + 5)
    return table
