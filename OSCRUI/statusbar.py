from datetime import datetime

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QListView, QPushButton, QTextEdit,
    QVBoxLayout, QWidget)

from .datamodels import StringListModel
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import (
    AHCENTER, ALEFT, ARIGHT, SMAXMAX, SMAXMIN, SMINMAX,
    create_button, create_frame, create_label)


class StatusBar(QFrame):
    """Bar that displays status information"""

    parser_status: Signal = Signal(str)
    status_message: Signal = Signal(str, str)

    def __init__(self, theme: AppTheme, window: QWidget):
        super().__init__()
        self._theme: AppTheme = theme
        self._parser_label: QLabel
        self._message_button: QPushButton
        self._log_window: LogWindow = LogWindow(theme, window)
        icon_size = 16 * self._theme.scale
        self._ready_icon: QPixmap = self._theme.icons['parser-ready'].pixmap(icon_size)
        self._active_icon: QPixmap = self._theme.icons['parser-active'].pixmap(icon_size)
        self.setup_bar()
        self.parser_status.connect(self.update_parser_status)
        self.status_message.connect(self.update_status_message)

    def setup_bar(self):
        """
        Creates the widgets.
        """
        layout = QGridLayout()
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)
        small_margin = self._theme.scale * 2
        margin = self._theme['app']['frame_thickness']
        layout.setContentsMargins(margin, small_margin, margin, small_margin)
        layout.setSpacing(margin)
        self._parser_label = create_label(self._theme, '', 'label_status')
        self._parser_label.setPixmap(self._ready_icon)
        self._parser_label.setToolTip('Parser Ready')
        self._parser_label.setCursor(Qt.CursorShape.WhatsThisCursor)
        layout.addWidget(self._parser_label, 0, 0, alignment=ARIGHT)
        separator = create_frame(
            self._theme, 'frame', {'background-color': '@mfg', 'margin': (0, 0, 1, 0)},
            size_policy=SMAXMIN)
        separator.setFixedWidth(self._theme.scale * 1)
        layout.addWidget(separator, 0, 1)
        self._message_button = create_button(self._theme, tr('Idle'), 'statusbar_button')
        self._message_button.clicked.connect(self._log_window.open)
        layout.addWidget(self._message_button, 0, 2, alignment=ALEFT)

        self.setSizePolicy(SMINMAX)
        self.setStyleSheet(self._theme.get_style('frame', {'background-color': '@oscr'}))
        self.setLayout(layout)

    def update_parser_status(self, status: str):
        """
        Sets new status for parser.

        Parameters:
        - :param status: `ready` or `active`
        """
        if status == 'ready':
            self._parser_label.setPixmap(self._ready_icon)
            self._parser_label.setToolTip('Parser Ready')
        elif status == 'active':
            self._parser_label.setPixmap(self._active_icon)
            self._parser_label.setToolTip('Parser Analyzing Log File...')

    def update_status_message(self, status_message: str, description: str = ''):
        """
        Shows status message and adds message to status log.

        Parameters:
        - :param status_message: message to show
        - :param description: description for the message (optional)
        """
        self._message_button.setText(status_message)
        time = datetime.now()
        full_message = f'[{time.hour:02}:{time.minute:02}:{time.second:02}] {status_message}'
        self._log_window.add_message(full_message, description)


class LogWindow(QDialog):
    """Displays status log"""

    def __init__(self, theme: AppTheme, window: QWidget):
        super().__init__(parent=window)
        self._theme: AppTheme = theme
        self.model: StringListModel = StringListModel()
        self.descriptions: list[str] = list()
        self._desc: QTextEdit
        self.setWindowTitle(tr('OSCR - Message Log'))
        self.build_dialog()

    def build_dialog(self):
        """
        Creates dialog window.
        """
        window_layout = QHBoxLayout()
        border = self._theme['app']['frame_thickness']
        window_layout.setContentsMargins(border, border, border, border)
        bg_frame = create_frame(self._theme)
        window_layout.addWidget(bg_frame)
        m = self._theme['defaults']['margin'] * self._theme.scale
        layout = QVBoxLayout()
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(m)
        log_list = QListView()
        log_list.setStyleSheet(
            self._theme.get_style_class('QListView', 'listbox', {'font': '@font'}))
        log_list.setMinimumHeight(300 * self._theme.scale)
        log_list.setMinimumWidth(400 * self._theme.scale)
        log_list.setModel(self.model)
        layout.addWidget(log_list)
        log_list.clicked.connect(self.slot_description)
        self._desc = QTextEdit()
        self._desc.setReadOnly(True)
        self._desc.setMinimumHeight(200 * self._theme.scale)
        self._desc.setMinimumWidth(400 * self._theme.scale)
        self._desc.setFont(self._theme.get_font('app'))
        self._desc.setStyleSheet(self._theme.get_style_class('QTextEdit', 'textedit'))
        layout.addWidget(self._desc)
        close_button = create_button(self._theme, tr('Close'))
        layout.addWidget(close_button, alignment=AHCENTER)
        close_button.clicked.connect(self.accept)
        bg_frame.setLayout(layout)
        self.setStyleSheet(self._theme.get_style('dialog_window'))
        self.setSizePolicy(SMAXMAX)
        self.setLayout(window_layout)

    def add_message(self, message: str, description: str = ''):
        """
        Adds a message to the log.

        Parameters:
        - :param message: short message
        - :param description: description of the message
        """
        self.model.append(message)
        if description == '':
            self.descriptions.append('[' + tr('No Description') + ']')
        else:
            self.descriptions.append(description)

    def slot_description(self, index: QModelIndex):
        """
        Inserts description into description box
        """
        self._desc.setText(self.descriptions[index.row()])
