import json
import os
import re
import shutil
import sys
import webbrowser

from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QIcon

# --------------------------------------------------------------------------------------------------
# object methods
# --------------------------------------------------------------------------------------------------


def browse_path(self, default_path: str = None, types: str = 'Any File (*.*)', save=False) -> str:
    """
    Opens file dialog prompting the user to select a file.

    Parameters:
    - :param default_path: path that the file dialog opens at
    - :param types: string containing all file extensions and their respective names that are
    allowed.
    Format: "<name of file type> (*.<extension>);;<name of file type> (*.<extension>);; [...]"
    Example: "Logfile (*.log);;Any File (*.*)"
    """
    if default_path is None or default_path == '':
        default_path = self.app_dir
    default_path = os.path.abspath(default_path)
    if not os.path.exists(os.path.dirname(default_path)):
        default_path = self.app_dir
    if save:
        f = QFileDialog.getSaveFileName(self.window, 'Save Log', default_path, types)[0]
    else:
        f = QFileDialog.getOpenFileName(self.window, 'Open Log', default_path, types)[0]
        if not os.path.exists(f):
            return ''
    return f

# --------------------------------------------------------------------------------------------------
# static functions
# --------------------------------------------------------------------------------------------------


def get_asset_path(asset_name: str, app_directory: str) -> str:
    """
    returns the absolute path to a file in the asset folder

    Parameters:
    - :param asset_name: filename of the asset
    - :param app_directory: absolute path to app directory
    """
    fp = os.path.join(app_directory, 'assets', asset_name)
    if os.path.exists(fp):
        return fp
    else:
        return ''


def load_icon(filename: str, app_directory: str) -> QIcon:
    """
    Loads icon from path and returns it.

    Parameters:
    - :param path: path to icon
    - :param app_directory: absolute path to the app directory
    """
    return QIcon(get_asset_path(filename, app_directory))


def load_icon_series(icons: dict, app_directory: str) -> dict[str, QIcon]:
    """
    Loads multiple icons and returns dictionary containing the icons.

    Parameters:
    - :param icons: contains icons; format: {"<icon_name>": "<icon_path>", [...]}
    - :param app_directory: absolute path to app directory

    :return: dictionary containing icons; format: {"<icon_name>": "<icon>", [...]}
    """
    asset_path = os.path.join(app_directory, 'assets')
    icon_dict = dict()
    for icon_name, file_name in icons.items():
        icon_dict[icon_name] = QIcon(os.path.join(asset_path, file_name))
    return icon_dict


def open_link(link: str = ''):
    """
    Opens provided link
    """
    if link:
        webbrowser.open(link, new=2, autoraise=True)


def fetch_json(path: str) -> dict | list:
    """
    Fetches json from path and returns dictionary.

    Parameters:
    - :param path: path to json file
    """
    if not (os.path.exists(path) and os.path.isfile(path) and os.path.isabs(path)):
        raise FileNotFoundError('Invalid Path')
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def store_json(data: dict | list, path: str):
    """
    Stores data to json file at path. Overwrites file at target location.

    Paramters:
    - :param data: dictionary or list that should be stored
    - :param path: target location; must be absolute path
    """
    if not os.path.isabs(path):
        return
    try:
        with open(path, 'w') as file:
            json.dump(data, file)
    except OSError as e:
        sys.stdout.write(f'[Error] Data could not be saved: {e}')


def reset_temp_folder(path: str):
    '''
    Deletes and re-creates folder housing temporary log files.
    '''
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            raise FileExistsError(f'Expected path to folder, got "{path}"')
    os.mkdir(path)


def sanitize_file_name(txt, chr_set='extended') -> str:
    """Converts txt to a valid filename.

    Parameters:
    - :param txt: The path to convert.
    - :param chr_set:
        - 'printable':    Any printable character except those disallowed on Windows/*nix.
        - 'extended':     'printable' + extended ASCII character codes 128-255
        - 'universal':    For almost *any* file system.
    """
    FILLER = '-'
    MAX_LEN = 255  # Maximum length of filename is 255 bytes in Windows and some *nix flavors.

    # Step 1: Remove excluded characters.
    BLACK_LIST = set(chr(127) + r'<>:"/\|?*')
    white_lists = {
        'universal': {'-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'},
        'printable': {chr(x) for x in range(32, 127)} - BLACK_LIST,     # 0-32, 127 are unprintable,
        'extended': {chr(x) for x in range(32, 256)} - BLACK_LIST,
    }
    white_list = white_lists[chr_set]
    result = ''.join(x if x in white_list else FILLER for x in txt)

    # Step 2: Device names, '.', and '..' are invalid filenames in Windows.
    DEVICE_NAMES = (
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7',
            'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
            'CONIN$', 'CONOUT$', '..', '.')
    if '.' in txt:
        name, _, ext = result.rpartition('.')
        ext = f'.{ext}'
    else:
        name = result
        ext = ''
    if name in DEVICE_NAMES:
        result = f'-{result}-{ext}'

    # Step 3: Truncate long files while preserving the file extension.
    if len(result) > MAX_LEN:
        result = result[:MAX_LEN - len(ext)] + ext

    # Step 4: Windows does not allow filenames to end with '.' or ' ' or begin with ' '.
    result = re.sub(r"[. ]$", FILLER, result)
    result = re.sub(r"^ ", FILLER, result)

    return result
