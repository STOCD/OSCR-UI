from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QListView, QVBoxLayout, QWidget)

from .datamodels import CombatModel
from .dialogs import DialogsWrapper
from .parserbridge import ParserBridge
from .theme import AppTheme
from .translation import tr
from .widgetbuilder import (
    create_button, create_button_series, create_frame, create_label,
    ABOTTOM, AHCENTER, ALEFT, ARIGHT, SMAXMAX, SMINMAX, SMINMIN, SMIXMIN)
from .widgets import CombatDelegate


class SplitDialog(QDialog):
    """Dialog window that allows for splitting and repairing of the logfile"""

    def __init__(
            self, parent_window: QWidget, parser: ParserBridge, dialogs: DialogsWrapper,
            theme: AppTheme):
        """
        Parameters:
        - :param parent_window: primary window of the app
        - :param parser: ParserBridge
        - :param dialogs: DialogsWrapper
        - :param theme: AppTheme
        """
        super().__init__(parent_window, modal=True)
        self._parser: ParserBridge = parser
        self._dialogs: DialogsWrapper = dialogs
        self._theme: AppTheme = theme
        self._current_log_path: Path
        self._current_log_label: QLabel
        self._combat_model: CombatModel
        self.setWindowTitle(tr('OSCR - Split Logfile'))
        self.build_dialog()

    def build_dialog(self):
        """
        Creates layout of split dialog.
        """
        main_layout = QVBoxLayout()
        thick = self._theme['app']['frame_thickness']
        main_layout.setContentsMargins(thick, thick, thick, thick)
        content_frame = create_frame(self._theme)
        main_layout.addWidget(content_frame)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(thick, thick, thick, thick)
        content_layout.setSpacing(thick)
        log_layout = QHBoxLayout()
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(thick)
        log_layout.setAlignment(ALEFT)
        current_log_heading = create_label(self._theme, tr('Selected Logfile:'), 'label_light')
        log_layout.addWidget(current_log_heading)
        self._current_log_label = create_label(
            self._theme, '', 'label_subhead', {'margin-bottom': 0})
        log_layout.addWidget(self._current_log_label)
        content_layout.addLayout(log_layout)
        seperator = create_frame(self._theme, style='hr', size_policy=SMINMAX)
        seperator.setFixedHeight(self._theme['hr']['height'])
        content_layout.addWidget(seperator)
        trim_layout = QGridLayout()
        trim_layout.setContentsMargins(0, 0, 0, 0)
        trim_layout.setSpacing(thick)
        trim_layout.setColumnStretch(0, 1)
        trim_heading = create_label(self._theme, tr('Trim Logfile:'), 'label_heading')
        trim_layout.addWidget(trim_heading, 0, 0, alignment=ALEFT)
        label_text = tr(
            'Removes all combats except for the most recent one from the selected logfile. '
            'All previous combats will be lost!')
        trim_text = create_label(self._theme, label_text)
        trim_text.setSizePolicy(SMINMAX)
        trim_text.setWordWrap(True)
        trim_layout.addWidget(trim_text, 1, 0)
        trim_button = create_button(self._theme, tr('Trim'))
        trim_button.clicked.connect(self.confirm_trim_logfile)
        trim_layout.addWidget(trim_button, 0, 1, alignment=ARIGHT | ABOTTOM)
        content_layout.addLayout(trim_layout)
        seperator = create_frame(self._theme, style='hr', size_policy=SMINMAX)
        seperator.setFixedHeight(self._theme['hr']['height'])
        content_layout.addWidget(seperator)
        repair_layout = QGridLayout()
        repair_layout.setContentsMargins(0, 0, 0, 0)
        repair_layout.setSpacing(thick)
        repair_layout.setColumnStretch(0, 1)
        repair_log_heading = create_label(self._theme, tr('Repair Logfile:'), 'label_heading')
        repair_layout.addWidget(repair_log_heading, 0, 0, alignment=ALEFT)
        label_text = tr(
            'Attempts to repair the logfile by replacing sections known to break parsing.')
        repair_label = create_label(self._theme, label_text)
        repair_layout.addWidget(repair_label, 1, 0)
        repair_log_button = create_button(self._theme, tr('Repair'))
        repair_log_button.clicked.connect(
            lambda: self._parser.repair_logfile(self._current_log_path))
        repair_layout.addWidget(repair_log_button, 0, 1, alignment=ARIGHT | ABOTTOM)
        content_layout.addLayout(repair_layout)
        seperator = create_frame(self._theme, style='hr', size_policy=SMINMAX)
        seperator.setFixedHeight(self._theme['hr']['height'])
        content_layout.addWidget(seperator)

        combat_list = QListView()
        split_heading_layout = QHBoxLayout()
        split_heading_layout.setContentsMargins(0, 0, 0, 0)
        split_heading_layout.setSpacing(thick)
        split_heading = create_label(self._theme, tr('Split Logfile:'), 'label_heading')
        split_heading_layout.addWidget(split_heading, alignment=ALEFT, stretch=1)
        split_button_style = {
            tr('Load Combats'): {'callback': self.populate_split_combats},
            tr('Split'): {'callback': lambda: self._parser.extract_combats(
                combat_list.selectionModel().selectedIndexes(), self._current_log_path)},
        }
        buttons_layout = create_button_series(
            self._theme, split_button_style, 'button', seperator='•')
        split_heading_layout.addLayout(buttons_layout)
        content_layout.addLayout(split_heading_layout)
        label_text = tr(
            'Extracts (multiple) combats from selected file and saves them to new file.')
        split_label = create_label(self._theme, label_text)
        content_layout.addWidget(split_label)
        background_frame = create_frame(self._theme, style='frame', style_override={
                'border-radius': self._theme['listbox']['border-radius'], 'margin-top': '@csp',
                'margin-bottom': '@csp'}, size_policy=SMINMIN)
        background_layout = QVBoxLayout()
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_frame.setLayout(background_layout)
        combat_list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        combat_list.setSelectionMode(QListView.SelectionMode.MultiSelection)
        combat_list.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        combat_list.setStyleSheet(self._theme.get_style_class('QListView', 'listbox'))
        combat_list.setFont(self._theme.get_font('listbox'))
        combat_list.setAlternatingRowColors(True)
        combat_list.setSizePolicy(SMIXMIN)
        self._combat_model = CombatModel()
        combat_list.setModel(self._combat_model)
        border_width = 1 * self._theme.scale
        padding = 4 * self._theme.scale
        combat_list.setItemDelegate(CombatDelegate(border_width, padding))
        background_layout.addWidget(combat_list)
        content_layout.addWidget(background_frame, alignment=AHCENTER)

        content_frame.setLayout(content_layout)
        self.setSizePolicy(SMAXMAX)
        self.setStyleSheet(self._theme.get_style('dialog_window'))
        self.setLayout(main_layout)

    def show_dialog(self, current_log_path: str):
        """
        Shows dialog to split and repair combat.

        Parameters:
        - :param current_log_path: log path to operate on
        """
        self._current_log_path = Path(current_log_path)
        self._current_log_label.setText(current_log_path)
        self._combat_model.clear()
        self.open()

    def confirm_trim_logfile(self):
        """
        Prompts the user to confirm whether the logfile should be trimmed
        """
        title = tr('Trim Logfile')
        text = tr(
                'Trimming the logfile will delete all combats except for the most recent combat. '
                'Continue?')
        if self._dialogs.confirm(title, text, 'warning'):
            success = self._parser.trim_logfile(self._current_log_path)
            if success:
                self._dialogs.show_message(title, tr('Logfile has been trimmed.'))
            else:
                self._dialogs.show_message(title, tr('Trimming the logfile failed.'), 'error')

    def populate_split_combats(self):
        """
        Isolates combats and inserts them into list
        """
        self._parser.populate_split_combats_list(self._combat_model, self._current_log_path)
