# inspired from https://github.com/DocHub-ULB/DocHub/blob/main/users/authBackend.py

import os
from dotenv import load_dotenv
import requests
from furl import furl

load_dotenv()

# TODO:


class CASAuth
  CAS_ENDPOINT = os.getenv("CAS_ENDPOINT")
  LOGIN_METHOD = "cas"
    XML_NAMESPACES = {
        "cas": "http://www.yale.edu/tp/cas",
    }
  CAS_TICKET_URL_PATH = os.getenv("CAS_TICKET_URL_PATH") # "/proxyValidate"

  def getUser(self):
    pass

  def authenticate(self, request, ticket=None):
    if not ticket:
      return None
    pass


