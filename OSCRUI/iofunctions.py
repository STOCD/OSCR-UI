import json
import os
from pathlib import Path
import webbrowser

from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QIcon


def browse_path(
        preset_path: Path, types: str = 'Any File (*.*)', save: bool = False) -> Path | None:
    """
    Opens file dialog prompting the user to select a file.

    Parameters:
    - :param preset_path: path that the file dialog opens at; includes default file name
    - :param types: string containing all file extensions and their respective names that are \
    allowed. \
    Format: `<name of file type> (*.<extension>);;<name of file type> (*.<extension>);; [...]` \
    Example: `Logfile (*.log);;Any File (*.*)`
    - :param save: False => open file with dialog; True => save file with dialog

    :return: returns selected path; None if user aborts or tries to open not-existing file
    """
    if save:
        f = QFileDialog.getSaveFileName(caption='Save Log', dir=str(preset_path), filter=types)[0]
        if f == '':
            return None
        return Path(f)
    else:
        f = QFileDialog.getOpenFileName(caption='Open Log', dir=str(preset_path), filter=types)[0]
        if f == '':
            return None
        selected_path = Path(f)
        if selected_path.exists():
            return selected_path
        else:
            return None


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


def save_to_json(path: Path, data: dict) -> bool:
    """
    Saves dictionary to JSON file using the json library. Returns `True` on success, `False` on
    failure.

    :param path: filepath to write the file to
    :param data: dictionary containing the data to be serialized
    """
    try:
        with path.open('w') as file:
            json.dump(data, file)
        return True
    except OSError:
        return False
