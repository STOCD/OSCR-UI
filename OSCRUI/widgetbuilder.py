from types import FunctionType, BuiltinFunctionType, MethodType
from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSlider, QVBoxLayout)

from .theme import AppTheme

CALLABLE = (FunctionType, BuiltinFunctionType, MethodType)

SMINMIN = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
SMAXMAX = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
SMAXMIN = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
SMINMAX = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
SMIXMAX = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
SMIXMIN = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
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
RCONTENT = QHeaderView.ResizeMode.ResizeToContents

OVERTICAL = Qt.Orientation.Vertical

SMPIXEL = QAbstractItemView.ScrollMode.ScrollPerPixel

SCROLLOFF = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
SCROLLON = Qt.ScrollBarPolicy.ScrollBarAlwaysOn


def create_button(
        theme: AppTheme, text: str, style: str = 'button', style_override: dict = {},
        toggle: bool = None):
    """
    Creates a button according to style with parent.

    Parameters:
    - :param theme: reference to AppTheme
    - :param text: text to be shown on the button
    - :param style: name of the style as in self.theme or style dict
    - :param style_override: style dict to override default style (optional)
    - :param toggle: True or False when button should be a toggle button, None when it should be a \
    normal button; the bool value indicates the default state of the button

    :return: configured QPushButton
    """
    button = QPushButton(text)
    button.setStyleSheet(theme.get_style_class('QPushButton', style, style_override))
    if 'font' in style_override:
        button.setFont(theme.get_font(style, style_override['font']))
    else:
        button.setFont(theme.get_font(style))
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setSizePolicy(SMAXMAX)
    if isinstance(toggle, bool):
        button.setCheckable(True)
        button.setChecked(toggle)
    return button


def create_button_series(
        theme: AppTheme, buttons: dict[str, dict], style: str, shape: str = 'row',
        seperator: str = '', ret: bool = False) -> (
            QVBoxLayout | QHBoxLayout | tuple[QVBoxLayout | QHBoxLayout, list[QPushButton]]):
    """
    Creates a row / column of buttons.

    Parameters:
    - :param theme: reference to AppTheme
    - :param buttons: dictionary containing button details
        - key "default" contains style override for all buttons (optional)
        - all other keys represent one button, key will be the text on the button; value for the
        key contains dict with details for the specific button (all optional)
            - "callback": callable that will be called on button click
            - "style": individual style override dict
            - "toggle": True or False when button should be a toggle button, None when it should
                be a normal button; the bool value indicates the default state of the button
            - "stretch": stretch value for the button
            - "align": alignment flag for button
    - :param style: key for AppTheme -> default style
    - :param shape: row / column
    - :param seperator: string seperator displayed between buttons (optional)
    - :param ret: set to true to return list of created buttons along with layout

    :return: populated QVBoxlayout / QHBoxlayout
    """
    if 'default' in buttons:
        defaults = theme.merge_style(theme[style], buttons.pop('default'))
    else:
        defaults = theme[style]

    if shape == 'column':
        layout = QVBoxLayout()
    else:
        shape = 'row'
        layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    if seperator != '':
        sep_style = {
            'color': defaults['color'], 'margin': 0, 'padding': 0, 'background': '#00000000'}

    button_list = []
    for i, (name, detail) in enumerate(buttons.items()):
        if 'style' in detail:
            button_style = theme.merge_style(defaults, detail['style'])
        else:
            button_style = defaults
        toggle_button = detail['toggle'] if 'toggle' in detail else None
        bt = create_button(theme, name, style, button_style, toggle_button)
        if 'callback' in detail and isinstance(detail['callback'], CALLABLE):
            if toggle_button:
                bt.clicked[bool].connect(detail['callback'])
            else:
                bt.clicked.connect(detail['callback'])
        stretch = detail['stretch'] if 'stretch' in detail else 0
        if 'align' in detail:
            layout.addWidget(bt, stretch, detail['align'])
        else:
            layout.addWidget(bt, stretch)
        button_list.append(bt)
        if seperator != '' and i < (len(buttons) - 1):
            sep_label = create_label(theme, seperator, 'label', sep_style)
            sep_label.setSizePolicy(SMAXMIN)
            layout.addWidget(sep_label, alignment=ACENTER)

    if ret:
        return layout, button_list
    else:
        return layout


def create_combo_box(
        theme: AppTheme, style: str = 'combobox', style_override: dict = {}) -> QComboBox:
    """
    Creates a combobox with given style and returns it.

    Parameters:
    - :param theme: reference to AppTheme
    - :param style: key for theme -> default style
    - :param style_override: style dict to override default style

    :return: styled QCombobox
    """
    combo_box = QComboBox()
    combo_box.setStyleSheet(theme.get_style_class('QComboBox', style, style_override))
    if 'font' in style_override:
        combo_box.setFont(theme.get_font(style, style_override['font']))
    else:
        combo_box.setFont(theme.get_font(style))
    combo_box.setSizePolicy(SMINMAX)
    combo_box.setCursor(Qt.CursorShape.PointingHandCursor)
    combo_box.view().setCursor(Qt.CursorShape.PointingHandCursor)
    return combo_box


def create_frame(
        theme: AppTheme, style: str = 'frame', style_override: dict = {},
        size_policy: QSizePolicy | None = None) -> QFrame:
    """
    Creates a frame with default styling

    Parameters:
    - :param theme: reference to AppTheme
    - :param style: style dict to override default style (optional)
    - :param size_policy: size policy of the frame (optional)

    :return: configured QFrame
    """
    frame = QFrame()
    frame.setStyleSheet(theme.get_style(style, style_override))
    frame.setSizePolicy(size_policy if size_policy is not None else SMAXMAX)
    return frame


def create_label(theme: AppTheme, text: str, style: str = 'label', style_override={}) -> QLabel:
    """
    Creates a label according to style with parent.

    Parameters:
    - :param theme: reference to AppTheme
    - :param text: text to be shown on the label
    - :param style: name of the style as in self.theme
    - :param style_override: style dict to override default style (optional)

    :return: configured QLabel
    """
    label = QLabel()
    label.setText(text)
    label.setStyleSheet(theme.get_style(style, style_override))
    label.setSizePolicy(SMAXMAX)
    if 'font' in style_override:
        label.setFont(theme.get_font(style, style_override['font']))
    else:
        label.setFont(theme.get_font(style))
    return label


def create_icon_button(
        theme: AppTheme, icon_name: str, tooltip: str = '', style: str = 'icon_button',
        style_override={}, icon_size: tuple = ()) -> QPushButton:
    """
    Creates a button showing an icon according to style with parent.

    Parameters:
    - :param theme: reference to AppTheme
    - :param icon_name: name of the icon to be shown on the button
    - :param tooltip: text to show when the mouse pointer is on the button
    - :param style: name of the style as in self.theme or style dict
    - :param style_override: style dict to override default style (optional)
    - :param icon_size: set icon size in case it should be different from the default

    :return: configured QPushButton
    """
    button = QPushButton('')
    button.setIcon(theme.icons[icon_name])
    if tooltip:
        button.setToolTip(tooltip)
    button.setStyleSheet(theme.get_style_class('QPushButton', style, style_override))
    if len(icon_size) != 2:
        icon_size = [theme.opt.icon_size] * 2
    button.setIconSize(QSize(*icon_size))
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setSizePolicy(SMAXMAX)
    return button


def create_entry(
        theme: AppTheme, default_value='', validator: QValidator | None = None,
        style: str = 'entry', style_override: dict = {}, placeholder: str = '') -> QLineEdit:
    """
    Creates an entry widget and styles it.

    Parameters:
    - :param theme: reference to AppTheme
    - :param default_value: default value for the entry
    - :param validator: validator to validate entered characters against
    - :param style: key for self.theme -> default style
    - :param style_override: style dict to override default style
    - :param placeholder: placeholder shown when entry is empty

    :return: styled QLineEdit
    """
    entry = QLineEdit(default_value)
    entry.setValidator(validator)
    entry.setPlaceholderText(placeholder)
    entry.setStyleSheet(theme.get_style_class('QLineEdit', style, style_override))
    if 'font' in style_override:
        entry.setFont(theme.get_font(style, style_override['font']))
    else:
        entry.setFont(theme.get_font(style))
    entry.setCursor(Qt.CursorShape.IBeamCursor)
    entry.setSizePolicy(SMAXMAX)
    return entry


def create_annotated_slider(
        theme: AppTheme, default_value: int = 1, min: int = 0, max: int = 3,
        style: str = 'slider', style_override_slider: dict = {}, style_override_label: dict = {},
        callback: Callable = lambda v: v) -> QHBoxLayout:
    """
    Creates Slider with label to display the current value.

    Parameters:
    - :param theme: reference to AppTheme
    - :param default_value: start value for the slider
    - :param min: lowest value of the slider
    - :param max: highest value of the slider
    - :param style: key for self.theme -> default style
    - :param style_override_slider: style dict to override default style
    - :param style_override_label: style dict to override default style
    - :param callback: callable to be attached to the valueChanged signal of the slider; will be \
    passed value the slider was moved to; must return value that the label should be set to

    :return: layout with slider
    """
    def label_updater(new_value):
        if isinstance(callback, CALLABLE):
            new_text = callback(new_value)
            slider_label.setText(str(new_text))

    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 3)
    layout.setSpacing(theme['defaults']['margin'])
    slider_label = create_label(
            theme, '', style, style_override=style_override_label)
    layout.addWidget(slider_label, alignment=AVCENTER)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(min, max)
    slider.setSingleStep(1)
    slider.setPageStep(1)
    slider.setValue(default_value)
    slider.setTickPosition(QSlider.TickPosition.NoTicks)
    slider.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
    slider.setSizePolicy(SMINMAX)
    slider.setStyleSheet(theme.get_style_class('QSlider', style, style_override_slider))
    slider.setFixedHeight(22)
    slider.valueChanged.connect(label_updater)
    layout.addWidget(slider, stretch=1, alignment=AVCENTER)
    label_updater(default_value)
    return layout
