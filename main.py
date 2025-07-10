from multiprocessing import freeze_support, set_start_method
import os
import sys

from OSCRUI import OSCRUI


class Launcher():

    version = '2025.7.10.1'
    __version__ = '1.0'

    # holds the style of the app
    theme = {
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
            'font': ('Roboto Mono', 11, 'Normal'),
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
        #        :alternate is the alternate style -> s.c: table_alternate
        'table': {
            'color': '@fg',
            'background-color': '@bg',
            'gridline-color': 'rgba(0,0,0,0)',  # -> s.c: table_gridline
            'outline': '0',  # removes dotted line around clicked item
            'margin': (5, 0, 0, 0),
            'font': ('Roboto Mono', 12, 'Medium'),
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
            'font': ('Overpass', 12, 'Medium'),
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
            'font': ('Overpass', 12, 'Normal'),
            '::item': {
                'font': ('Roboto Mono', 12, 'Normal'),
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
                'image': 'url(assets/chevron-down.svg)'
            },
            # right-pointing arrow
            '::branch:closed:has-children': {
                'image': 'url(assets/chevron-right.svg)'
            }
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
                'image': 'url(assets/thick-chevron-down.svg)',
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
                             '#B45492', '#A27534', '#54A9B4', '#E47B1C', '#BCBCBC'),
        },
        'plot_legend': {
            'font': ('Overpass', 11, 'Medium'),
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
            'gridline-color': 'rgba(0,0,0,0)',  # -> s.c: table_gridline
            'outline': '0',  # removes dotted line around clicked item
            'margin': (4, 4, 4, 4),
            'font': ('Roboto Mono', 10, 'Medium'),
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
            'font': ('Overpass', 10, 'Medium'),
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
            'image': 'url(assets/resize.svg)',
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
        },
        # other style decisions
        's.c': {
            'sidebar_item_width': 0.2,
            'button_icon_size': 24,
            'table_alternate': True,
            'table_gridline': False,
            'overview_graph_stretch': 1,
            'overview_table_stretch': 1,
            'big_icon_size': 70
        }
    }

    @staticmethod
    def base_path() -> str:
        """initialize the base path"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            if getattr(sys, 'frozen', False):
                # The application is frozen
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.abspath(os.path.dirname(__file__))
        return base_path

    @staticmethod
    def app_config() -> dict:
        config = {
            'minimum_window_width': 1280,
            'minimum_window_height': 720,
            'settings_path': r'/.OSCR_settings.ini',
            'templog_folder_path': r'/~temp_log_files',
            'link_website': 'https://oscr.stobuilds.com',
            'link_github': 'https://github.com/STOCD/OSCR-UI',
            'link_downloads': 'https://github.com/STOCD/OSCR-UI/releases',
            'link_stobuilds': 'https://discord.gg/stobuilds',
            'link_stocd': 'https://github.com/STOCD',
            'live_graph_fields': ('DPS', 'Debuff', 'Attacks-in Share', 'HPS'),
            'ui_scale': 1,
            'live_scale': 1,
            'icon_size': 24,
            'default_settings': {
                'language': 'en',
                'log_path': '',
                'sto_log_path': '',
                'geometry': None,
                'live_geometry': None,
                'live_splitter': None,
                'dmg_columns|0': True,
                'dmg_columns|1': True,
                'dmg_columns|2': True,
                'dmg_columns|3': True,
                'dmg_columns|4': True,
                'dmg_columns|5': True,
                'dmg_columns|6': True,
                'dmg_columns|7': True,
                'dmg_columns|8': True,
                'dmg_columns|9': True,
                'dmg_columns|10': True,
                'dmg_columns|11': True,
                'dmg_columns|12': True,
                'dmg_columns|13': True,
                'dmg_columns|14': True,
                'dmg_columns|15': True,
                'dmg_columns|16': True,
                'dmg_columns|17': True,
                'dmg_columns|18': True,
                'dmg_columns|19': True,
                'dmg_columns|20': True,
                'dmg_columns_length': 21,
                'heal_columns|0': True,
                'heal_columns|1': True,
                'heal_columns|2': True,
                'heal_columns|3': True,
                'heal_columns|4': True,
                'heal_columns|5': True,
                'heal_columns|6': True,
                'heal_columns|7': True,
                'heal_columns|8': True,
                'heal_columns|9': True,
                'heal_columns|10': True,
                'heal_columns|11': True,
                'heal_columns|12': True,
                'heal_columns_length': 13,
                'seconds_between_combats': 45,
                'combat_min_lines': 20,
                'excluded_event_ids': ['Autodesc.Combatevent.Falling', ''],
                'graph_resolution': 0.2,
                'combats_to_parse': 10,
                'favorite_ladders': list(),
                'overview_sort_column': 1,
                'overview_sort_order': 'Descending',
                'auto_scan': False,
                'live_columns|0': True,
                'live_columns|1': False,
                'live_columns|2': True,
                'live_columns|3': False,
                'live_columns|4': False,
                'live_columns|5': False,
                'live_columns|6': False,
                'live_parser_opacity': 0.85,
                'live_graph_active': False,
                'live_graph_field': 0,
                'first_overview_tab': 0,
                'ui_scale': 1,
                'live_scale': 1,
                'live_enabled': False,
                'overview_splitter': None,
                'analysis_splitter': None,
                'analysis_graph': True,
                'live_player': 'Handle',
                'result_format': 'Compact',
            }
        }
        return config

    @staticmethod
    def launch():
        args = {}
        exit_code = OSCRUI(
                theme=Launcher.theme, args=args,
                path=Launcher.base_path(), config=Launcher.app_config(),
                versions=(Launcher.__version__, Launcher.version)).run()
        sys.exit(exit_code)


if __name__ == '__main__':
    freeze_support()
    set_start_method('spawn')
    Launcher.launch()
