from os import getenv, listdir, path
import json

DEFAULT_LANG = getenv("DEFAULT_LANG", "en")

languages = {}
lang_list = []

for file in listdir(path.join(path.dirname(__file__))):
    if not file.endswith(".json"):
        continue
    lang_code = file.split(".")[0]
    if len(lang_code) != 2:
        continue
    print(f"Found locale file: {file} => lang_code: {lang_code}")
    try:
        with open(path.join(path.dirname(__file__), file), "r", encoding="utf-8") as f:
            languages[lang_code] = json.load(f)
            lang_list.append(lang_code)
        print(f"Successfully loaded {lang_code} locale file")
    except Exception as e:
        print(f"Failed to load {lang_code} locale file: {e}")

def lang_str(string: str, user_lang: str) -> str:
    if user_lang not in languages.keys():
        user_lang = DEFAULT_LANG
    return languages[user_lang].get(string, languages[DEFAULT_LANG].get(string, string))
