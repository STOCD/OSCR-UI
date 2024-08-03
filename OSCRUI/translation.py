import gettext
import os

def init_translation(lang_code='en'):
    """
    Initialize translation.
    :param lang_code: Language codes, Example: 'en', 'zh', 'fr'
    :return: gettext translation function
    """
    try:
        lang = gettext.translation('messages', localedir='locales', languages=[lang_code], fallback=True)
        lang.install()
    except Exception as e:
        print(e)

    return lang.gettext
