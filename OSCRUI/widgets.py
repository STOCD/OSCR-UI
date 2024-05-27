from math import sqrt, floor, frexp

import numpy as np
from pyqtgraph import AxisItem, BarGraphItem, PlotWidget
from PySide6.QtCore import QRect, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QMouseEvent, QPixmap, QPainter, QFont
from PySide6.QtWidgets import QComboBox, QFrame, QListWidget, QPushButton, QSizeGrip, QSplitter
from PySide6.QtWidgets import QTableView, QTabWidget, QTreeView, QWidget

from .widgetbuilder import SMINMIN


class WidgetStorage():
    """
    Class to store widgets.
    """
    def __init__(self):
        self.main_menu_buttons: list[QPushButton] = list()
        self.main_tabber: QTabWidget
        self.main_tab_frames: list[QFrame] = list()
        self.sidebar_tabber: QTabWidget
        self.sidebar_tab_frames: list[QFrame] = list()
        self.map_tabber: QTabWidget
        self.map_tab_frames: list[QFrame] = list()
        self.map_menu_buttons: list[QPushButton] = list()

        self.navigate_up_button: QPushButton
        self.navigate_down_button: QPushButton

        self.overview_menu_buttons: list[QPushButton] = list()
        self.overview_tabber: QTabWidget
        self.overview_tab_frames: list[QFrame] = list()
        self.overview_table_frame: QFrame
        self.overview_table_button: FlipButton

        self.analysis_menu_buttons: list[QPushButton] = list()
        self.analysis_copy_combobox: QComboBox
        self.analysis_tabber: QTabWidget
        self.analysis_tab_frames: list[QFrame] = list()
        self.analysis_table_dout: QTreeView
        self.analysis_table_dtaken: QTreeView
        self.analysis_table_hout: QTreeView
        self.analysis_table_hin: QTreeView
        self.analysis_plot_dout: AnalysisPlot
        self.analysis_plot_dtaken: AnalysisPlot
        self.analysis_plot_hout: AnalysisPlot
        self.analysis_plot_hin: AnalysisPlot

        self.ladder_selector: QListWidget
        self.favorite_ladder_selector: QListWidget
        self.season_ladder_selector: QListWidget
        self.ladder_table: QTableView

        self.live_parser_table: QTableView
        self.live_parser_button: QPushButton
        self.live_parser_curves: list
        self.live_parser_splitter: QSplitter

    @property
    def analysis_table(self):
        return (self.analysis_table_dout, self.analysis_table_dtaken, self.analysis_table_hout,
                self.analysis_table_hin)


class FlipButton(QPushButton):
    """
    QPushButton with two sets of commands, texts and icons that alter on click.
    """
    def __init__(self, r_text, l_text, parent, checkable=False, *ar, **kw):
        super().__init__(r_text, parent, *ar, **kw)
        self._r = True
        self._checkable = checkable
        if checkable:
            self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._r_text = r_text
        self._l_text = l_text
        self.setText(r_text)
        self.r_function = self._f
        self.l_function = self._f
        self._r_icon = None
        self._l_icon = None
        self._r_tooltip = ''
        self._l_tooltip = ''
        self.clicked.connect(self.flip)

    @Slot()
    def flip(self):
        if self._r:
            self.r_function()
            if self._l_icon is not None:
                self.setIcon(self._l_icon)
            self.setText(self._l_text)
            self.setToolTip(self._l_tooltip)
            self._r = not self._r
            if self._checkable:
                self.setChecked(True)
        else:
            self.l_function()
            if self._r_icon is not None:
                self.setIcon(self._r_icon)
            self.setText(self._r_text)
            self.setToolTip(self._r_tooltip)
            self._r = not self._r
            if self._checkable:
                self.setChecked(False)

    def set_icon_r(self, icon: QIcon):
        self._r_icon = icon
        if self._r:
            self.setIcon(icon)

    def set_icon_l(self, icon: QIcon):
        self._l_icon = icon
        if not self._r:
            self.setIcon(icon)

    def set_text_r(self, text):
        self._r_text = text
        if self._r:
            self.setText(text)

    def set_text_l(self, text):
        self._l_text = text
        if not self._r:
            self.setText(text)

    def set_tooltip_r(self, text):
        self._r_tooltip = text
        if self._r:
            self.setToolTip(text)

    def set_tooltip_l(self, text):
        self._l_tooltip = text
        if not self._r:
            self.setToolTip(text)

    def configure(self, settings):
        self.set_icon_r(settings['icon_r'])
        self.set_icon_l(settings['icon_l'])
        self.r_function = settings['func_r']
        self.l_function = settings['func_l']
        self.set_tooltip_r(settings['tooltip_r'])
        self.set_tooltip_l(settings['tooltip_l'])

    def _f(self):
        return


class BannerLabel(QWidget):
    """
    Label displaying image that resizes according to its parents width while preserving aspect
    ratio.
    """
    def __init__(self, path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setPixmap(QPixmap(path))
        self.setSizePolicy(SMINMIN)
        self.setMinimumHeight(10)  # forces visibility

    def setPixmap(self, p):
        self.p = p
        self.update()

    def paintEvent(self, event):
        if not self.p.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            w = int(self.rect().width())
            h = int(w * 126 / 2880)
            rect = QRect(0, 0, w, h)
            painter.drawPixmap(rect, self.p)
            self.setMaximumHeight(h)
            self.setMinimumHeight(h)


class CustomPlotAxis(AxisItem):
    """
    Extending AxisItem for custom tick formatting
    """
    def __init__(self, *args, unit: str = '', no_labels=False, compressed=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._unit = ' ' + unit
        self._no_labels = no_labels
        self._compressed = compressed

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        self._unit = ' ' + value

    def tickStrings(self, values, scale, spacing):
        if self._no_labels:
            return []

        if self.logMode:
            return self.logTickStrings(values, scale, spacing)

        strings = list()
        for tick in values:
            if tick >= 1000000:
                strings.append(f'{tick / 1000000:.2f} M{self._unit}')
            elif tick >= 1000:
                strings.append(f'{tick / 1000:.0f} k{self._unit}')
            else:
                strings.append(f'{tick:.0f}{self._unit}')
        return strings

    def tickSpacing(self, minVal, maxVal, size):
        """Return values describing the desired spacing and offset of ticks.

        This method is called whenever the axis needs to be redrawn and is a
        good method to override in subclasses that require control over tick locations.

        The return value must be a list of tuples, one for each set of ticks::

            [
                (major tick spacing, offset),
                (minor tick spacing, offset),
                (sub-minor tick spacing, offset),
                ...
            ]
        """
        # almost the original implementation of tickSpacing
        if self._tickSpacing is not None:
            return self._tickSpacing

        dif = abs(maxVal - minVal)
        if dif == 0:
            return []

        ref_size = 300.
        minNumberOfIntervals = max(2.25, 2.25 * self._tickDensity * sqrt(size / ref_size))

        majorMaxSpacing = dif / minNumberOfIntervals

        mantissa, exp2 = frexp(majorMaxSpacing)
        p10unit = 10. ** (floor((exp2 - 1) / 3.32192809488736) - 1)
        if 100. * p10unit <= majorMaxSpacing:
            majorScaleFactor = 10
            p10unit *= 10.
        else:
            if self._compressed:
                scale_factors = (50, 30, 20, 10)
            else:
                scale_factors = (50, 20, 10)
            for majorScaleFactor in scale_factors:
                if majorScaleFactor * p10unit <= majorMaxSpacing:
                    break
        majorInterval = majorScaleFactor * p10unit

        minorMinSpacing = 2 * dif / size
        if majorScaleFactor == 10:
            trials = (5, 10)
        else:
            trials = (10, 20, 50)
        for minorScaleFactor in trials:
            minorInterval = minorScaleFactor * p10unit
            if minorInterval >= minorMinSpacing:
                break
        levels = [
            (majorInterval, 0),
            (minorInterval, 0)
        ]

        if self.style['maxTickLevel'] >= 2:
            if majorScaleFactor == 10:
                trials = (1, 2, 5, 10)
            elif majorScaleFactor == 20:
                trials = (2, 5, 10, 20)
            elif majorScaleFactor == 50:
                trials = (5, 10, 50)
            else:
                trials = ()
                extraInterval = minorInterval
            for extraScaleFactor in trials:
                extraInterval = extraScaleFactor * p10unit
                if extraInterval >= minorMinSpacing or extraInterval == minorInterval:
                    break
            if extraInterval < minorInterval:
                levels.append((extraInterval, 0))
        return levels


class AnalysisPlot(PlotWidget):
    """
    PlotWidget for plotting the analysis plot.
    """
    def __init__(self, colors: tuple, tick_color: str, tick_font: QFont, legend_layout):
        """
        Parameters:
        - :param colors: tuple with at least 5 different colors that are used to paint the bars
        - :param tick_color: color for the tick annotations
        - :param tick_font: font for the tick annotations
        """
        super().__init__()
        self._bar_queue = list()
        self._legend_queue = list()
        self._bar_item_queue = list()
        self._bar_position = 0
        self._colors = colors
        self._frozen = True
        self._legend_layout = legend_layout
        left_axis = CustomPlotAxis('left')
        left_axis.setTickFont(tick_font)
        left_axis.setTextPen(color=tick_color)
        bottom_axis = CustomPlotAxis('bottom', unit='s')
        bottom_axis.setTickFont(tick_font)
        bottom_axis.setTextPen(color=tick_color)
        self.setAxisItems({'left': left_axis, 'bottom': bottom_axis})
        self.setBackground(None)
        self.setMouseEnabled(False, False)
        self.setMenuEnabled(False)
        self.hideButtons()
        self.setDefaultPadding(padding=0)

    def add_bar(self, item):
        """
        Adds plot item to plot widget and removes plot item if there are more than 5 currently
        displayed.

        Parameters:
        - :param item: object with property ".graph_data", containing the height of the bars

        :return: returns the color that the graph was created with for the legend
        """
        if self._frozen or item in self._bar_item_queue:
            return
        data = item.graph_data
        time_reference = np.arange(len(data))
        group_width = 0.9
        bar_width = group_width / 5
        bar_offset = - (group_width / 2) + 0.5 * bar_width + self._bar_position * bar_width
        time_data = np.subtract(time_reference, bar_offset)
        brush_color = self._colors[self._bar_position]
        bars = BarGraphItem(x=time_data, width=bar_width, height=data, brush=brush_color, pen=None)
        if len(self._bar_queue) >= 5:
            self.removeItem(self._bar_queue.pop(0))
            self._bar_item_queue.pop(0)
            legend_item_to_remove = self._legend_queue.pop(0)
            self._legend_layout.removeWidget(legend_item_to_remove)
            legend_item_to_remove.setParent(None)
        self._bar_queue.append(bars)
        self._bar_item_queue.append(item)
        self.addItem(bars)
        self._bar_position += 1
        if self._bar_position >= 5:
            self._bar_position = 0
        return brush_color

    def add_legend_item(self, legend_item: QFrame):
        self._legend_queue.append(legend_item)
        self._legend_layout.addWidget(legend_item)

    def clear_plot(self):
        """
        Removes all bars from the plot
        """
        for bar in self._bar_queue:
            self.removeItem(bar)
        self._bar_queue = list()
        for legend_item in self._legend_queue:
            self._legend_layout.removeWidget(legend_item)
            legend_item.setParent(None)
        self._legend_queue = list()
        self._bar_item_queue = list()
        self._bar_position = 0

    def toggle_freeze(self, state):
        """
        Freezes when unfrozen, unfreezes when frozen
        """
        self._frozen = not self._frozen


class SizeGrip(QSizeGrip):
    """
    Overrides mouse event functions to stop event propagation
    """
    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        event.accept()


class LiveParserWindow(QFrame):
    """
    Subclass of QWidget providing two custom signals: update_table and update_graph
    """
    update_table = Signal(tuple)
    update_graph = Signal(list)
