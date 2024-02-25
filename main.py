import sys
import os

from OSCRUI import OSCRUI

class Launcher():

    version = '2024.2a231'

    # holds the style of the app
    theme = {
        # general style
        'app': {
            'bg': '#1a1a1a',
            'fg': '#eeeeee',
            'oscr': '#c82934',
            'font': ('Overpass', 15, 'normal'), # used when no font is specified in style definition
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
                    'width': 10,
                },
                'QScrollBar:horizontal': {
                    'height': 10,    
                },
                # space above and below the scrollbar handle
                'QScrollBar::add-page, QScrollBar::sub-page': {
                    'background': 'none'
                },
                # scroll bar handle
                'QScrollBar::handle': {
                    'background-color': 'rgba(0,0,0,.75)',
                    'border-radius': 5,
                    'border': 'none'
                },
                # scroll bar arrow buttons
                'QScrollBar::add-line, QScrollBar::sub-line': {
                    'height': 0 # hiding the arrow buttons
                },
                # top left corner of table
                'QTableCornerButton::section': {
                    'background-color': '#1a1a1a'
                }
            }
        },
        # shortcuts, @bg -> means bg in this sub-dictionary
        'defaults': {
            'bg': '#1a1a1a', # background
            'mbg': '#242424', # medium background
            'lbg': '#404040', # light background
            'oscr': '#c82934', # accent
            'loscr': '#20c82934', # light accent (12.5% opacity)
            'font': ('Overpass', 15, 'normal'),
            'fg': '#eeeeee', # foreground (usually text)
            'mfg': '#bbbbbb', # medium foreground
            'bc': '#888888', # border color
            'bw': 1, # border width
            'br': 2, # border radius
            'sep': 2, # seperator -> width of major seperating lines
            'margin': 10, # default margin between widgets
            'csp': 5, # child spacing -> content margin
            'isp': 15, # item spacing
        },
        # dark frame
        'frame': {
            'background-color': '@bg',
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
            'qproperty-indent': '0' # disables auto-indent
        },
        # default button
        'button': {
            'background': 'none',
            'color': '@fg',
            'text-decoration': 'none',
            'border': 'none',
            'border-radius': '@br',
            'margin': (3, 10, 3, 10),
            'padding': (2, 5, 0, 5),
            'font': ('Overpass', 15, 'medium'),
            ':hover': {
                'color': '@fg',
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@oscr'
            },
            ':disabled': {
                'color': '@bc'
            }
        },
        # big button (main tab switcher)
        'menu_button': {
            'background': 'none',
            'color': '@fg',
            'text-decoration': 'none', # removes underline
            'border': 'none',
            'margin': (6, 10, 4, 10),
            # 'margin-left': 10,
            # 'margin-top': 6,
            # 'margin-bottom': 4,
            # 'margin-right': 10,
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
            'margin': (4, 2, 1, 4),
            # 'margin-left': 4,
            # 'margin-top': 4,
            # 'margin-bottom': 1,
            # 'margin-right': 2,
            'padding': (2, 0, 2, 0),
            ':hover': {
                'background-color': 'rgba(136,136,136,.2)'
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
            }
        },
        # line of user-editable text
        'entry': {
            'background-color': '@lbg',
            'color': '@fg',
            'border-width': '@bw',
            'border-style': 'solid',
            'border-color': '@bc',
            'border-radius': '@br',
            'font': ('Overpass', 12, 'normal'),
            ':focus': { # cursor is inside the line
                'border-color': '@oscr'
            }
        },
        # scrollable list of items; ::item refers to the rows
        'listbox': {
            'background-color': '@lbg',
            'color': '@fg',
            'border-width': '@bw',
            'border-style': 'solid',
            'border-color': '@bc',
            'border-radius': '@br',
            'font': ('Overpass', 10, 'normal'),
            'outline': '0', # removes dotted line around clicked item
            '::item': {
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@lbg',
            },
            '::item:selected': {
                'background': 'none',
                'border-width': '@bw',
                'border-style': 'solid',
                'border-color': '@oscr',
                'border-radius': '@br',
            },
            # selected but not the last click of the user
            '::item:selected:!active': {
                'color':'@fg'
            },
            '::item:hover': {
                'background-color': '@loscr',
            },
        },
        # holds sub-pages
        'tabber': {
            'background': 'none',
            'border': 'none',
            'margin': 0,
            'padding': 0,
            '::pane': {
                'border': 'none'
            }
        },
        # default tabber buttons (hidden)
        'tabber_tab': {
            '::tab': {
                'height': 0,
                'width': 0
            }
        },
        # used in settings
        'toggle_button': {
            'width': '100%',
            'background': 'none',
            'color': '@fg',
            'text-decoration': 'none',
            'border-style': 'solid',
            'border-color': '@bc',
            'border-width': '@bw',
            'border-radius': '@br',
            'margin': (3, 3, 3, 3),
            'padding': (2, 5, 0, 5),
            'font': ('Overpass', 15, 'medium'),
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
        # table; ::item refers to the cells, :alternate is the alternate style -> s.c: table_alternate
        'table': {
            'color': '@fg',
            'background-color': '@bg',
            'border-width': '@bw',
            'border-style': 'solid',
            'border-color': '@bc',
            'gridline-color': 'rgba(0,0,0,0)', # -> s.c: table_gridline
            'outline': '0', # removes dotted line around clicked item
            'margin': (0, 10, 10, 0),
            'font': ('Roboto Mono', 15, 'Medium'),
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
            'outline': '0', # removes dotted line around clicked item
            'font': ('Overpass', 15, 'Medium'),
            '::section': {
                'background-color': '@mbg',
                'color': '@fg',
                'padding': (0, 0, 0, 0), #(0, -8, -3, 6), # don't ask
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
            'outline': '0', # removes dotted line around clicked item
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
        # analysis table; ::item refers to the cells; ::branch refers to the space on the left of the rows
        'tree_table': {
            'border': '1px solid #888888',
            'background-color': '@bg',
            'alternate-background-color': '@mbg',
            'color': '@fg',
            'margin': (10, 0, 10, 0),
            'outline': '0', # removes dotted line around clicked item
            'font': ('Overpass', 11, 'Normal'),
            '::item': {
                'font': ('Roboto Mono', 11, 'Normal'),
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
                'image': 'url(assets/arrow-down.svg)'
            },
            # right-pointing arrow
            '::branch:closed:has-children': {
                'image': 'url(assets/arrow-right.svg)'
            }
        },
        # header of the analysis table; ::section refers to the individual buttons
        'tree_table_header': {
            'background-color': '@bg',
            'border': 'none',
            'border-bottom-width': '@sep',
            'border-bottom-style': 'solid',
            'border-bottom-color': '@bc',
            'font': ('Overpass', 12, 'Medium'),
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
            'font': ('Overpass', 12, 'normal'),
            '::down-arrow': {
                'image': 'url(assets/fat-arrow-down.svg)',
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
        # frame of the plot widgets
        'plot_widget': {
            'border-style': 'solid',
            'border-width': '@bw',
            'border-color': '@bc',
            'margin': (10, 10, 10, 0),
            'padding': 10,
            'font': ('Overpass', 10, 'bold')
        },
        # undoes all styling of plot_widget to stop inheritance
        'plot_widget_nullifier': {
            'border': 'none',
            'margin': 0,
            'padding': 0,
        },
        # holds various properties related to graphing
        'plot': {
            'color_cycler': ('#b47254', '#545db4', '#a84a51', '#8f54b4', '#7FA95F', '#B45492', '#BFBC45', 
                             '#54A9B4', '#E47B1C', '#BCBCBC'),
        },
        'plot_legend': {
            'font': ('Overpass', 12, 'Medium'),
            'border-style': 'none',
            'padding': 0,
            'margin': 0
        },
        # other style decisions
        's.c': {
            'sidebar_item_width': 0.2,
            'button_icon_size': 24,
            'table_alternate': True,
            'table_gridline': False,
        }
    }

    @staticmethod
    def base_path() -> str:
        """initialize the base path"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return base_path

    @staticmethod
    def app_config() -> dict:
        config = {
            'minimum_window_width': 1280,
            'minimum_window_height': 720,
            'settings_path': r'/.OSCR_settings.ini',
            'default_settings': {
                'log_path': '',
                'geometry': None,
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
                'heal_columns_length' : 13
            }
        }
        return config

    @staticmethod
    def launch():
        args = {}
        exit_code = OSCRUI(version=Launcher.version, theme=Launcher.theme, args=args, 
                path=Launcher.base_path(), config=Launcher.app_config()
                ).run()
        sys.exit(exit_code)


if __name__ == '__main__':
    Launcher.launch()
