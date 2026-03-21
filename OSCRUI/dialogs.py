from typing import Iterable

from PySide6.QtCore import QObject, QSize, Signal
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QLabel, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget)

from OSCR_django_client import CombatLogUploadV2Response
from OSCR import DetectionInfo

from .iofunctions import open_link
from .style import get_style
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import (
        AHCENTER, ALEFT, ARIGHT, ATOP, AVCENTER,
        create_button2, create_frame2, create_label2,
        create_button, create_frame, create_label,
        SMAXMAX, SMINMAX, SMINMIN, SFIXED)
from .widgets import FlipButton


class DetectionInfoDialog(QDialog):
    """Dialog showing info about map detection."""

    def __init__(self, parent_window: QWidget, theme: AppTheme):
        """
        Parameters:
        - :param parent_window: window to center dialog on
        - :param theme: AppTheme
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


class UploadresultDialog(QDialog):
    """Shows feedback from upload"""

    def __init__(self, parent_window: QWidget, theme: AppTheme):
        """
        Parameters:
        - :param parent_window: window to center dialog on
        - :param theme: AppTheme
        """
        super().__init__(parent_window, modal=True)
        self._theme: AppTheme = theme
        self.setWindowTitle(tr('OSCR - Upload Results'))
        self._log_id: int = -1
        self._result_frame: QFrame
        self._title_label: QLabel
        self._view_button: QPushButton
        self.build_dialog()

    def build_dialog(self):
        """
        Creates layout of dialog
        """
        main_layout = QVBoxLayout()
        thick = self._theme['app']['frame_thickness']
        main_layout.setContentsMargins(thick, thick, thick, thick)
        content_frame = create_frame2(self._theme)
        content_layout = QGridLayout()
        content_layout.setContentsMargins(thick, thick, thick, thick)
        content_layout.setSpacing(0)
        margin = {'margin-bottom': self._theme['defaults']['isp']}
        self._title_label = create_label2(self._theme, '', 'label_heading', style_override=margin)
        content_layout.addWidget(self._title_label, 0, 0, alignment=ALEFT)
        self._view_button = create_button2(self._theme, 'View Online', style_override=margin)
        self._view_button.clicked.connect(self.view_online)
        content_layout.addWidget(self._view_button, 0, 0, alignment=ARIGHT)
        self._view_button.hide()
        self._result_frame = create_frame2(self._theme)
        self._result_frame.setLayout(QGridLayout())
        content_layout.addWidget(self._result_frame, 1, 0)
        close_button = create_button2(
            self._theme, 'Close', style_override={'margin-top': self._theme['defaults']['isp']})
        close_button.clicked.connect(self.accept)
        content_layout.addWidget(close_button, 2, 0, alignment=AHCENTER)
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame)

        self.setStyleSheet(self._theme.get_style('dialog_window'))
        self.setSizePolicy(SMAXMAX)
        self.setLayout(main_layout)

    def view_online(self):
        """
        Opens webbrowser to show the uploaded combatlog on the DPS League tables.
        """
        if self._log_id != -1:
            open_link(f"https://oscr.stobuilds.com/ui/combatlog/{self._log_id}/")

    def show_dialog(self, result: CombatLogUploadV2Response):
        """
        Shows a dialog that informs about the result of the triggered upload.

        Paramters:
        - :param result: response of upload
        """
        QWidget().setLayout(self._result_frame.layout())
        self._title_label.setText(result.detail)
        if result.combatlog is None:
            self._view_button.hide()
        else:
            self._log_id = result.combatlog
            self._view_button.show()
        result_layout = QGridLayout()
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(0)
        icon_size = QSize(self._theme.opt.icon_size / 1.5, self._theme.opt.icon_size / 1.5)
        row = 0
        if result.results:
            for row, line in enumerate(result.results, 1):
                if row % 2 == 1:
                    table_style = {'background-color': '@mbg', 'padding': (5, 3, 3, 3), 'margin': 0}
                    icon_table_style = {'background-color': '@mbg', 'padding': 3, 'margin': 0}
                else:
                    table_style = {'background-color': '@bg', 'padding': (5, 3, 3, 3), 'margin': 0}
                    icon_table_style = {'background-color': '@bg', 'padding': 3, 'margin': 0}
                if line.updated:
                    icon = self._theme.icons['check'].pixmap(icon_size)
                else:
                    icon = self._theme.icons['dash'].pixmap(icon_size)
                status_label = create_label2(self._theme, '', style_override=icon_table_style)
                status_label.setPixmap(icon)
                status_label.setSizePolicy(SMINMIN)
                result_layout.addWidget(status_label, row, 0)
                name_label = create_label2(self._theme, line.name, style_override=table_style)
                name_label.setSizePolicy(SMINMAX)
                result_layout.addWidget(name_label, row, 1)
                value_label = create_label2(
                    self._theme, str(line.value), style_override=table_style)
                value_label.setSizePolicy(SMINMAX)
                value_label.setAlignment(ARIGHT)
                result_layout.addWidget(value_label, row, 2)
                detail_label = create_label2(self._theme, line.detail, style_override=table_style)
                detail_label.setSizePolicy(SMINMAX)
                result_layout.addWidget(detail_label, row, 3)
        self._result_frame.setLayout(result_layout)
        self.open()


class DialogsWrapper(QObject):
    """Contains simple, multi-purpose dialogs"""

    _message_signal = Signal(str, str, str)
    _error_signal = Signal(str, str, str)

    def __init__(self, parent_window: QWidget, theme: AppTheme):
        """
        Parameters:
        - :param parent_window: window to center dialog on
        - :param theme: AppTheme
        """
        super().__init__()
        self._theme: AppTheme = theme
        self._message_dialog: QDialog = QDialog(parent_window, modal=True)
        self._icon_label_m: QLabel
        self._message_label_m: QLabel
        self.build_message_dialog()
        self._message_signal.connect(self._show_message)
        self._confirm_dialog: QDialog = QDialog(parent_window, modal=True)
        self._icon_label_c: QLabel
        self._message_label_c: QLabel
        self.build_confirmation_dialog()
        self._error_dialog: QDialog = QDialog(parent_window, modal=True)
        self._message_label_e: QLabel
        self._error_label_e: QTextEdit
        self.build_error_dialog()
        self._error_signal.connect(self._show_error)

    def build_message_dialog(self):
        """Creates layout for message dialog"""
        thick = self._theme['app']['frame_thickness']
        item_spacing = self._theme['defaults']['isp']
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(thick, thick, thick, thick)
        dialog_frame = create_frame2(self._theme, size_policy=SMINMIN)
        main_layout.addWidget(dialog_frame)
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(thick, thick, thick, thick)
        dialog_layout.setSpacing(thick)
        content_frame = create_frame2(self._theme, size_policy=SMINMIN)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(item_spacing)
        content_layout.setAlignment(ATOP)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2 * thick)
        self._icon_label_m = create_label2(self._theme, '')
        top_layout.addWidget(self._icon_label_m, alignment=ALEFT | AVCENTER)
        self._message_label_m = create_label2(self._theme, '')
        self._message_label_m.setWordWrap(True)
        self._message_label_m.setSizePolicy(SMINMAX)
        top_layout.addWidget(self._message_label_m, stretch=1)
        content_layout.addLayout(top_layout)

        content_frame.setLayout(content_layout)
        dialog_layout.addWidget(content_frame, stretch=1)

        seperator = create_frame2(self._theme, style='light_frame', size_policy=SMINMAX)
        seperator.setFixedHeight(1)
        dialog_layout.addWidget(seperator)
        ok_button = create_button2(self._theme, tr('OK'))
        ok_button.clicked.connect(lambda: self._message_dialog.done(0))
        dialog_layout.addWidget(ok_button, alignment=AHCENTER)
        dialog_frame.setLayout(dialog_layout)

        self._message_dialog.setStyleSheet(self._theme.get_style('dialog_window'))
        self._message_dialog.setSizePolicy(SMAXMAX)
        self._message_dialog.setLayout(main_layout)

    def show_message(self, title: str, message: str, icon: str = 'info'):
        """
        Displays a message in a dialog. Passed through signal to ensure multi-thread compatability.

        Parameters:
        - :param title: title of the message window
        - :param message: message to be displayed
        - :param icon: "warning" or "info" or "error"
        """
        self._message_signal.emit(title, message, icon)

    def _show_message(self, title: str, message: str, icon: str = 'info'):
        """
        Displays a message in a dialog

        Parameters:
        - :param title: title of the message window
        - :param message: message to be displayed
        - :param icon: "warning" or "info" or "error"
        """
        self._message_dialog.setWindowTitle('OSCR - ' + title)
        self._message_label_m.setText(message)
        icon_size = self._theme.opt.default_big_icon_size * self._theme.scale
        self._icon_label_m.setPixmap(self._theme.icons[icon].pixmap(icon_size))
        self._message_dialog.open()

    def build_confirmation_dialog(self):
        """Creates layout for confirmation dialog"""
        thick = self._theme['app']['frame_thickness']
        item_spacing = self._theme['defaults']['isp']
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(thick, thick, thick, thick)
        dialog_frame = create_frame2(self._theme, size_policy=SMINMIN)
        main_layout.addWidget(dialog_frame)
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(thick, thick, thick, thick)
        dialog_layout.setSpacing(thick)
        content_frame = create_frame2(self._theme, size_policy=SMINMIN)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(item_spacing)
        content_layout.setAlignment(ATOP)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2 * thick)
        self._icon_label_c = create_label2(self._theme, '')
        # icon_size = self._theme.opt.default_big_icon_size * self._theme.scale
        # icon_label.setPixmap(self.icons[icon].pixmap(icon_size))
        top_layout.addWidget(self._icon_label_c, alignment=ALEFT | AVCENTER)
        self._message_label_c = create_label2(self._theme, '')
        self._message_label_c.setWordWrap(True)
        self._message_label_c.setSizePolicy(SMINMAX)
        top_layout.addWidget(self._message_label_c, stretch=1)
        content_layout.addLayout(top_layout)

        content_frame.setLayout(content_layout)
        dialog_layout.addWidget(content_frame, stretch=1)

        seperator = create_frame2(self._theme, style='light_frame', size_policy=SMINMAX)
        seperator.setFixedHeight(1)
        dialog_layout.addWidget(seperator)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(thick)
        cancel_button = create_button2(self._theme, tr('Cancel'))
        cancel_button.clicked.connect(lambda: self._confirm_dialog.done(0))
        button_layout.addWidget(cancel_button, alignment=ARIGHT)
        ok_button = create_button2(self._theme, tr('OK'))
        ok_button.clicked.connect(lambda: self._confirm_dialog.done(1))
        button_layout.addWidget(ok_button, alignment=ALEFT)
        dialog_layout.addLayout(button_layout)
        dialog_frame.setLayout(dialog_layout)

        self._confirm_dialog.setStyleSheet(self._theme.get_style('dialog_window'))
        self._confirm_dialog.setSizePolicy(SMAXMAX)
        self._confirm_dialog.setLayout(main_layout)

    def confirm(self, title: str, message: str, icon: str = 'info') -> int:
        """
        Asks user for confirmation. Returns `1` if the user confirms, `0` if the use rejects.

        Parameters:
        - :param title: title of the confirmation dialog
        - :param message: message to be displayed
        - :param icon: "warning" or "info" or "error"
        """
        self._confirm_dialog.setWindowTitle('OSCR - ' + title)
        self._message_label_c.setText(message)
        icon_size = self._theme.opt.default_big_icon_size * self._theme.scale
        self._icon_label_c.setPixmap(self._theme.icons[icon].pixmap(icon_size))
        return self._confirm_dialog.exec()

    def build_error_dialog(self):
        """
        Creates layout of error dialog
        """
        thick = self._theme['app']['frame_thickness']
        item_spacing = self._theme['defaults']['isp']
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(thick, thick, thick, thick)
        dialog_frame = create_frame2(self._theme, size_policy=SMINMIN)
        main_layout.addWidget(dialog_frame)
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(thick, thick, thick, thick)
        dialog_layout.setSpacing(thick)
        content_frame = create_frame2(self._theme, size_policy=SMINMIN)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(item_spacing)
        content_layout.setAlignment(ATOP)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2 * thick)
        icon_label = create_label2(self._theme, '')
        icon_size = self._theme.opt.default_big_icon_size * self._theme.scale
        icon_label.setPixmap(self._theme.icons['error'].pixmap(icon_size))
        top_layout.addWidget(icon_label, alignment=ALEFT | AVCENTER)
        self._message_label_e = create_label2(self._theme, '')
        self._message_label_e.setWordWrap(True)
        self._message_label_e.setSizePolicy(SMINMAX)
        top_layout.addWidget(self._message_label_e, stretch=1)
        content_layout.addLayout(top_layout)
        self._error_label_e = QTextEdit()
        self._error_label_e.setSizePolicy(SMINMIN)
        self._error_label_e.setReadOnly(True)
        self._error_label_e.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self._error_label_e.setFont(self._theme.get_font('textedit'))
        self._error_label_e.setStyleSheet(self._theme.get_style_class('QTextEdit', 'textedit'))
        expand_button = FlipButton(tr('Show Error'), tr('Hide Error'))
        expand_button.set_icon_r(self._theme.icons['chevron-right'])
        expand_button.set_icon_l(self._theme.icons['chevron-down'])
        expand_button.r_function = self._error_label_e.show
        expand_button.l_function = self._error_label_e.hide
        expand_button.setStyleSheet(self._theme.get_style_class('FlipButton', 'button'))
        expand_button.setFont(self._theme.get_font('button'))
        content_layout.addWidget(expand_button, alignment=ALEFT)
        content_layout.addWidget(self._error_label_e, stretch=1)
        self._error_label_e.hide()
        content_frame.setLayout(content_layout)
        dialog_layout.addWidget(content_frame, stretch=1)

        seperator = create_frame2(self._theme, style='light_frame', size_policy=SMINMAX)
        seperator.setFixedHeight(1)
        dialog_layout.addWidget(seperator)
        ok_button = create_button2(self._theme, tr('OK'))
        ok_button.clicked.connect(self._error_dialog.accept)
        dialog_layout.addWidget(ok_button, alignment=AHCENTER)
        dialog_frame.setLayout(dialog_layout)

        self._error_dialog.setStyleSheet(self._theme.get_style('dialog_window'))
        self._error_dialog.setLayout(main_layout)

    def show_error(self, error_title: str, error_message: str, error_details: str):
        """
        Shows error message with expandable field for error details like a traceback. Passed
        through signal to ensure multi-thread compatability.

        Parameters:
        - :param error_title: very short decription of the error for the dialog window title
        - :param error_message: message decribing the error
        - :param error_details: advanced information about the error
        """
        self._error_signal.emit(error_title, error_message, error_details)

    def _show_error(self, error_title: str, error_message: str, error_details: str):
        """
        Shows error message with expandable field for error details like a traceback.

        Parameters:
        - :param error_title: very short decription of the error for the dialog window title
        - :param error_message: message decribing the error
        - :param error_details: advanced information about the error
        """
        self._error_dialog.setWindowTitle(f'OSCR - {error_title}')
        self._message_label_e.setText(error_message)
        self._error_label_e.setText(error_details)
        self._error_dialog.open()
