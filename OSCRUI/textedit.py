import os


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
            return data[0] + data[1]
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
            return data[0] + data[1]
        return data
    elif column == 8:
        return f'{data * 100:,.2f}%'
    elif column in (1, 2, 3, 4, 5, 6, 7, 17, 18):
        return f'{data:,.2f}'
    elif column in (9, 10, 12, 13):
        return f'{data:,.0f}'
    elif column == 11:
        return f'{data}s'


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


def format_damage_number(num: int) -> str:
    """
    Formats a number:
    - num < 10^3: 123.876 -> 123.9
    - 10^3 < num < 10^6: 123456.789 -> 123.5 k
    - 10^6 < num: 123456789 -> 123.5 M

    Parameters:
    - :param num: number to be formatted
    """
    if num > 1_000_000:
        return f'{num / 1_000_000:.1f} M'
    elif num > 1_000:
        return f'{num / 1000:.1f} k'
    else:
        return f'{num:.1f}'
