from os import getenv, listdir, path
import json
import logging

DEFAULT_LANG = getenv("DEFAULT_LANG", "en")
#DEBUG=True if getenv("DEBUG") is not None or getenv("DEBUG") != "" else False

class Locale:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.languages = {}
        self.lang_list = []
        self.locales_path = path.join(path.dirname(__file__),"../locales/")

        self.logger = logging.getLogger("lang")

        if self.debug:
            #logging.basicConfig(level=logging.DEBUG)
            logging.basicConfig(
                level=logging.DEBUG,
                format="{asctime} [{threadName}] ({filename}:{lineno}) [{levelname}]  {message}", # [{threadName}]
                style="{",
                datefmt="%Y-%m-%d %H:%M"
            )
            self.logger.info("Debug mode enabled")
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="{asctime} [{filename}:{lineno}-{levelname}]  {message}", # [{threadName}]
                style="{",
                datefmt="%Y-%m-%d %H:%M"
            )

        #for file in listdir(path.join(path.dirname(__file__))):
        for file in listdir(self.locales_path):
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
            self.logger.info(f"Found locale file: {self.locales_path}{file} => lang_code: {lang_code}")
            try:
                with open(path.join(self.locales_path, file), "r", encoding="utf-8") as lang_file:
                    self.languages[lang_code] = json.load(lang_file) # load json file as lang dict
                    self.lang_list.append(lang_code)
                self.logger.info(f"Successfully loaded {lang_code} locale file")
            except Exception as e:
                self.logger.error(f"Failed to load {lang_code} locale file: {e}")
    
    def lang_str(self, string: str, user_lang: str) -> str:
        if user_lang not in self.languages.keys():
            if self.debug:
                self.logger.debug(f"'{string}' translation in {user_lang} not found, using default language ({DEFAULT_LANG})")
            user_lang = DEFAULT_LANG
        return self.languages[user_lang].get(string, self.languages[DEFAULT_LANG].get(string, string))

