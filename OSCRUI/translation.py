import gettext
from typing import Iterable


def init_translation(lang_code='en'):
    """
    Initialize translation.

    Parameters:
    - :param lang_code: Language codes, Example: 'en', 'zh', 'fr'

    :return: gettext translation function
    """
    if lang_code == 'en':
        return
    global translation_func
    translation_func = gettext.translation(
            'messages', localedir='locales', languages=[lang_code], fallback=True).gettext


def tr(message: str | Iterable[str]) -> str | tuple[str]:
    """
    Translates message into currently installed language. Accepts str or iterable of str. Iterables
    are returned as tuple object.
    """
    if isinstance(message, str):
        return translation_func(message)
    else:
        return tuple(translation_func(m) for m in message)
        # return map(translation_func, message)  # more memory efficient, but can't be indexed


def _identity(msg):
    return msg


if 'translation_func' not in globals():
    global translation_func
    translation_func = _identity
