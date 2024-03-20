import os
from re import sub as re_sub


def clean_player_id(id: str) -> str:
    """
    cleans player id and returns handle
    """
    return id[id.find(' ') + 1:-1]


def clean_entity_id(id: str) -> str:
    """
    cleans entity id and returns it
    """
    return re_sub(r'C\[([0-9]+) +?([a-zA-Z_0-9]+)\]', r'\2 \1', id).replace('_', ' ')


def get_entity_num(id: str) -> int:
    """
    gets entity number from entity id
    """
    if not id.startswith('C['):
        return -1
    try:
        return int(re_sub(r'C\[([0-9]+) +?([a-zA-Z_0-9]+)\]', r'\1', id))
    except ValueError:
        return int(re_sub(r'C\[([0-9]+) +?([a-zA-Z_0-9]+)\]_WCB', r'\1', id))
    except TypeError:
        return -1


def format_damage_tree_data(data, column: int) -> str:
    """
    Formats a data point according to TREE_HEADER

    Parameters:
    - :param data: unformatted data point
    - :param column: column of the data point in TREE_HEADER

    :return: formatted data point
    """
    if data == '':
        return ''
    if column == 0:
        if isinstance(data, tuple):
            return ''.join(data)
        return data
    elif column in (3, 5, 6, 7):
        return f'{data * 100:,.2f}%'
    elif column in (1, 2, 4, 13, 14, 15, 16, 17, 18):
        return f'{data:,.2f}'
    elif column in (8, 9, 10, 11, 12, 20, 21):
        return f'{data:,.0f}'
    elif column == 19:
        return f'{data}s'


def format_heal_tree_data(data, column: int) -> str:
    """
    Formats a data point according to HEAL_TREE_HEADER

    Parameters:
    - :param data: unformatted data point
    - :param column: column of the data point in HEAL_TREE_HEADER

    :return: formatted data point
    """
    if data == '':
        return ''
    if column == 0:
        if isinstance(data, tuple):
            return ''.join(data)
        return data
    elif column == 8:
        return f'{data * 100:,.2f}%'
    elif column in (1, 2, 3, 4, 5, 6, 7, 17, 18):
        return f'{data:,.2f}'
    elif column in (9, 10, 12, 13):
        return f'{data:,.0f}'
    elif column == 11:
        return f'{data}s'


def compensate_text(text: str) -> str:
    """
    Unescapes various characters not correctly represented in combatlog files

    Parameters:
    - :param text: str -> text to be cleaned

    :return: cleaned text
    """
    text = text.replace('â€“', '–')
    text = text.replace('Ãœ', 'Ü')
    text = text.replace('Ã¼', 'ü')
    text = text.replace('ÃŸ', 'ß')
    text = text.replace('Ã¶', 'ö')
    text = text.replace('Ã¤', 'ä')
    text = text.replace('â€˜', "'")
    return text


def format_path(path: str):
    if len(path) < 2:
        return path
    path = path.replace(chr(92), '/')
    if path[1] == ':' and path[0] >= 'a' and path[0] <= 'z':
        path = path[0].capitalize() + path[1:]
    if path[-1] != '/':
        if os.path.isdir(path):
            path += '/'
    return path


def format_data(el, integer=False) -> str:
    """
    rounds floats and ints to 2 decimals and sets 1000s seperators, ignores string values

    Parameters:
    - :param el: value to be formatted
    - :param integer: rounds numbers to zero decimal places when True (optional)
    """
    if isinstance(el, (int, float)):
        if not integer:
            return f'{el:,.2f}'
        else:
            return f'{el:,.0f}'
    elif isinstance(el, str):
        el = el.replace('â€“', '–')
        el = el.replace('Ãœ', 'Ü')
        el = el.replace('Ã¼', 'ü')
        el = el.replace('ÃŸ', 'ß')
        el = el.replace('Ã¶', 'ö')
        el = el.replace('Ã¤', 'ä')
        el = el.replace('â€˜', "'")
        return el
    else:
        return str(el)


def format_datetime_str(datetime: str) -> str:
    """
    Formats datetime string into datetime to be displayed.

    Parameters:
    - :param datetime: datetime string; for example "2022-02-23T14:00:27.100000Z"

    :return: formated datetime -> "2022-02-23 14:00:27"
    """
    parts = datetime[:-1].split(':')
    seconds = int(float(parts[-1]))
    return f'{parts[0].replace("T", " ")}:{parts[1]}:{seconds:02d}'
