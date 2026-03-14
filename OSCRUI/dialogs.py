from typing import Iterable

from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QVBoxLayout, QWidget

from OSCR import DetectionInfo

from .style import get_style
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import (
        AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER,
        create_button2, create_frame2, create_label2,
        create_button, create_frame, create_label,
        SMAXMAX, SMINMAX, SMINMIN, SFIXED)


class DetectionInfoDialog(QDialog):
    """Dialog showing info about map detection."""

    def __init__(self, parent_window: QWidget, theme: AppTheme):
        """
        Parameters:
        - :param parent_window: window to center dialog on
        """
        super().__init__(parent_window, modal=True)
        self._theme: AppTheme = theme
        self._info_frame: QFrame
        self.setWindowTitle(tr('OSCR - Map Detection Details'))
        self.build_dialog()

    def build_dialog(self):
        """
        creates layout of detection dialog
        """
        thick = self._theme['app']['frame_thickness']
        item_spacing = self._theme['defaults']['isp']
        main_layout = QVBoxLayout()
        main_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        main_layout.setContentsMargins(thick, thick, thick, thick)
        content_frame = create_frame2(self._theme)
        main_layout.addWidget(content_frame)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(thick, thick, thick, thick)
        content_layout.setSpacing(item_spacing)

        self._info_frame = create_frame2(self._theme)
        self._info_frame.setLayout(QVBoxLayout())
        content_layout.addWidget(self._info_frame)
        seperator = create_frame2(self._theme, style='light_frame', size_policy=SMINMAX)
        seperator.setFixedHeight(1)
        content_layout.addWidget(seperator)
        ok_button = create_button2(self._theme, tr('OK'))
        ok_button.clicked.connect(lambda: self.done(0))
        content_layout.addWidget(ok_button, alignment=AHCENTER)
        content_frame.setLayout(content_layout)

        self.setStyleSheet(self._theme.get_style('dialog_window'))
        self.setLayout(main_layout)

    def show_dialog(self, detection_info: Iterable[DetectionInfo]):
        """
        Shows detection info dialog with the given detection data.

        Parameters:
        - :param detection_info: contains detection steps to display
        """
        QWidget().setLayout(self._info_frame.layout())
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(self._theme['defaults']['isp'])

        for detection_step in detection_info:
            if detection_step.success:
                if detection_step.step == 'existence':
                    detection_method = tr(
                        'by checking whether the following entities exist in the log')
                elif detection_step.step == 'deaths':
                    detection_method = tr('by checking the death counts of following entities')
                else:
                    detection_method = tr('by checking the hull values of following entities')
                if detection_step.type == 'both':
                    detected_type = tr('Map and Difficulty were')
                elif detection_step.type == 'difficulty':
                    detected_type = f"{tr('Difficulty')} ({detection_step.difficulty}) {tr('was')}"
                else:
                    detected_type = f"{tr('Map')} ({detection_step.map}) {tr('was')}"
                t = (
                    f"{tr('The')} {detected_type} {tr('successfully detected')} {detection_method}"
                    f": {', '.join(detection_step.identificators)}.")
            else:
                if detection_step.type == 'both':
                    detected_type = tr('Map and Difficulty')
                elif detection_step.type == 'difficulty':
                    detected_type = f"{tr('Difficulty')} ({detection_step.difficulty})"
                else:
                    detected_type = f"{tr('Map')} ({detection_step.map}) {tr('was')}"
                t = f"{tr('The')} {tr(detected_type)} {tr('could not be detected, because')} "
                if detection_step.step == 'existence':
                    t += tr('no entity identifying a map was found in the log.')
                elif detection_step.step == 'deaths':
                    t += (
                        f'{tr("the entity")} "{detection_step.identificators[0]}" '
                        f'{tr("was killed")} {detection_step.retrieved_value} '
                        f'{tr("times instead of the expected")} {detection_step.target_value} '
                        f'{tr("times")}.')
                else:
                    t += (
                        f'{tr("the entities")} "{detection_step.identificators[0]}" '
                        f'{tr("average hull capacity of")} {detection_step.retrieved_value:.0f} '
                        f'{tr("was higher than the allowed")} {detection_step.target_value:.0f}.')
            info_label = create_label2(self._theme, t)
            info_label.setSizePolicy(SMINMAX)
            info_label.setWordWrap(True)
            info_layout.addWidget(info_label)

        self._info_frame.setLayout(info_layout)
        self.open()


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
    icon_size = self.theme['s.c']['big_icon_size'] * self.config.ui_scale
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
    icon_size = self.theme['s.c']['big_icon_size'] * self.config.ui_scale
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
