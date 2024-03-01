from types import FunctionType, BuiltinFunctionType, MethodType
import os

from PySide6.QtWidgets import QPushButton, QFrame, QLabel, QTreeView, QHeaderView, QTableView, QSpacerItem
from PySide6.QtWidgets import QSizePolicy, QAbstractItemView, QMessageBox, QComboBox, QDialog, QLineEdit
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIntValidator

from OSCR import split_log_by_lines, split_log_by_combat
from .style import get_style_class, get_style, merge_style, theme_font
from .textedit import format_path
from .iofunctions import browse_path

CALLABLE = (FunctionType, BuiltinFunctionType, MethodType)

SMINMIN = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
SMAXMAX = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
SMAXMIN = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
SMINMAX = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
SMAX = QSizePolicy.Policy.Maximum
SMIN = QSizePolicy.Policy.Minimum
SEXPAND = QSizePolicy.Policy.Expanding
SFIXED = QSizePolicy.Policy.Fixed

ATOP = Qt.AlignmentFlag.AlignTop
ABOTTOM = Qt.AlignmentFlag.AlignBottom
ARIGHT = Qt.AlignmentFlag.AlignRight
ALEFT = Qt.AlignmentFlag.AlignLeft
ACENTER = Qt.AlignmentFlag.AlignCenter
AVCENTER = Qt.AlignmentFlag.AlignVCenter
AHCENTER = Qt.AlignmentFlag.AlignHCenter

RFIXED = QHeaderView.ResizeMode.Fixed

SMPIXEL = QAbstractItemView.ScrollMode.ScrollPerPixel

def create_button(self, text, style: str = 'button', parent=None, style_override={}, toggle=None):
    """
    Creates a button according to style with parent.

    Parameters:
    - :param text: text to be shown on the button
    - :param style: name of the style as in self.theme or style dict
    - :param parent: parent of the button (optional)
    - :param style_override: style dict to override default style (optional)
    - :param toggle: True or False when button should be a toggle button, None when it should be a normal 
    button; the bool value indicates the default state of the button

    :return: configured QPushButton
    """
    button = QPushButton(text, parent)
    button.setStyleSheet(get_style_class(self, 'QPushButton', style, style_override))
    if 'font' in style_override:
        button.setFont(theme_font(self, style, style_override['font']))
    else:
        button.setFont(theme_font(self, style))
    button.setSizePolicy(SMAXMAX)
    if isinstance(toggle, bool):
        button.setCheckable(True)
        button.setChecked(toggle)
    return button

def create_icon_button(self, icon, tooltip: str = '', style: str = 'icon_button', parent=None,
        style_override={}) -> QPushButton:
    """
    Creates a button showing an icon according to style with parent.

    Parameters:
    - :param icon: icon to be shown on the button
    - :param tooltip: text to show when the mouse pointer is on the button
    - :param style: name of the style as in self.theme or style dict
    - :param parent: parent of the button (optional)
    - :param style_override: style dict to override default style (optional)

    :return: configured QPushButton
    """
    button = QPushButton('', parent)
    button.setIcon(icon)
    if tooltip:
        button.setToolTip(tooltip)
    button.setStyleSheet(get_style_class(self, 'QPushButton', style, style_override))
    icon_size = self.theme['s.c']['button_icon_size']
    button.setIconSize(QSize(icon_size, icon_size))
    button.setSizePolicy(SMAXMAX)
    return button

def create_frame(self, parent=None, style='frame', style_override={}, size_policy=None) -> QFrame:
    """
    Creates a frame with default styling and parent

    Parameters:
    - :param parent: parent of the frame (optional)
    - :param style: style dict to override default style (optional)
    - :param size_policy: size policy of the frame (optional)

    :return: configured QFrame
    """
    frame = QFrame(parent)
    frame.setStyleSheet(get_style(self, style, style_override))
    frame.setSizePolicy(size_policy if isinstance(size_policy, QSizePolicy) else SMAXMAX)
    return frame

def create_label(self, text, style:str='', parent=None, style_override={}):
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
    if 'font' in style_override:
        label.setFont(theme_font(self, style, style_override['font']))
    else:
        label.setFont(theme_font(self, style))
    return label
    
def create_button_series(self, parent, buttons:dict, style, shape:str='row', seperator:str='', ret=False):
    """
    Creates a row / column of buttons.

    Parameters:
    - :param parent: widget that will contain the buttons
    - :param buttons: dictionary containing button details
        - key "default" contains style override for all buttons (optional)
        - all other keys represent one button, key will be the text on the button; value for the key contains
        dict with details for the specific button (all optional)
            - "callback": callable that will be called on button click
            - "style": individual style override dict
            - "toggle": True or False when button should be a toggle button, None when it should be a normal 
            button; the bool value indicates the default state of the button
            - "stretch": stretch value for the button
            - "align": alignment flag for button
    - :param style: key for self.theme -> default style
    - :param shape: row / column
    - :param seperator: string seperator displayed between buttons (optional)

    :return: populated QVBoxlayout / QHBoxlayout
    """
    if 'default' in buttons:
        defaults = merge_style(self, self.theme[style], buttons.pop('default'))
    else:
        defaults = self.theme[style]

    if shape == 'column':
        layout = QVBoxLayout()
    else:
        shape = 'row'
        layout = QHBoxLayout()
    
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    button_list = []
    
    if seperator != '':
        sep_style = {'color':defaults['color'], 'margin':0, 'padding':0, 'background':'rgba(0,0,0,0)'}
    
    for i, (name, detail) in enumerate(buttons.items()):
        if 'style' in detail:
            button_style = merge_style(self, defaults, detail['style'])
        else:
            button_style = defaults
        toggle_button = detail['toggle'] if 'toggle' in detail else None
        bt = self.create_button(name, style, parent, button_style, toggle_button)
        if 'callback' in detail and isinstance(detail['callback'], CALLABLE):
            bt.clicked.connect(detail['callback'])
        stretch = detail['stretch'] if 'stretch' in detail else 0
        if 'align' in detail:
            layout.addWidget(bt, stretch, detail['align'])
        else:
            layout.addWidget(bt, stretch)
        button_list.append(bt)
        if seperator != '' and i < (len(buttons) - 1):
            sep_label = self.create_label(seperator, 'label', parent, sep_style)
            sep_label.setSizePolicy(SMAXMIN)
            layout.addWidget(sep_label)
    
    if ret: return layout, button_list
    else: return layout

def create_combo_box(self, parent, style: str = 'combobox', style_override: dict = {}) -> QComboBox:
    """
    Creates a combobox with given style and returns it.

    Parameters:
    - :param parent: parent of the combo box
    - :param style: key for self.theme -> default style
    - :param style_override: style dict to override default style

    :return: styled QCombobox
    """
    combo_box = QComboBox(parent)
    combo_box.setStyleSheet(get_style_class(self, 'QComboBox', style, style_override))
    if 'font' in style_override:
        combo_box.setFont(theme_font(self, style, style_override['font']))
    else:
        combo_box.setFont(theme_font(self, style))
    combo_box.setSizePolicy(SMINMAX)
    return combo_box

def create_entry(self, default_value, validator=None, style: str = 'entry', style_override: dict = {}
        ) -> QLineEdit:
    """
    Creates an entry widget and styles it.

    Parameters:
    - :param default_value: default value for the entry
    - :param validator: validator to validate entered characters against
    - :param style: key for self.theme -> default style
    - :param style_override: style dict to override default style

    :return: styled QLineEdit
    """
    entry = QLineEdit(default_value)
    entry.setValidator(validator)
    entry.setStyleSheet(get_style_class(self, 'QLineEdit', style, style_override))
    if 'font' in style_override:
        entry.setFont(theme_font(self, style, style_override['font']))
    else:
        entry.setFont(theme_font(self, style))
    entry.setSizePolicy(SMAXMAX)
    return entry

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
    table.setStyleSheet(get_style_class(self, 'QTreeView', widget))
    table.setSizePolicy(SMINMIN)
    table.setAlternatingRowColors(True)
    table.setHorizontalScrollMode(SMPIXEL)
    table.setVerticalScrollMode(SMPIXEL)
    table.setSortingEnabled(True)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.header().setStyleSheet(get_style_class(self, 'QHeaderView', 'tree_table_header'))
    table.header().setSectionResizeMode(RFIXED)
    #table.header().setSectionsMovable(False)
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
    table.setAlternatingRowColors(self.theme['s.c']['table_alternate'])
    table.setShowGrid(self.theme['s.c']['table_gridline'])
    table.setSortingEnabled(True)
    table.setStyleSheet(get_style_class(self, 'QTableView', 'table'))
    table.setHorizontalScrollMode(SMPIXEL)
    table.setVerticalScrollMode(SMPIXEL)
    table.horizontalHeader().setStyleSheet(get_style_class(self, 'QHeaderView', 'table_header'))
    table.verticalHeader().setStyleSheet(get_style_class(self, 'QHeaderView', 'table_index'))
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
    error.setWindowIcon(self.icons['oscr'])
    error.exec()

def log_size_warning(self):
    """
    Warns user about oversized logfile.

    :return: "cancel", "split dialog", "continue"
    """
    dialog = QMessageBox()
    dialog.setIcon(QMessageBox.Icon.Warning)
    message = ('The combatlog file you are trying to open will impair the performance of the app due to its '
            'size. It is advised to split the log. \n\nClick "Split Dialog" to split the file, "Cancel" to '
            'abort combatlog analysis or "Continue" to analyze the log nevertheless.')
    dialog.setText(message)
    dialog.setWindowTitle('Open Source Combalog Reader')
    dialog.setWindowIcon(self.icons['oscr'])
    dialog.addButton('Cancel', QMessageBox.ButtonRole.RejectRole)
    default_button = dialog.addButton('Split Dialog', QMessageBox.ButtonRole.ActionRole)
    dialog.addButton('Continue', QMessageBox.ButtonRole.AcceptRole)
    dialog.setDefaultButton(default_button)
    clicked = dialog.exec()
    if clicked == 1:
        return 'split dialog'
    elif clicked == 2:
        return 'continue'
    else:
        return 'cancel'
    
def split_dialog(self):
    """
    Opens dialog to split the current logfile.
    """
    main_layout = QVBoxLayout()
    thick = self.theme['app']['frame_thickness']
    item_spacing = self.theme['defaults']['isp']
    main_layout.setContentsMargins(thick, thick, thick, thick)
    content_frame = create_frame(self)
    main_layout.addWidget(content_frame)
    current_logpath = self.entry.text()
    vertical_layout = QVBoxLayout()
    vertical_layout.setContentsMargins(thick, thick, thick, thick)
    vertical_layout.setSpacing(item_spacing)
    log_layout = QHBoxLayout()
    log_layout.setContentsMargins(0, 0, 0, 0)
    log_layout.setSpacing(item_spacing)
    current_log_heading = create_label(self, 'Selected Logfile:', 'label_subhead')
    log_layout.addWidget(current_log_heading, alignment=ALEFT)
    current_log_label = create_label(self, format_path(current_logpath), 'label')
    log_layout.addWidget(current_log_label, alignment=AVCENTER)
    log_layout.addSpacerItem(QSpacerItem(1, 1, hData=SEXPAND, vData=SMAX))
    vertical_layout.addLayout(log_layout)
    seperator_1 = create_frame(self, content_frame, 'hr', size_policy=SMINMIN)
    seperator_1.setFixedHeight(self.theme['hr']['height'])
    vertical_layout.addWidget(seperator_1)
    grid_layout = QGridLayout()
    grid_layout.setContentsMargins(0, 0, 0, 0)
    grid_layout.setVerticalSpacing(0)
    grid_layout.setHorizontalSpacing(item_spacing)
    vertical_layout.addLayout(grid_layout)
    auto_split_heading = create_label(self, 'Split Log Automatically:', 'label_heading')
    grid_layout.addWidget(auto_split_heading, 0, 0, alignment=ALEFT)
    label_text = ('Automatically splits the logfile at the next combat end after '
            f'{self.settings.value('split_log_after', type=int):,} lines until the entire file has been split. '
            'The new files are written to the selected folder. It is advised to select an empty folder '
            'to ensure all files are saved correctly.')
    auto_split_text = create_label(self, label_text, 'label')
    auto_split_text.setWordWrap(True)
    auto_split_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(auto_split_text, 1, 0, alignment=ALEFT)
    auto_split_button = create_button(self, 'Auto Split')
    auto_split_button.clicked.connect(lambda: auto_split_callback(self, current_logpath))
    grid_layout.addWidget(auto_split_button, 1, 2, alignment=ARIGHT|ABOTTOM)
    grid_layout.setRowMinimumHeight(2, item_spacing)
    seperator_3 = create_frame(self, content_frame, 'hr', size_policy=SMINMIN)
    seperator_3.setFixedHeight(self.theme['hr']['height'])
    grid_layout.addWidget(seperator_3, 3, 0, 1, 3)
    grid_layout.setRowMinimumHeight(4, item_spacing)
    range_split_heading = create_label(self, 'Export Range of Combats:', 'label_heading')
    grid_layout.addWidget(range_split_heading, 5, 0, alignment=ALEFT)
    label_text = ('Exports combats including and between lower and upper limit to selected file. '
            'Both limits refer to the indexed list of all combats in the file starting with 1. '
            'An upper limit larger than the total number of combats or of "-1", is treated as being equal to '
            'the total number of combats.')
    range_split_text = create_label(self, label_text, 'label')
    range_split_text.setWordWrap(True)
    range_split_text.setFixedWidth(self.sidebar_item_width)
    grid_layout.addWidget(range_split_text, 6, 0, alignment=ALEFT)
    range_limit_layout = QGridLayout()
    range_limit_layout.setContentsMargins(0, 0, 0, 0)
    range_limit_layout.setSpacing(0)
    range_limit_layout.setRowStretch(0, 1)
    lower_range_label = create_label(self, 'Lower Limit:', 'label')
    range_limit_layout.addWidget(lower_range_label, 1, 0, alignment=AVCENTER)
    upper_range_label = create_label(self, 'Upper Limit:', 'label')
    range_limit_layout.addWidget(upper_range_label, 2, 0, alignment=AVCENTER)
    lower_range_entry = QLineEdit()
    lower_validator = QIntValidator()
    lower_validator.setBottom(1)
    lower_range_entry.setValidator(lower_validator)
    lower_range_entry.setText('1')
    lower_range_entry.setStyleSheet(get_style(self, 'entry', {'margin-top': 0, 'margin-left': '@csp'}))
    lower_range_entry.setFixedWidth(self.sidebar_item_width // 7)
    range_limit_layout.addWidget(lower_range_entry, 1, 1, alignment=AVCENTER)
    upper_range_entry = QLineEdit()
    upper_validator = QIntValidator()
    upper_validator.setBottom(-1)
    upper_range_entry.setValidator(upper_validator)
    upper_range_entry.setText('1')
    upper_range_entry.setStyleSheet(get_style(self, 'entry', {'margin-top': 0, 'margin-left': '@csp'}))
    upper_range_entry.setFixedWidth(self.sidebar_item_width // 7)
    range_limit_layout.addWidget(upper_range_entry, 2, 1, alignment=AVCENTER)
    grid_layout.addLayout(range_limit_layout, 6, 1)
    range_split_button = create_button(self, 'Export Combats')
    range_split_button.clicked.connect(lambda le=lower_range_entry, ue=upper_range_entry: 
            combat_split_callback(self, current_logpath, le.text(), ue.text()))
    grid_layout.addWidget(range_split_button, 6, 2, alignment=ARIGHT|ABOTTOM)

    content_frame.setLayout(vertical_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle('OSCR - Split Logfile')
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.exec()

def auto_split_callback(self, path: str):
    """
    Callback for auto split button
    """
    folder_path = QFileDialog.getExistingDirectory(self.window, 'Select Folder', os.path.dirname(path))
    split_log_by_lines(path, folder_path, self.settings.value('split_log_after', type=int),
            self.settings.value('combat_distance', type=int))

def combat_split_callback(self, path: str, first_num: str, last_num: str):
    """
    Callback for combat split button
    """
    target_path = browse_path(self, path, 'Logfile (*.log);;Any File (*.*)', True)
    split_log_by_combat(path, target_path, int(first_num), int(last_num), 
            self.settings.value('seconds_between_combats', type=int), 
            self.settings.value('excluded_event_ids', type=list))