import json
import configparser
from flask import request
config = configparser.ConfigParser()
config.read("default.ini")

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)

whiteList = config.get("security", "whitelisted").split(",")
blackList = config.get("security", "blackList").split(",")
ip_auth_enabled = (config['security'].get(
    'ip_authentication_enabled') == 'true') if True else False


def auth(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        if ip_auth_enabled:
            if request.remote_addr in blackList:
                return {"errors": errorMessages['whitelist-error']}, errorMessages['whitelist-error']['status']

            if request.method == "POST":
                if(request.remote_addr not in whiteList):
                    return {"errors": errorMessages['whitelist-error']}, errorMessages['whitelist-error']['status']

        headers = request.headers
        if not "API_KEY" in headers:
            return {"errors": errorMessages['authorization']}, errorMessages['authorization']['status']

        auth = headers.get("API_KEY")
        if auth != config['security']['token']:
            return {"errors": errorMessages['authorization']}, errorMessages['authorization']['status']

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper
