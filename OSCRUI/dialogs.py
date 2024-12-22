from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout

from .style import get_style
from .translation import tr
from .widgetbuilder import (
        AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER,
        create_button, create_frame, create_label,
        SMAXMAX, SMINMAX, SMINMIN)


def show_message(self, title: str, message: str, icon: str = 'info'):
    """
    Displays a message in a dialog

    Parameters:
    - :param title: title of the warning
    - :param message: message to be displayed
    - :param icon: "warning" or "info" or "error"
    """
    dialog = QDialog(self.window)
    thick = self.theme['app']['frame_thickness']
    item_spacing = self.theme['defaults']['isp']
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(thick, thick, thick, thick)
    dialog_frame = create_frame(self, size_policy=SMINMIN)
    main_layout.addWidget(dialog_frame)
    dialog_layout = QVBoxLayout()
    dialog_layout.setContentsMargins(thick, thick, thick, thick)
    dialog_layout.setSpacing(thick)
    content_frame = create_frame(self, size_policy=SMINMIN)
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(item_spacing)
    content_layout.setAlignment(ATOP)

    top_layout = QHBoxLayout()
    top_layout.setContentsMargins(0, 0, 0, 0)
    top_layout.setSpacing(2 * thick)
    icon_label = create_label(self, '')
    icon_size = self.theme['s.c']['big_icon_size'] * self.config['ui_scale']
    icon_label.setPixmap(self.icons[icon].pixmap(icon_size))
    top_layout.addWidget(icon_label, alignment=ALEFT | AVCENTER)
    message_label = create_label(self, message)
    message_label.setWordWrap(True)
    message_label.setSizePolicy(SMINMAX)
    top_layout.addWidget(message_label, stretch=1)
    content_layout.addLayout(top_layout)

    content_frame.setLayout(content_layout)
    dialog_layout.addWidget(content_frame, stretch=1)

    seperator = create_frame(self, style='light_frame', size_policy=SMINMAX)
    seperator.setFixedHeight(1)
    dialog_layout.addWidget(seperator)
    ok_button = create_button(self, tr('OK'))
    ok_button.clicked.connect(lambda: dialog.done(0))
    dialog_layout.addWidget(ok_button, alignment=AHCENTER)
    dialog_frame.setLayout(dialog_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle('OSCR - ' + title)
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    dialog.exec()


def confirmation_dialog(self, title: str, message: str, icon: str = 'warning') -> bool:
    """
    Opens dialog asking for user confirmation. Returns True/False depending on the users action.

    Parameters:
    - :param title: title of the dialog window
    - :param message: displayed message prompting the user to confirm an action

    :return: True if user clicked "OK", False if user clicked "Cancel"
    """
    dialog = QDialog(self.window)
    thick = self.theme['app']['frame_thickness']
    item_spacing = self.theme['defaults']['isp']
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(thick, thick, thick, thick)
    dialog_frame = create_frame(self, size_policy=SMINMIN)
    main_layout.addWidget(dialog_frame)
    dialog_layout = QVBoxLayout()
    dialog_layout.setContentsMargins(thick, thick, thick, thick)
    dialog_layout.setSpacing(thick)
    content_frame = create_frame(self, size_policy=SMINMIN)
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(item_spacing)
    content_layout.setAlignment(ATOP)

    top_layout = QHBoxLayout()
    top_layout.setContentsMargins(0, 0, 0, 0)
    top_layout.setSpacing(2 * thick)
    icon_label = create_label(self, '')
    icon_size = self.theme['s.c']['big_icon_size'] * self.config['ui_scale']
    icon_label.setPixmap(self.icons[icon].pixmap(icon_size))
    top_layout.addWidget(icon_label, alignment=ALEFT | AVCENTER)
    message_label = create_label(self, message)
    message_label.setWordWrap(True)
    message_label.setSizePolicy(SMINMAX)
    top_layout.addWidget(message_label, stretch=1)
    content_layout.addLayout(top_layout)

    content_frame.setLayout(content_layout)
    dialog_layout.addWidget(content_frame, stretch=1)

    seperator = create_frame(self, style='light_frame', size_policy=SMINMAX)
    seperator.setFixedHeight(1)
    dialog_layout.addWidget(seperator)
    button_layout = QHBoxLayout()
    button_layout.setContentsMargins(0, 0, 0, 0)
    button_layout.setSpacing(thick)
    cancel_button = create_button(self, tr('Cancel'))
    cancel_button.clicked.connect(lambda: dialog.done(False))
    button_layout.addWidget(cancel_button, alignment=ARIGHT)
    ok_button = create_button(self, tr('OK'))
    ok_button.clicked.connect(lambda: dialog.done(True))
    button_layout.addWidget(ok_button, alignment=ALEFT)
    dialog_layout.addLayout(button_layout)
    dialog_frame.setLayout(dialog_layout)

    dialog = QDialog(self.window)
    dialog.setLayout(main_layout)
    dialog.setWindowTitle('OSCR - ' + title)
    dialog.setStyleSheet(get_style(self, 'dialog_window'))
    dialog.setSizePolicy(SMAXMAX)
    return dialog.exec()
