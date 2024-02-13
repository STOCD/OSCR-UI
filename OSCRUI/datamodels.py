from PyQt6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel
from PyQt6.QtGui import QFont

from .OSCR import TABLE_HEADER

from .widgetbuilder import AVCENTER, ARIGHT, ACENTER

class TableModel(QAbstractTableModel):
    def __init__(self, data, header_font:QFont, cell_font:QFont):
        super().__init__()
        self._data = tuple(line[2:] for line in data)
        self._header = TABLE_HEADER
        self._index = tuple(f'{line[0]}{line[1]}' for line in data)
        self._header_font = header_font
        self._cell_font = cell_font
    
    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            current_col = index.column()
            cell = self._data[index.row()][current_col]
            column = index.column()
            if column == 0:
                return f'{cell:.1f}s'
            elif column in (1, 2, 7, 10, 13, 14, 15):
                return f'{cell:,.2f}'
            elif column in (3, 4, 5, 6, 8, 11, 12):
                return f'{cell:,.2f}%'
            elif column in (9, 16, 17, 18, 19, 20, 21, 22):
                return str(cell)
            return cell
        
        if role == Qt.ItemDataRole.FontRole:
            return self._cell_font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return AVCENTER + ARIGHT

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0]) # all columns must have the same length

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._header[section]
                #return TABLE_HEADER_CONVERSION[self._header[section]]

            if orientation == Qt.Orientation.Vertical:
                return self._index[section]

        if role == Qt.ItemDataRole.FontRole:
            return self._header_font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if orientation == Qt.Orientation.Horizontal:
                return ACENTER

            if orientation == Qt.Orientation.Vertical:
                return AVCENTER + ARIGHT

class SortingProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()

    def lessThan(self, left, right):
        l = self.sourceModel()._data[left.row()][left.column()]
        r = self.sourceModel()._data[right.row()][right.column()]
        return l < r