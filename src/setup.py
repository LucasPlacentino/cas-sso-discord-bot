import pip
from os import getenv
from dotenv import load_dotenv
load_dotenv()

# install the correct ormar dependencies based on the database type

# in requiremetns.txt: ormar[postgresql,sqlite,mysql]==...

#! ------ not used ------

db_type = getenv("DB_TYPE")

if db_type == "sqlite":
    pass
    #pip.