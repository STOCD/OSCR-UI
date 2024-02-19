from PyQt6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QAbstractItemModel, QModelIndex
from PyQt6.QtGui import QFont
import sys
from OSCR import TABLE_HEADER, TreeItem

from .widgetbuilder import AVCENTER, ARIGHT, ACENTER, ALEFT

class TableModel(QAbstractTableModel):
    def __init__(self, data, header_font: QFont, cell_font: QFont):
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
    
class TreeSortingProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()

    def lessThan(self, left, right):
        l = self.sourceModel().data(left, -13)
        r = self.sourceModel().data(right, -13)
        if l is None and r is None:
            return True
        return l < r
    
class TreeModel(QAbstractItemModel):
    """
    Data model for the analysis table
    """
    def __init__(self, root_item, header_font, name_font, cell_font):
        """
        Initializes Tree Model with data in root item.

        Parameters:
        - :param root_item: item supporting the following operations:
            - function "get_child(row: int)" returning the n-th child of the item; None if not exists
            - function "get_data(column: int)" returning the data of the item at the given column; None if
            not exists
            - function "append_child(item)" adds the given item as child to the item 
            - property "parent" containing the parent item of the item; None for the root item
            - property "row" containing the row number which the item is stored at in its parent item
            - property "child_count" containing the number of children the item has
            - property "column_count" containing the number of columns the items data row

        The item may already contain childen.
        """
        super().__init__()
        self._root = root_item
        self._root_index = self.createIndex(0, 0, self._root)
        self._header_font = header_font
        self._name_font = name_font
        self._cell_font = cell_font

    def sort(self, column: int, order: Qt.SortOrder):
        if order == Qt.SortOrder.AscendingOrder:
            descending = True
        else:
            descending = False
        self.layoutAboutToBeChanged.emit()
        self.recursive_sort(self._root._children[0], column, descending)
        self.recursive_sort(self._root._children[1], column, descending)
        self.layoutChanged.emit()
    
    def recursive_sort(self, item: TreeItem, column: int, desc):
        if item.child_count > 0:
            for child in item._children:
                self.recursive_sort(child, column, desc)
            item._children.sort(key=lambda row: row.get_data(column), reverse=desc)

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex | None:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            p = self._root
        else:
            p = parent.internalPointer()
        c = p.get_child(row)
        if not c is None:
            return self.createIndex(row, column, c)
        return QModelIndex()
    
    def parent(self, index: QModelIndex) -> QModelIndex | None:
        if not index.isValid():
            return QModelIndex()
        child = index.internalPointer()
        parent = child.parent
        if parent is None:
            return QModelIndex()
        return self.createIndex(parent.row, 0, parent)
    
    def rowCount(self, parent: QModelIndex) -> int:
        if not parent.isValid():
            parent = self._root
        else:
            parent = parent.internalPointer()
        return parent.child_count
    
    def columnCount(self, parent: QModelIndex) -> int:
        if parent.isValid():
            return parent.internalPointer().column_count
        return self._root.column_count
    
    def data(self, index: QModelIndex, role: int) -> str:
        if not index.isValid():
            return ''
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            data = index.internalPointer().get_data(column)
            if data == '':
                return ''
            if column == 0:
                if isinstance(data, tuple):
                    return ''.join(data)
                return data
            elif column in (3, 5, 6, 7):
                return f'{data * 100:,.2f}%'
            elif column in (1, 2, 4, 13, 14, 15, 16, 17, 18):
                return f'{data:,.2f}'
            elif column in (8, 9, 10, 11, 12, 20, 21):
                return f'{data:,.0f}'
            elif column == 19 and data:
                return f'{data}s'
        elif role == Qt.ItemDataRole.FontRole:
            if column == 0:
                return self._name_font
            return self._cell_font
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column != 0:
                return AVCENTER + ARIGHT
            else:
                return AVCENTER + ALEFT
        elif role == -13:
            return index.internalPointer().get_data(column)
        return None
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index)
    
    def headerData(self, section, orientation, role) -> str:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._root.data[section]
        elif role == Qt.ItemDataRole.FontRole:
            return self._header_font
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return ACENTER
        return None
