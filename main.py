from argparse import ArgumentParser
from multiprocessing import freeze_support, set_start_method, get_start_method
import os
import sys

from OSCRUI import OSCRUI


class Launcher():

    __version__ = '10.1.0'

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
                'live_copy_kills': False,
                'result_format': 'Compact',
            }
        }
        return config

    @staticmethod
    def launch():
        argparser = ArgumentParser(prog='OSCR UI', description='The OSCR parser app.')
        argparser.add_argument(
            '--config_dir', type=str, required=False,
            help='Change configuration directory (must be readable and writable)')
        args, _ = argparser.parse_known_args()
        exit_code = OSCRUI(
            args=args, path=Launcher.base_path(),
            config=Launcher.app_config(), version=Launcher.__version__).run()
        sys.exit(exit_code)


if __name__ == '__main__':
    freeze_support()
    try:
        set_start_method('spawn')
    except RuntimeError:
        if get_start_method() != 'spawn':
            set_start_method('spawn', force=True)
    Launcher.launch()
