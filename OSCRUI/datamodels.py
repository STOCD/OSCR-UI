from typing import Iterable
import sys

from OSCR import TreeItem
from PySide6.QtCore import QAbstractItemModel, QAbstractTableModel, QItemSelectionModel
from PySide6.QtCore import QItemSelection, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QFont

ARIGHT = Qt.AlignmentFlag.AlignRight
ALEFT = Qt.AlignmentFlag.AlignLeft
ACENTER = Qt.AlignmentFlag.AlignCenter
AVCENTER = Qt.AlignmentFlag.AlignVCenter


class TableModel(QAbstractTableModel):
    def __init__(
            self, data, header: Iterable, index: Iterable, header_font: QFont, cell_font: QFont):
        """
        Creates table model from supplied data.

        Parameters:
        - :param data: data to be displayed without index or header; two-dimensional iterable;
        must support .extend() function
        - :param header: column headings
        - :param index: row index
        - :param header_font: font to style the column headings with
        - :param cell_font: font to style the cells with
        """
        super().__init__()
        self._data = data
        self._header = tuple(header)
        self._index = list(index)
        self._header_font = header_font
        self._cell_font = cell_font

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        try:
            return len(self._data[0])  # all columns must have the same length
        except IndexError:
            return 0

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._header[section]

            if orientation == Qt.Orientation.Vertical:
                return self._index[section]

        if role == Qt.ItemDataRole.FontRole:
            return self._header_font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if orientation == Qt.Orientation.Horizontal:
                return ACENTER

            if orientation == Qt.Orientation.Vertical:
                return AVCENTER + ARIGHT


class OverviewTableModel(TableModel):
    """
    Model for overview table
    """
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


class LeagueTableModel(TableModel):
    """
    Model for league table
    """
    def __init__(self, *ar, combatlog_id_list: list = [], **kw):
        super().__init__(*ar, **kw)
        self._combatlog_id_list = combatlog_id_list

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            current_col = index.column()
            cell = self._data[index.row()][current_col]
            column = index.column()
            if column == 5:
                return f'{cell:.1f}s'
            elif column in (2, 3, 7):
                return f'{cell:,.2f}'
            elif column == 8:
                return f'{cell:,.2f}%'
            elif column == 4:
                return str(cell)
            return cell

        if role == Qt.ItemDataRole.FontRole:
            return self._cell_font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 1:
                return AVCENTER + ALEFT
            return AVCENTER + ARIGHT

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.FontRole and orientation == Qt.Orientation.Vertical:
            return self._cell_font
        return super().headerData(section, orientation, role)

    def extend_data(self, index: list, rows: list, combatlog_ids: list):
        current_row_count = len(self._index)
        self.beginInsertRows(QModelIndex(), current_row_count, current_row_count + len(index) - 1)
        self._index.extend(index)
        self._data.extend(rows)
        self._combatlog_id_list.extend(combatlog_ids)
        self.endInsertRows()


class LiveParserTableModel(TableModel):
    """
    Model for LiveParser Table
    """
    def __init__(self, *args, legend_col=None, colors=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._legend_column = legend_col
        if colors is not None:
            self._colors = [QColor.fromString(color) for color in colors]
        else:
            self._colors = None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            column = index.column()
            data = self._data[index.row()][column]
            if column in (0, 4):
                return f'{data:,.2f}'
            elif column == 1:
                return f'{data:.1f}s'
            elif column == 2:
                if data == 0:
                    return '---.--%'
                return f'{data:,.2f}%'
            elif column == 3:
                return f'{data:,.2f}%'
            return str(data)

        if role == Qt.ItemDataRole.FontRole:
            return self._cell_font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return AVCENTER + ARIGHT

        if role == Qt.ItemDataRole.DecorationRole:
            if self._legend_column is not None and index.column() == self._legend_column:
                row = index.row()
                if row < len(self._colors):
                    return self._colors[row]
            return None

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._header[section]

            if orientation == Qt.Orientation.Vertical:
                try:
                    return self._index[section]
                except IndexError:
                    sys.stdout.write(f'Section:{section}|Data{self._data}|Index{self._index}\n')

        if role == Qt.ItemDataRole.FontRole:
            return self._header_font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if orientation == Qt.Orientation.Horizontal:
                return ACENTER

            if orientation == Qt.Orientation.Vertical:
                return AVCENTER + ARIGHT

    def replace_data(self, index: list, rows: list):
        self.beginResetModel()
        self._index = index
        self._data = rows
        self.endResetModel()


class SortingProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self._name_filter: str = ''

    @property
    def name_filter(self) -> str:
        return self._name_filter

    @name_filter.setter
    def name_filter(self, filter_value: str):
        self._name_filter = filter_value
        self.invalidateFilter()

    def lessThan(self, left, right):
        links = self.sourceModel()._data[left.row()][left.column()]
        rechts = self.sourceModel()._data[right.row()][right.column()]
        return links > rechts  # inverted operator to make descending sort come up first

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        filter_value = self.name_filter
        if filter_value:
            full_name = ''.join(self.sourceModel()._data[source_row][0:2]).casefold()
            return filter_value.casefold() in full_name
        return True


class TreeModel(QAbstractItemModel):
    """
    Data model for the analysis table
    """
    def __init__(self, root_item, header_font: QFont, name_font: QFont, cell_font: QFont):
        """
        Initializes Tree Model with data in root item.

        Parameters:
        - :param root_item: item supporting the following operations:
            - function "get_child(row: int)" returning the n-th child of the item; None if not
            exists
            - function "get_data(column: int)" returning the data of the item at the given column;
            None if
            not exists
            - function "append_child(item)" adds the given item as child to the item
            - property "parent" containing the parent item of the item; None for the root item
            - property "row" containing the row number which the item is stored at in its parent
            item
            - property "child_count" containing the number of children the item has
            - property "column_count" containing the number of columns the items data row

        The item may already contain childen.
        - :param header_font: font used for the header
        - :param name_font: font used for the first column
        - :param cell_font: font used for the second to last column
        """
        super().__init__()
        self._root = root_item
        self._root_index = self.createIndex(0, 0, self._root)
        self._header_font = header_font
        self._name_font = name_font
        self._cell_font = cell_font
        if root_item.get_child(0).get_data(0) == 'Player':
            self._player = root_item.get_child(0)
            self._npc = root_item.get_child(1)
        else:
            self._player = root_item.get_child(1)
            self._npc = root_item.get_child(0)

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
        if c is not None:
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


class DamageTreeModel(TreeModel):
    """
    Tree Model subclass for the damage tables
    """
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
            elif column == 19:
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


class HealTreeModel(TreeModel):
    """
    Tree Model subclass for the heal tables
    """
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
            elif column == 8:
                return f'{data * 100:,.2f}%'
            elif column in (1, 2, 3, 4, 5, 6, 7, 17, 18):
                return f'{data:,.2f}'
            elif column in (9, 10, 12, 13):
                return f'{data:,.0f}'
            elif column == 11:
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


class TreeSelectionModel(QItemSelectionModel):
    """
    Implements custom selection behavior for analysis tables.
    """
    def __init__(self, model: QAbstractItemModel):
        super().__init__(model)

    def select(
            self, index_or_selection: QModelIndex | QItemSelection,
            flag: QItemSelectionModel.SelectionFlag):
        if isinstance(index_or_selection, QItemSelection):
            try:
                if index_or_selection.indexes()[0].column() == 0:
                    super().select(
                        index_or_selection, flag | QItemSelectionModel.SelectionFlag.Rows)
                else:
                    super().select(index_or_selection, flag)
            # deselecting has empty list of indexes
            except IndexError:
                super().select(index_or_selection, QItemSelectionModel.SelectionFlag.Clear)
        else:
            if index_or_selection.isValid():
                super().select(index_or_selection, flag)
            else:
                self.clear()
