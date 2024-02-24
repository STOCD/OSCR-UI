from types import BuiltinFunctionType, FunctionType, MethodType

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFrame,
                               QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                               QPushButton, QSizePolicy, QTableView, QTreeView,
                               QVBoxLayout)

from .style import get_style, get_style_class, merge_style, theme_font

CALLABLE = (FunctionType, BuiltinFunctionType, MethodType)

SMINMIN = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
SMAXMAX = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
SMAXMIN = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
SMINMAX = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

ATOP = Qt.AlignmentFlag.AlignTop
ARIGHT = Qt.AlignmentFlag.AlignRight
ALEFT = Qt.AlignmentFlag.AlignLeft
ACENTER = Qt.AlignmentFlag.AlignCenter
AVCENTER = Qt.AlignmentFlag.AlignVCenter
AHCENTER = Qt.AlignmentFlag.AlignHCenter

RFIXED = QHeaderView.ResizeMode.Fixed

SMPIXEL = QAbstractItemView.ScrollMode.ScrollPerPixel


def create_button(self, text, style: str = "", parent=None, style_override={}):
    """
    Creates a button according to style with parent.

    Parameters:
    - :param text: text to be shown on the button
    - :param style: name of the style as in self.theme or style dict
    - :param parent: parent of the button (optional)
    - :param style_override: style dict to override default style (optional)

    :return: configured QPushButton
    """
    button = QPushButton(text, parent)
    button.setStyleSheet(get_style_class(self, "QPushButton", style, style_override))
    if "font" in style_override:
        button.setFont(theme_font(self, style, style_override["font"]))
    else:
        button.setFont(theme_font(self, style))
    button.setSizePolicy(SMAXMAX)
    return button


def create_icon_button(self, icon, style: str = "", parent=None, style_override={}):
    """
    Creates a button showing an icon according to style with parent.

    Parameters:
    - :param icon: icon to be shown on the button
    - :param style: name of the style as in self.theme or style dict
    - :param parent: parent of the button (optional)
    - :param style_override: style dict to override default style (optional)

    :return: configured QPushButton
    """
    button = QPushButton("", parent)
    button.setIcon(icon)
    button.setStyleSheet(get_style_class(self, "QPushButton", style, style_override))
    icon_size = self.theme["s.c"]["button_icon_size"]
    button.setIconSize(QSize(icon_size, icon_size))
    button.setSizePolicy(SMAXMAX)
    return button


def create_frame(self, parent=None, style="frame", style_override={}) -> QFrame:
    """
    Creates a frame with default styling and parent

    Parameters:
    - :param parent: parent of the frame (optional)
    - :param style: style dict to override default style (optional)

    :return: configured QFrame
    """
    frame = QFrame(parent)
    frame.setStyleSheet(get_style(self, style, style_override))
    frame.setSizePolicy(SMAXMAX)
    return frame


def create_label(self, text, style: str = "", parent=None, style_override={}):
    """
    Creates a label according to style with parent.

    Parameters:
    - :param text: text to be shown on the label
    - :param style: name of the style as in self.theme
    - :param parent: parent of the label (optional)
    - :param style_override: style dict to override default style (optional)

    :return: configured QLabel
    """
    label = QLabel(parent)
    label.setText(text)
    label.setStyleSheet(get_style(self, style, style_override))
    label.setSizePolicy(SMAXMAX)
    if "font" in style_override:
        label.setFont(theme_font(self, style, style_override["font"]))
    else:
        label.setFont(theme_font(self, style))
    return label


def create_button_series(
    self,
    parent,
    buttons: dict,
    style,
    shape: str = "row",
    seperator: str = "",
    ret=False,
):
    """
    Creates a row / column of buttons.

    Parameters:
    - :param parent: widget that will contain the buttons
    - :param buttons: dictionary containing button details
    - :param style: key for self.theme -> default style
    - :param shape: row / column
    - :param seperator: string seperator displayed between buttons (optional)

    :return: populated QVBoxlayout / QHBoxlayout
    """
    if "default" in buttons:
        defaults = merge_style(self, self.theme[style], buttons.pop("default"))
    else:
        defaults = self.theme[style]

    if shape == "column":
        layout = QVBoxLayout()
    else:
        shape = "row"
        layout = QHBoxLayout()

    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    button_list = []

    if seperator != "":
        sep_style = {
            "color": defaults["color"],
            "margin": 0,
            "padding": 0,
            "background": "rgba(0,0,0,0)",
        }

    for i, (name, detail) in enumerate(buttons.items()):
        if "style" in detail:
            button_style = merge_style(self, defaults, detail["style"])
        else:
            button_style = defaults
        bt = self.create_button(name, style, parent, button_style)
        if "callback" in detail and isinstance(detail["callback"], CALLABLE):
            bt.clicked.connect(detail["callback"])
        stretch = detail["stretch"] if "stretch" in detail else 0
        if "align" in detail:
            layout.addWidget(bt, stretch, detail["align"])
        else:
            layout.addWidget(bt, stretch)
        button_list.append(bt)
        if seperator != "" and i < (len(buttons) - 1):
            sep_label = self.create_label(seperator, "label", parent, sep_style)
            sep_label.setSizePolicy(SMAXMIN)
            layout.addWidget(sep_label)

    if ret:
        return layout, button_list
    else:
        return layout


def create_combo_box(
    self, parent, style: str = "combobox", style_override: dict = {}
) -> QComboBox:
    """
    Creates a combobox with given style and returns it.

    Parameters:
    - :param parent: parent of the combo box
    - :param style: key for self.theme -> default style
    - :param style_override: style dict to override default style

    :return: styled QCombobox
    """
    combo_box = QComboBox(parent)
    combo_box.setStyleSheet(get_style_class(self, "QComboBox", style, style_override))
    if "font" in style_override:
        combo_box.setFont(theme_font(self, style, style_override["font"]))
    else:
        combo_box.setFont(theme_font(self, style))
    combo_box.setSizePolicy(SMINMAX)
    return combo_box


def resize_tree_table(tree: QTreeView):
    """
    Resizes the columns of the given tree table to fit its contents

    Parameters:
    - :param tree: QTreeView -> tree to be resized
    """
    for col in range(tree.header().count()):
        width = max(tree.sizeHintForColumn(col), tree.header().sectionSizeHint(col)) + 5
        tree.header().resizeSection(col, width)


def create_analysis_table(self, parent, widget) -> QTreeView:
    """
    Creates and returns a QTreeView with parent, styled according to widget.

    Parameters:
    - :param parent: parent of the table
    - :param widget: style key for the table

    :return: configured QTreeView
    """
    table = QTreeView(parent)
    table.setStyleSheet(get_style_class(self, "QTreeView", widget))
    table.setSizePolicy(SMINMIN)
    table.setAlternatingRowColors(True)
    table.setHorizontalScrollMode(SMPIXEL)
    table.setVerticalScrollMode(SMPIXEL)
    table.setSortingEnabled(True)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.header().setStyleSheet(
        get_style_class(self, "QHeaderView", "tree_table_header")
    )
    table.header().setSectionResizeMode(RFIXED)
    # table.header().setSectionsMovable(False)
    table.header().setMinimumSectionSize(1)
    table.header().setSectionsClickable(True)
    table.header().setStretchLastSection(False)
    table.header().setSortIndicatorShown(False)
    table.expanded.connect(lambda: resize_tree_table(table))
    table.collapsed.connect(lambda: resize_tree_table(table))
    return table


def style_table(self, table: QTableView):
    """
    Styles the given table.

    Parameters:
    - :param table: table to be styled
    """
    table.setAlternatingRowColors(self.theme["s.c"]["table_alternate"])
    table.setShowGrid(self.theme["s.c"]["table_gridline"])
    table.setSortingEnabled(True)
    table.setStyleSheet(get_style_class(self, "QTableView", "table"))
    table.setHorizontalScrollMode(SMPIXEL)
    table.setVerticalScrollMode(SMPIXEL)
    table.horizontalHeader().setStyleSheet(
        get_style_class(self, "QHeaderView", "table_header")
    )
    table.verticalHeader().setStyleSheet(
        get_style_class(self, "QHeaderView", "table_index")
    )
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    table.horizontalHeader().setSortIndicatorShown(False)
    table.horizontalHeader().setSectionResizeMode(RFIXED)
    table.verticalHeader().setSectionResizeMode(RFIXED)
    table.setSizePolicy(SMINMIN)


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
    error.setWindowIcon(self.icons["oscr"])
    error.exec()
