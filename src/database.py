# -*- coding: utf-8 -*-
import logging
import os

#from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from gsheets_connector import GSheetsConnector # TODO:

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class database():
    #TODO: db actions for any db type
    db_type = os.getenv("DB_TYPE")
    if db_type == "gsheets": # see https://www.cdata.com/kb/tech/gsheets-python-sqlalchemy.rst
        pass
    elif db_type == "mysql":
        pass
    elif db_type == "postgresql":
        pass
    elif db_type == "sqlite":
        pass
    else:
        raise NotImplementedError("DB_TYPE not implemented, must be one of \"gsheets\", \"mysql\", \"postgresql\", or \"sqlite\"")