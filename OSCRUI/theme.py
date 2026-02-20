import copy

from PySide6.QtGui import QFont

WEIGHT_CONVERSION = {
    'normal': QFont.Weight.Normal,
    'bold': QFont.Weight.Bold,
    'extrabold': QFont.Weight.ExtraBold,
    'medium': QFont.Weight.Medium
}


class ThemeOptions:
    """Contains Theme options affecting the UI, but not directly related to the style"""

    __slots__ = ('sidebar_item_width', 'icon_size', 'default_icon_size', 'default_big_icon_size',
                 'table_alternate', 'table_gridline', 'overview_graph_stretch',
                 'overview_table_stretch')

    def __init__(self, initial_options: dict[str] = {}):
        """
        Parameters:
        - :param initial_options: options to use instead of defaults (optional)
        """
        self.sidebar_item_width: float = 0.2
        self.icon_size: int = 24
        self.default_icon_size: int = 24
        self.default_big_icon_size: int = 70
        self.table_alternate: bool = True
        self.table_gridline: bool = False
        self.overview_graph_stretch: int = 1
        self.overview_table_stretch: int = 1
        if len(initial_options) > 0:
            for option_name in self.__slots__:
                if option_value := initial_options.get(option_name):
                    setattr(self, option_name, option_value)


class AppTheme:
    """Encapsulates theme functions and data."""

    def __init__(self, scale: float, theme_tree: dict[str] = {}, theme_options: dict[str] = {}):
        """
        Parameters:
        - :param scale: Used to adjust font sizes, margins, paddings, etc.
        - :param theme_tree: theme data to use instead of default theme
        - :param theme_tree: options that affect the UI, but are not directly related to the style
        """
        self.scale = scale
        self.opt: ThemeOptions = ThemeOptions(theme_options)
        if len(theme_tree) > 0:
            self._theme_data: dict[str, dict] = theme_tree
        else:
            self._theme_data: dict[str, dict] = self.get_default_theme()

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
                style_sheet += f' {self.get_style_class(f"{class_name} {prop[1:]}", '', value)}'
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

    def get_default_theme(self) -> dict[str, dict]:
        """
        Returns default theme.
        """
        return {
            # general style
            'app': {
                'bg': '#1a1a1a',
                'fg': '#eeeeee',
                'oscr': '#c82934',
                'font': ('Overpass', 11, 'normal'),
                'heading': ('Overpass', 14, 'bold'),
                'subhead': ('Overpass', 12, 'medium'),
                'font-fallback': ('Yu Gothic UI', 'Nirmala UI', 'Microsoft YaHei UI', 'sans-serif'),
                'frame_thickness': 8,
                # this styles every item of the given type
                'style': {
                    # scroll bar trough (invisible)
                    'QScrollBar': {
                        'background': 'none',
                        'border': 'none',
                        'border-radius': 0,
                        'margin': 0
                    },
                    'QScrollBar:vertical': {
                        'width': 8,
                    },
                    'QScrollBar:horizontal': {
                        'height': 8,
                    },
                    # space above and below the scrollbar handle
                    'QScrollBar::add-page, QScrollBar::sub-page': {
                        'background': 'none'
                    },
                    # scroll bar handle
                    'QScrollBar::handle': {
                        'background-color': 'rgba(100,100,100,.75)',
                        'border-radius': 4,
                        'border': 'none'
                    },
                    # scroll bar arrow buttons
                    'QScrollBar::add-line, QScrollBar::sub-line': {
                        'height': 0  # hiding the arrow buttons
                    },
                    # top left corner of table
                    'QTableCornerButton::section': {
                        'background-color': '#1a1a1a'
                    },
                }
            },
            # shortcuts, @bg -> means bg in this sub-dictionary
            'defaults': {
                'bg': '#1a1a1a',  # background
                'mbg': '#242424',  # medium background
                'lbg': '#404040',  # light background
                'oscr': '#c82934',  # accent
                'loscr': '#20c82934',  # light accent (12.5% opacity)
                'font': ('Overpass', 11, 'normal'),
                'heading': ('Overpass', 14, 'bold'),
                'subhead': ('Overpass', 12, 'medium'),
                'small_text': ('Overpass', 10, 'normal'),
                'fg': '#eeeeee',  # foreground (usually text)
                'mfg': '#cccccc',  # medium foreground
                'bc': '#888888',  # border color
                'bw': 1,  # border width
                'br': 2,  # border radius
                'sep': 2,  # seperator -> width of major seperating lines
                'm': 3,  # outside margin
                'margin': 10,  # default margin between widgets
                'csp': 5,  # child spacing -> content margin
                'isp': 15,  # item spacing
            },
            # dark frame
            'frame': {
                'background-color': '@bg',
                'border-style': 'none',
                'margin': 0,
                'padding': 0
            },
            # medium frame
            'medium_frame': {
                'background-color': '@mbg',
                'margin': 0,
                'padding': 0
            },
            # light frame
            'light_frame': {
                'background': '@lbg',
                'margin': 0,
                'padding': 0
            },
            # default text (non-button, non-entry, non table)
            'label': {
                'color': '@fg',
                'margin': (3, 0, 3, 0),
                'qproperty-indent': '0',  # disables auto-indent
                'border-style': 'none',
                'font': '@font'
            },
            # heading label
            'label_heading': {
                'color': '@fg',
                'qproperty-indent': '0',
                'border-style': 'none',
                'font': '@heading'
            },
            # label for subheading
            'label_subhead': {
                'color': '@fg',
                'qproperty-indent': '0',
                'border-style': 'none',
                'margin-bottom': 3,
                'font': '@subhead'
            },
            # label for less intrusive text
            'label_light': {
                'color': '@mfg',
                'qproperty-indent': '0',
                'border-style': 'none',
                'margin': (3, 0, 3, 0),
                'font': ('Overpass', 12, 'normal')
            },
            # default button
            'button': {
                'background': 'none',
                'color': '@fg',
                'text-decoration': 'none',
                'border': 'none',
                'border-radius': '@br',
                'margin': (3, 3, 3, 3),
                'padding': (2, 5, 0, 5),
                'font': ('Overpass', 12, 'medium'),
                ':hover': {
                    'color': '@fg',
                    'border-width': '@bw',
                    'border-style': 'solid',
                    'border-color': '@oscr'
                },
                ':disabled': {
                    'color': '@bc'
                },
                # Tooltip
                '~QToolTip': {
                    'background-color': '@mbg',
                    'border-style': 'solid',
                    'border-color': '@lbg',
                    'border-width': '@bw',
                    'padding': (0, 0, 0, 0),
                    'color': '@fg',
                    'font': 'Overpass'
                }
            },
            # button for tab switching
            'tab_button': {
                'background': 'none',
                'color': '@fg',
                'text-decoration': 'none',
                'border-style': 'none',
                'border-width': '@bw',
                'border-color': '@oscr',
                'border-radius': '@br',
                'margin': (3, 3, 3, 3),
                'padding': (2, 5, 0, 5),
                'font': ('Overpass', 15, 'medium'),
                ':hover': {
                    'color': '@fg',
                    'border-style': 'solid',
                },
                ':checked': {
                    'border-style': 'solid',
                }
            },
            # big button (main tab switcher)
            'menu_button': {
                'background': 'none',
                'color': '@fg',
                'text-decoration': 'none',  # removes underline
                'border': 'none',
                'margin': (6, 10, 4, 10),
                'padding': 0,
                'font': ('Overpass', 20, 'bold'),
                ':hover': {
                    'text-decoration': 'underline',
                    'color': '@fg'
                },
                ':disabled': {
                    'color': '@bc'
                }
            },
            # inconspicious button
            'small_button': {
                'background': 'none',
                'border': 'none',
                'border-radius': 3,
                'margin': 0,
                'padding': (2, 0, 2, 0),
                ':hover': {
                    'background-color': 'rgba(136,136,136,.2)'
                },
                # Tooltip
                '~QToolTip': {
                    'background-color': '@mbg',
                    'border-style': 'solid',
                    'border-color': '@lbg',
                    'border-width': '@bw',
                    'padding': (0, 0, 0, 0),
                    'margin': (0, 0, 0, 0),
                    'color': '@fg',
                    'font': 'Overpass'
                }
            },
            # button that holds icon
            'icon_button': {
                'background': 'none',
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@bc',
                'border-radius': 3,
                'margin': 1,
                'padding': (2, 0, 2, 0),
                ':hover': {
                    'border-color': '@oscr'
                },
                ':checked': {
                    'border-color': '@oscr'
                },
                # Tooltip
                '~QToolTip': {
                    'background-color': '@mbg',
                    'border-style': 'solid',
                    'border-color': '@lbg',
                    'border-width': '@bw',
                    'padding': (0, 0, 0, 0),
                    'color': '@fg',
                    'font': 'Overpass'
                }
            },
            # line of user-editable text
            'entry': {
                'background-color': '@bg',
                'color': '@fg',
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@bc',
                'border-radius': '@br',
                'margin-top': '@csp',
                'font': '@small_text',
                'padding': 2,
                'selection-background-color': '#80c82934',
                # cursor is inside the line
                ':focus': {
                    'border-color': '@oscr'
                }
            },
            # horizontal seperator
            'hr': {
                'background-color': '@lbg',
                'border-style': 'none',
                'height': 1
            },
            # button that holds LiveParser icon
            'live_icon_button': {
                'background': 'none',
                'border-width': 1,
                'border-style': 'none',
                'border-color': '@fg',
                'border-radius': 3,
                'margin': (6, 10, 4, 10),
                'padding': (2, 1, 2, 0),
                ':hover': {
                    'border-style': 'solid'
                },
                ':checked': {
                    'border-style': 'solid',
                },
                # Tooltip
                '~QToolTip': {
                    'background-color': '@mbg',
                    'border-style': 'solid',
                    'border-color': '@lbg',
                    'border-width': '@bw',
                    'padding': (0, 0, 0, 0),
                    'color': '@fg',
                    'font': 'Overpass'
                }
            },
            # scrollable list of items; ::item refers to the rows
            'listbox': {
                'background-color': '@bg',
                'color': '@fg',
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@bc',
                'border-radius': '@br',
                'margin': 0,
                'font': '@small_text',
                'outline': '0',  # removes dotted line around clicked item
                '::item': {
                    'show-decoration-selected': '0',
                    'border-width': 1,  # hardcoded into the delegate!
                    'border-style': 'solid',
                    'border-color': '@bg',
                    'padding': 2  # for league listboxes
                    # 'padding': 4  # hardcoded into the delegate!
                },
                '::item:alternate': {
                    'background-color': '@mbg',
                    'border-color': '@mbg'
                },
                '::item:selected': {
                    'border-color': '@oscr',
                },
                # selected but not the last click of the user
                '::item:selected:!active': {
                    'color': '@fg'
                },
                '::item:hover': {
                    'border-color': '@oscr',
                },
            },
            # horizontal sliding selector
            'slider': {
                'font': ('Roboto Mono', 11, 'normal'),
                'color': '@fg',
                'margin-bottom': 3,
                '::groove:horizontal': {
                    'border-style': 'none',
                    'background-color': '@lbg',
                    'border-radius': '@bw',
                    'height': 5
                },
                '::handle:horizontal': {
                    'border-style': 'solid',
                    'border-width': '@bw',
                    'border-color': '@bc',
                    'border-radius': '@br',
                    'background-color': '@bc',
                    'width': 8,
                    'margin-top': -7,
                    'margin-bottom': -7
                },
                '::handle:horizontal:hover': {
                    'border-color': '@oscr'
                },
                '::handle:horizontal:pressed': {
                    'background-color': '#666666'
                },
            },
            # holds sub-pages
            'tabber': {
                'background': 'none',
                'border': 'none',
                'margin': 0,
                'padding': 0,
                '::pane': {
                    'border': 'none',
                    'padding': 0,
                    'margin': 0
                }
            },
            # used in settings
            'toggle_button': {
                'background': 'none',
                'color': '@fg',
                'text-decoration': 'none',
                'border-style': 'solid',
                'border-color': '@bc',
                'border-width': '@bw',
                'border-radius': '@br',
                'margin': (3, 3, 3, 3),
                'padding': (2, 5, 0, 5),
                'font': ('Overpass', 13, 'medium'),
                ':hover': {
                    'background-color': '@loscr',
                },
                ':checked': {
                    'border-color': '@oscr',
                },
                ':disabled': {
                    'color': '@bc'
                }
            },
            # table; ::item refers to the cells,
            #        :alternate is the alternate cell style
            'table': {
                'color': '@fg',
                'background-color': '@bg',
                'gridline-color': 'rgba(0,0,0,0)',
                'outline': '0',  # removes dotted line around clicked item
                'margin': (5, 0, 0, 0),
                'font': ('Roboto Mono', 12, 'normal'),
                '::item': {
                    'padding': (0, 5, 0, 5),
                    'border-width': '@bw',
                    'border-style': 'solid',
                    'border-color': '@bg',
                    'border-right-width': '@bw',
                    'border-right-style': 'solid',
                    'border-right-color': '@bc',
                },
                '::item:alternate': {
                    'padding': (0, 5, 0, 5),
                    'background-color': '@mbg',
                    'border-width': '@bw',
                    'border-style': 'solid',
                    'border-color': '@mbg',
                    'border-right-width': '@bw',
                    'border-right-style': 'solid',
                    'border-right-color': '@bc',
                },
                '::item:hover': {
                    'background-color': '@loscr',
                    'padding': (0, 5, 0, 5)
                },
                '::item:focus': {
                    'background-color': '@bg',
                    'color': '@fg',
                },
                '::item:selected': {
                    'background-color': '@bg',
                    'color': '@fg',
                    'border': '1px solid #c82934',
                },
                # selected but not the last click of the user
                '::item:alternate:focus': {
                    'background-color': '@mbg'
                },
                '::item:alternate:selected': {
                    'background-color': '@mbg'
                }
            },
            # heading of the table; ::section refers to the individual buttons
            'table_header': {
                'color': '@bg',
                'background-color': '@mbg',
                'border': 'none',
                'border-bottom-width': '@sep',
                'border-bottom-style': 'solid',
                'border-bottom-color': '@bc',
                'outline': '0',  # removes dotted line around clicked item
                'font': ('Overpass', 12, 'normal'),
                '::section': {
                    'background-color': '@mbg',
                    'color': '@fg',
                    'padding': (0, 0, 0, 0),
                    'border': 'none',
                    'margin': 0
                },
                '::section:hover': {
                    'background-color': '@loscr'
                },
            },
            # index of the table (vertical header); ::section refers to the individual buttons
            'table_index': {
                'color': '@bg',
                'background-color': '@mbg',
                'border': 'none',
                'border-right-width': '@sep',
                'border-right-style': 'solid',
                'border-right-color': '@bc',
                'outline': '0',  # removes dotted line around clicked item
                '::section': {
                    'background-color': '@mbg',
                    'color': '@fg',
                    'padding': (0, 3, 0, 3),
                    'border': 'none',
                    'margin': 0
                },
                '::section:hover': {
                    'background-color': '@loscr'
                },
            },
            # analysis table; ::item refers to the cells;
            #                 ::branch refers to the space on the left of the rows
            'tree_table': {
                'background-color': '@bg',
                'alternate-background-color': '@mbg',
                'color': '@fg',
                'margin': (5, 0, 0, 0),
                'outline': '0',  # removes dotted line around clicked item
                'font': ('Overpass', 12, 'normal'),
                '::item': {
                    'font': ('Roboto Mono', 12, 'normal'),
                    'border-right-width': '@bw',
                    'border-right-style': 'solid',
                    'border-right-color': '@bc',
                    'background-color': 'none',
                    'padding': (1, 4, 1, 4)
                },
                '::item:selected, ::item:focus': {
                    'border-width': '@bw',
                    'border-style': 'solid',
                    'border-color': '@oscr',
                    'color': '@fg'
                },
                '::item:hover, ::item:alternate:hover': {
                    'background-color': '@loscr',
                },
                '::branch:hover': {
                    'background-color': '@bg',
                    'border': 'none'
                },
                '::branch': {
                    'background-color': '@bg'
                },
                # down-pointing arrow
                '::branch:open:has-children': {
                    'image': 'url(assets_folder:chevron-down.svg)'
                },
                # right-pointing arrow
                '::branch:closed:has-children': {
                    'image': 'url(assets_folder:chevron-right.svg)'
                }
            },
            # font for analysis table cells, mirrors ['tree_table']['::item']['font']
            'tree_table_cells': {
                'font': ('Roboto Mono', 12, 'normal'),
            },
            # header of the analysis table; ::section refers to the individual buttons
            'tree_table_header': {
                'background-color': '@bg',
                'border': 'none',
                'border-bottom-width': '@sep',
                'border-bottom-style': 'solid',
                'border-bottom-color': '@bc',
                'font': '@subhead',
                '::section': {
                    'background-color': '@mbg',
                    'color': '@fg',
                    'border': 'none',
                },
                '::section:hover': {
                    'border-width': '@bw',
                    'border-style': 'solid',
                    'border-color': '@oscr',
                },
            },
            # combo box
            'combobox': {
                'border-style': 'solid',
                'border-width': '@bw',
                'border-color': '@bc',
                'border-radius': '@br',
                'background-color': '@bg',
                'padding': (2, 5, 0, 5),
                'color': '@fg',
                'font': '@subhead',
                '::down-arrow': {
                    'image': 'url(assets_folder:thick-chevron-down.svg)',
                    'width': '@margin',
                },
                '::drop-down': {
                    'border-style': 'none',
                    'padding': (2, 2, 2, 2)
                },
                '~QAbstractItemView': {
                    'background-color': '@mbg',
                    'border-style': 'solid',
                    'border-color': '@bc',
                    'border-width': '@bw',
                    'border-radius': '@br',
                    'color': '@fg',
                    'outline': '0',
                    '::item': {
                        'border-width': '@bw',
                        'border-style': 'solid',
                        'border-color': '@mbg',
                    },
                    '::item:hover': {
                        'border-color': '@oscr',
                    },
                }
            },
            # small window
            'dialog_window': {
                'background-color': '@oscr'
            },
            # frame of the plot widgets
            'plot_widget': {
                'border-bottom-color': '@bg',
                'margin': (0, 0, 5, 0),
                'padding': 10,
                'font': ('Overpass', 10, 'bold')
            },
            # undoes all styling of plot_widget to stop inheritance
            'plot_widget_nullifier': {
                'border': 'none',
                'margin': 0,
                'padding': 0,
            },
            # smaller tick font for live parser graph
            'live_plot_widget': {
                'font': ('Overpass', 9, 'medium')
            },
            # holds various properties related to graphing
            'plot': {
                'color_cycler': ('#8f54b4', '#B14D54', '#89B177', '#545DB4', '#C8B74E',
                                 '#B45492', '#A27534', '#54A9B4', '#E47B1C', '#BCBCBC')
            },
            'plot_legend': {
                'font': ('Overpass', 11, 'medium'),
                'border-style': 'none',
                'padding': 0,
                'margin': 0
            },
            'live_parser': {
                'background-color': '@bg',
                'border-style': 'solid',
                'border-color': '@oscr',
                'border-width': '@sep',
                'border-radius': '@br',
                'margin': 0,
                'padding': 0
            },
            'live_table': {
                'color': '@fg',
                'background-color': '@bg',
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@bc',
                'gridline-color': 'rgba(0,0,0,0)',
                'outline': '0',  # removes dotted line around clicked item
                'margin': (4, 4, 4, 4),
                'font': ('Roboto Mono', 10, 'medium'),
                '::item': {
                    'padding': (0, 2, 0, 2),
                    'margin': 0,
                    'border-width': '@bw',
                    'border-style': 'solid',
                    'border-color': '@bg',
                    'border-right-width': '@bw',
                    'border-right-style': 'solid',
                    'border-right-color': '@bc',
                },
                '::item:alternate': {
                    'background-color': '@mbg',
                }
            },
            # heading of the table; ::section refers to the individual buttons
            'live_table_header': {
                'color': '@bg',
                'background-color': '@mbg',
                'border': 'none',
                'border-bottom-width': '@sep',
                'border-bottom-style': 'solid',
                'border-bottom-color': '@bc',
                'outline': '0',  # removes dotted line around clicked item
                'font': ('Overpass', 10, 'medium'),
                '::section': {
                    'background-color': '@mbg',
                    'color': '@fg',
                    'padding': (0, 0, 0, 0),
                    'border': 'none',
                    'margin': 0
                },
            },
            # index of the table (vertical header); ::section refers to the individual buttons
            'live_table_index': {
                'color': '@bg',
                'background-color': '@mbg',
                'border': 'none',
                'border-right-width': '@sep',
                'border-right-style': 'solid',
                'border-right-color': '@bc',
                'outline': '0',  # removes dotted line around clicked item
                '::section': {
                    'background-color': '@mbg',
                    'color': '@fg',
                    'padding': (0, 2, 0, 2),
                    'border': 'none',
                    'margin': 0
                },
            },
            'resize_handle': {
                'border-style': 'none',
                'background-color': 'none',
                'image': 'url(assets_folder:resize.svg)',
            },
            'splitter': {
                'margin': (10, 0, 10, 0),
                'padding': 0,
                'border-style': 'solid',
                'border-width': '@bw',
                'border-color': '@bc',
                '::handle': {
                    'background-color': '@bc'
                },
                '::handle:pressed': {
                    'background-color': '@oscr'
                },
                '::handle:vertical': {
                    'height': '@bw',
                    'margin': (0, 13, 0, 13),
                }
            },
            # multiline text edit widget
            'textedit': {
                'border-style': 'solid',
                'border-width': '@bw',
                'border-color': '@bc',
                'border-radius': '@br',
                'background-color': '@bg',
                'color': '@fg',
                'font': ('Roboto Mono', 11, 'normal')
            }
        }
