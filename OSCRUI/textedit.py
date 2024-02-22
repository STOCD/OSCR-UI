import os
from re import sub as re_sub


def clean_player_id(id:str) -> str:
    """
    cleans player id and returns handle
    """
    return id[id.find(' ')+1:-1]

def clean_entity_id(id:str) -> str:
    """
    cleans entity id and returns it
    """
    return re_sub(r'C\[([0-9]+) +?([a-zA-Z_0-9]+)\]', r'\2 \1', id).replace('_', ' ')

def get_entity_num(id:str) -> int:
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
    
def compensate_text(text:str) -> str:
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
        if not integer: return f'{el:,.2f}'
        else: return f'{el:,.0f}'
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