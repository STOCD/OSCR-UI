from PySide6.QtWidgets import QWidget, QPushButton, QTabWidget, QFrame, QTreeView, QComboBox, QTableView
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import QRect, Slot
from pyqtgraph import AxisItem

from .widgetbuilder import SMINMIN

class FlipButton(QPushButton):
    """
    QPushButton with two sets of commands, texts and icons that alter on click.
    """
    def __init__(self, r_text, l_text, parent, *ar, **kw):
        super().__init__(r_text, parent, *ar, **kw)
        self._r = True
        self._r_text = r_text
        self._l_text = l_text
        self.setText(r_text)
        self._r_function = self._f
        self._l_function = self._f
        self._r_icon = None
        self._l_icon = None
        self.clicked.connect(self.flip)

    @Slot()
    def flip(self):
        if self._r:
            self._r_function()
            self.setIcon(self._l_icon)
            self.setText(self._l_text)
            self._r = not self._r
        else:
            self._l_function()
            self.setIcon(self._r_icon)
            self.setText(self._r_text)
            self._r = not self._r

    def set_icon_r(self, icon:QIcon):
        self._r_icon = icon
        if self._r:
            self.setIcon(icon)

    def set_icon_l(self, icon:QIcon):
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

    def set_func_r(self, func):
        self._r_function = func

    def set_func_l(self, func):
        self._l_function = func
            
    def configure(self, settings):
        self.set_icon_r(settings['icon_r'])
        self.set_icon_l(settings['icon_l'])
        self.set_func_r(settings['func_r'])
        self.set_func_l(settings['func_l'])

    def _f(self):
        return

class BannerLabel(QWidget):
    """
    Label displaying image that resizes according to its parents width while preserving aspect ratio.
    """
    def __init__(self, path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setPixmap(QPixmap(path))
        self.setSizePolicy(SMINMIN)
        self.setMinimumHeight(10) # forces visibility

    def setPixmap(self, p):
        self.p = p
        self.update()

    def paintEvent(self, event):
        if not self.p.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            w = int(self.rect().width())
            h = int(w * 126/2880)
            rect = QRect(0, 0, w, h)
            painter.drawPixmap(rect, self.p)
            self.setMaximumHeight(h)
            self.setMinimumHeight(h)

class CustomPlotAxis(AxisItem):
    """
    Extending AxisItem for custom tick formatting
    """
    def __init__(self, *args, unit: str = '', **kwargs):
        super().__init__(*args, **kwargs)
        self._unit = ' ' + unit

    @property
    def unit(self):
        return self._unit
    
    @unit.setter
    def unit(self, value):
        self._unit = ' ' + value

    def tickStrings(self, values, scale, spacing):
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
    
class WidgetStorage():
    """
    Class to store widgets.
    """
    def __init__(self):
        self.main_menu_buttons: list[QPushButton] = list()
        self.main_tabber: QTabWidget
        self.main_tab_frames: list[QFrame] = list()

        self.overview_menu_buttons: list[QPushButton] = list()
        self.overview_tabber: QTabWidget
        self.overview_tab_frames: list[QFrame] = list()
        
        self.analysis_menu_buttons: list[QPushButton] = list()
        self.analysis_tabber: QTabWidget
        self.analysis_tab_frames: list[QFrame] = list()
        self.analysis_table_dout: QTreeView
        self.analysis_table_dtaken: QTreeView
        self.analysis_table_hout: QTreeView
        self.analysis_table_hin: QTreeView

        self.ladder_map: QComboBox
        self.ladder_table: QTableView
