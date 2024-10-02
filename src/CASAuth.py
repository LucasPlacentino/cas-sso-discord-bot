# inspired from https://github.com/DocHub-ULB/DocHub/blob/main/users/authBackend.py

import os
from dotenv import load_dotenv
#import requests
from httpx import AsyncClient
from furl import furl
import xml.etree.ElementTree as ET # or from lxml import etree as ET
import logging
from fastapi import Request

from .models import User
from .app import app, DEBUG

load_dotenv()

# TODO: all this for custom CAS authentication implementation

"""
Code originally from DocHub: https://github.com/DocHub-ULB/DocHub
"""

class CASAuth:
    CAS_ENDPOINT = os.getenv("CAS_ENDPOINT")
    XML_NAMESPACES = {
            "cas": "http://www.yale.edu/tp/cas",
        }
    CAS_TICKET_URL_PATH = os.getenv("CAS_TICKET_URL_PATH") # "/proxyValidate"

    async def getUser(self, request: Request, ticket=None):
        if not ticket:
            return None
        
        # Craft request to the CAS provider
        cas_ticket_url = furl(self.CAS_ENDPOINT)
        cas_ticket_url.path = "/proxyValidate" # os.getenv("CAS_TICKET_URL_PATH")
        cas_ticket_url.args["ticket"] = ticket
        cas_ticket_url.args["service"] = self.get_service_url()
        # cas_ticket_url = "https://{self.CAS_ENDPOINT}/proxyValidate?ticket={ticket}&service={service_url}"
        
        # Send the request
        #resp = requests.get(cas_ticket_url.url)
        async with AsyncClient(app=app) as ac:
            if os.getenv("CAS_USE_CUSTOM_CERT", False):
                response = await ac.get(cas_ticket_url.url, cert=os.getenv("CAS_CERT_PATH")) #! cert needed ?
            else:
                response = await ac.get(cas_ticket_url.url)
        
        if response.status_code != 200:
            #return None
            raise CasRequestError(response)
        
        user_dict = self._parse_response(response.text)

        # Get or create a user from the parsed user_dict
        #TODO:
        try:
            user = User.objects.get(netid=user_dict["netid"])
        except User.DoesNotExist:
            user = User.objects.create_user(
                netid=user_dict["netid"],
                email=user_dict["email"],
                first_name=user_dict["first_name"],
                last_name=user_dict["last_name"],
                register_method=self.LOGIN_METHOD,
            )
        user.last_login_method = self.LOGIN_METHOD
        user.save()

        return user

    # TODO: adapt
    def _parse_response(self, xml):
        # Try to parse the response from the CAS provider
        try:
            tree = ET.fromstring(xml)
        except ET.ParseError as e:
            raise CasParseError("INVALID_XML", xml) from e

        success = tree.find(
            "./cas:authenticationSuccess", namespaces=self.XML_NAMESPACES
        )
        if success is None:
            failure = tree.find(
                "./cas:authenticationFailure", namespaces=self.XML_NAMESPACES
            )
            if failure is not None:
                raise CasRejectError(failure.attrib.get("code"), failure.text)
            else:
                raise CasParseError("UNKNOWN_STRUCTURE", xml)

        netid_node = success.find("cas:user", namespaces=self.XML_NAMESPACES)
        if netid_node is not None:
            netid = netid_node.text
        else:
            logging.error(f"User has no netid in CAS response")
            raise CasParseError("UNKNOWN_STRUCTURE", xml)

        first_name_node = success.find(
            "./cas:attributes/cas:givenName", namespaces=self.XML_NAMESPACES
        )
        last_name_node = success.find(
            "./cas:attributes/cas:sn", namespaces=self.XML_NAMESPACES
        )

        id_matricule_node = success.find(
            "./cas:attributes/cas:supannRefId", namespaces=self.XML_NAMESPACES
        )
        complete_name_node = success.find(
            "./cas:attributes/cas:cn", namespaces=self.XML_NAMESPACES
        )
        group_node = success.find(
            "./cas:attributes/cas:supannRoleEntite", namespaces=self.XML_NAMESPACES
        )
        if DEBUG:
            logging.debug(f"CAS id_matricule_node: {id_matricule_node}")
            logging.debug(f"CAS complete_name_node: {complete_name_node}")
            logging.debug(f"CAS group_node: {group_node}")

        email_node = success.find(
            "./cas:attributes/cas:mail", namespaces=self.XML_NAMESPACES
        )
        if email_node is not None:
            email = email_node.text
        else:
            email = f"{netid}@ulb.ac.be" # or f"{netid}@ulb.be" ?
            logging.error(f"User {netid} has no email address in CAS response")
            #raise CasParseError("UNKNOWN_STRUCTURE", xml)

        if DEBUG:
            all_attributes = success.findall("./cas:attributes/*", namespaces=self.XML_NAMESPACES)
            for attr in all_attributes:
                logging.debug(f"CAS attribute: {attr.tag} => {attr.text}")

        return {
            "netid": netid, # userid ?
            "email": email,
            "first_name": first_name_node.text if first_name_node is not None else netid,
            "last_name": last_name_node.text if last_name_node is not None else netid,
        }

    #TODO: adapt
    @classmethod
    def get_login_url(cls):
        url = furl(cls.CAS_ENDPOINT)
        url.path = "/login" # os.getenv("CAS_LOGIN_PATH")
        url.args["service"] = cls.get_service_url()

        return url.url

    #TODO: adapt
    @classmethod
    def get_service_url(cls, request: Request):
        url = furl(os.getenv("CAS_SERVICE_BASE_URL")) #settings.BASE_URL)
        url.path = request.url_for("auth-ulb") # os.getenv("CAS_SERVICE_PATH")
        return url.url

    #TODO: adapt
    def authenticate(self, request, ticket=None):
        if not ticket:
            return None
        pass

class CasError(Exception):
    pass


class CasRequestError(CasError):
    pass


class CasParseError(CasError):
    pass


class CasRejectError(CasError):
    pass

