import copy

from PySide6.QtGui import QFont

WEIGHT_CONVERSION = {
    'normal': QFont.Weight.Normal,
    'bold': QFont.Weight.Bold,
    'extrabold': QFont.Weight.ExtraBold,
    'medium': QFont.Weight.Medium
}


class AppTheme:
    """Encapsulates theme functions and data."""

    def __init__(self, scale: float, theme_tree: dict[str] = {}):
        """
        Parameters:
        - :param scale: Used to adjust font sizes, margins, paddings, etc.
        - :param theme_tree: theme data to use instead of default theme
        """
        self.scale = scale
        self._theme_data: dict[str, dict] = theme_tree

    def __getitem__(self, key: str):
        return self._theme_data[key]

    def get_style(self, widget: str, override: dict[str] = {}) -> str:
        """
        Returns style sheet according to default style of widget with override style. Returns
        empty string if widget style is not defined in current theme.

        Parameters:
        - :param widget: name of the widget to grab the style for from the current theme
        - :param override: contains additional style or override style to replace the default \
        style with (optional)

        :return: str containing css style sheet
        """
        if widget in self._theme_data:
            if len(override) > 0:
                style = self.merge_style(self._theme_data[widget], override)
            else:
                style = self._theme_data[widget]
            return self.get_css(style)
        else:
            return ''

    def get_style_class(self, class_name: str, widget: str, override: dict[str] = {}) -> str:
        """
        Returns style sheet according to default style of widget with override style. Style only
        applies to `class_name`. Sub-controls (prefixed with `::`), pseudo-states (prefixed with
        `:`) and descendant selectors (prefixed with `~`) defined in current theme are formatted to
        only apply to the given `class_name`. Returns empty string with wdget style is not defined
        in current theme.

        Parameters:
        - :param class_name: name of the widget class to be styled
        - :param widget: name of the widget to grab the style for from the current theme; may be \
        empty string to only apply override styles
        - :param override: contains additional style or override style to replace the default \
        style with (optional)

        :return: str containing css style sheet
        """
        if widget == '':
            style = override
        elif widget in self._theme_data:
            if len(override) > 0:
                style: dict[str] = self.merge_style(self._theme_data[widget], override)
            else:
                style: dict[str] = self._theme_data[widget]
        else:
            return ''
        style_sheet = f'{class_name} {{{self.get_css(style)}}}'
        for prop, value in style.items():
            if prop.startswith(':'):
                style_sheet += f''' {class_name}{prop} {{{self.get_css(value)}}}'''
            elif prop.startswith('~'):
                style_sheet += f' {self.get_style_class(f"{class_name} {prop[1:]}", None, value)}'
        return style_sheet

    def merge_style(self, s1: dict[str], s2: dict[str]) -> dict[str]:
        """
        Returns new dictionary where the given styles are merged. Values in the second style take
        precedence. Up to one sub-dictionary is merged recursively.

        Parameters:
        - :param s1: Style-dict 1
        - :param s2: Style-dict 2

        :return: merged dictionary
        """
        result = copy.deepcopy(s1)
        for key, value in s2.items():
            if key in result.keys() and isinstance(result[key], dict) and isinstance(value, dict):
                result[key].update(value)
                continue
            result[key] = value
        return result

    def get_css(self, style: dict[str]) -> str:
        """
        Converts style dictionary into css style sheet. Values starting with `@` are treated as
        shortcuts and replaced with values from the `default` key of the current theme. Ignores
        property `font`, sub-controls (prefixed with `::`), pseudo-states (prefixed with
        `:`) and descendant selectors (prefixed with `~`).

        Parameters:
        - :param style: dictionary containg style to be converted to css

        :return: css style sheet
        """
        style_sheet = str()
        for prop, raw_value in style.items():
            if isinstance(raw_value, str) and raw_value.startswith('@'):
                prop_value = self._theme_data['defaults'][raw_value[1:]]
            else:
                prop_value = raw_value
            if prop.startswith(':') or prop.startswith('~') or prop == 'font':
                continue
            elif isinstance(prop_value, int):
                style_sheet += f'{prop}:{prop_value * self.scale}px;'
            elif isinstance(prop_value, tuple):
                scaled_values = map(lambda s: str(s * self.scale), prop_value)
                style_sheet += f'''{prop}:{'px '.join(scaled_values)}px;'''
            else:
                style_sheet += f'{prop}:{prop_value};'
        return style_sheet

    def get_font(self, widget: str, font_spec: tuple[str, int, str] | str = ()) -> QFont:
        """
        Returns QFont object with font specified in current theme or font_spec. Adds default
        fallback font families.

        Parameters:
        - :param widget: name of style to get font from
        - :param font_spec: font tuple consisting of family, size and weight OR font shortcut \
        (optional)

        :return: configured QFont object
        """
        try:
            if len(font_spec) != 3 and isinstance(font_spec, tuple):
                font_spec = self._theme_data[widget]['font']
            if isinstance(font_spec, str) and font_spec.startswith('@'):
                font = self._theme_data['defaults'][font_spec[1:]]
            else:
                font = font_spec
        except KeyError:
            font = self._theme_data['app']['font']
        font_family = (font[0], *self._theme_data['app']['font-fallback'])
        font_size = int(font[1] * self.scale)
        font_weight = WEIGHT_CONVERSION[font[2]]
        font = QFont(font_family, font_size, font_weight)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        return font

    def create_style_sheet(self, d: dict[str, dict]) -> str:
        """
        Creates Stylesheet from dictionary. Dictionary keys represent css selector. Ignores
        property `font`, sub-controls (prefixed with `::`), pseudo-states (prefixed with
        `:`) and descendant selectors (prefixed with `~`).

        Parameters:
        - :param d: style dictionary

        :return: string containing style sheet
        """
        style_sheet = str()
        for prop, prop_value in d.items():
            style_sheet += f'{prop} {{{self.get_css(prop_value)}}}'
        return style_sheet
