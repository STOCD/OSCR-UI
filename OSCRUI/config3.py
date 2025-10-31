import os
from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings


class OSCRSettings():

    __slots__ = ('_settings', 'analysis_graph', 'auto_scan', 'combat_min_lines',
                 'combats_to_parse', 'copy_format', 'dmg_columns', 'favourite_ladders',
                 'first_overview_tab', 'graph_resolution', 'heal_columns', 'language', 'log_path',
                 'overview_sort_column', 'overview_sort_order', 'seconds_between_combats',
                 'sto_log_path', 'ui_scale', 'state__analysis_splitter', 'state__geometry',
                 'state__live_geometry', 'state__live_splitter', 'state__overview_splitter',
                 'liveparser__auto_enabled', 'liveparser__columns', 'liveparser__copy_kills',
                 'liveparser__graph_active', 'liveparser__graph_field',
                 'liveparser__player_display', 'liveparser__window_scale',
                 'liveparser__window_opacity')

    def __init__(self, settings_file_path: Path):
        self.analysis_graph: bool = True
        self.auto_scan: bool = False
        self.combat_min_lines: int = 20
        self.combats_to_parse: int = 10
        self.copy_format: str = 'Compact'
        self.dmg_columns: list[bool] = [True] * 21
        self.favourite_ladders: list[str] = list()
        self.first_overview_tab: int = 0
        self.graph_resolution: float = 0.2
        self.heal_columns: list[bool] = [True] * 13
        self.language: str = 'en'
        self.log_path: str = ''
        self.overview_sort_column: int = 1
        self.overview_sort_order: str = 'Descending'
        self.seconds_between_combats: int = 45
        self.sto_log_path: str = ''
        self.ui_scale: float = 1.0

        self.state__analysis_splitter: QByteArray = QByteArray()
        self.state__geometry: QByteArray = QByteArray()
        self.state__live_geometry: QByteArray = QByteArray()
        self.state__live_splitter: QByteArray = QByteArray()
        self.state__overview_splitter: QByteArray = QByteArray()

        self.liveparser__auto_enabled: bool = False
        self.liveparser__columns: list[bool] = [True, False, True, False, False, False, False]
        self.liveparser__copy_kills: bool = False
        self.liveparser__graph_active: bool = False
        self.liveparser__graph_field: int = 0
        self.liveparser__player_display: str = 'Handle'
        self.liveparser__window_scale: float = 1.0
        self.liveparser__window_opacity: float = 0.85

        if os.name == 'nt':
            self._settings = QSettings(str(settings_file_path), QSettings.Format.IniFormat)
        else:
            self._settings = QSettings(settings_file_path, QSettings.Format.NativeFormat)

        self.load_settings()

    def load_settings(self):
        for setting in self.__slots__:
            if setting.startswith('_'):
                continue
            setting_id = setting.replace('__', '/')
            if self._settings.contains(setting_id):
                item_type = type(getattr(self, setting))
                if item_type is list:
                    settings_item: list = getattr(self, setting)
                    if len(settings_item) > 0:
                        list_element_type = type(settings_item[0])
                    else:
                        list_element_type = str
                    item_list = self._settings.value(setting_id, type=list)
                    setattr(self, setting, [list_element_type(el) for el in item_list])
                else:
                    setattr(self, setting, self._settings.value(setting_id, type=item_type))

    def store_settings(self):
        for setting in self.__slots__:
            if not setting.startswith('_'):
                setting_id = setting.replace('__', '/')
                self._settings.setValue(setting_id, getattr(self, setting))


if __name__ == '__main__':
    sett = OSCRSettings(Path('new_settings.ini'))
    print({k: getattr(sett, k) for k in sett.__slots__})

    sett.liveparser__auto_enabled = True
    sett.overview_sort_order = 'Ascending'
    sett.heal_columns[3] = False
    sett.favourite_ladders.append('ISE')

    sett.store_settings()
