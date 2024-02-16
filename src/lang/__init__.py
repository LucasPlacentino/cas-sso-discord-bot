from .en import en_dict
from .fr import fr_dict
from os import getenv


LANG = getenv("LANG", "en")

def lang_str(string: str) -> str:
    if LANG == "fr":
        return fr_dict.get(string, en_dict.get(string, string))
    else:
        return en_dict.get(string, string)