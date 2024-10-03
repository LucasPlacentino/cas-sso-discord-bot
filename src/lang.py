from os import getenv, listdir, path
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_LANG = getenv("DEFAULT_LANG", "en")
DEBUG=False
if getenv("DEBUG") is not None or getenv("DEBUG") != "":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{asctime} [{threadName}] [{levelname}]  {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M"
    )
    DEBUG=True
    logger.debug("Debug mode enabled")
else:
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} [{threadName}] [{levelname}]  {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M"
    )

languages = {}
lang_list = [] # redundant with languages.keys()

locales_path: str = path.join(path.dirname(__file__),"../locales/")

#for file in listdir(path.join(path.dirname(__file__))):
for file in listdir(locales_path):
    if not file.endswith(".json"): #only get json files
        continue
    lang_code = file.split(".")[0] # get filename without extension
    if len(lang_code) == 5: # handle cases like "en_US.json"
        pre = file.split("_")[0]
        if pre is None or len(pre) != 2:
            continue
        lang_code = pre
    elif len(lang_code) != 2: # filename should be a 2-letter language code like "en.json"
        continue
    lang_code = lang_code.lower()
    logger.info(f"Found locale file: {locales_path}{file} => lang_code: {lang_code}")
    try:
        with open(path.join(locales_path, file), "r", encoding="utf-8") as lang_file:
            languages[lang_code] = json.load(lang_file) # load json file as lang dict
            lang_list.append(lang_code)
        logger.info(f"Successfully loaded {lang_code} locale file")
    except Exception as e:
        logger.error(f"Failed to load {lang_code} locale file: {e}")

def lang_str(string: str, user_lang: str) -> str:
    if user_lang not in languages.keys():
        if DEBUG:
            logger.debug(f"'{string}' translation in {user_lang} not found, using default language ({DEFAULT_LANG})")
        user_lang = DEFAULT_LANG
    return languages[user_lang].get(string, languages[DEFAULT_LANG].get(string, string))
