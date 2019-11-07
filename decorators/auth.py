import json
import configparser
from flask import request
CONFIG = configparser.ConfigParser()
CONFIG.read("default.ini")

with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)

WHITELIST = CONFIG.get("security", "whitelisted").split(",")
BLACKLIST = CONFIG.get("security", "blackList").split(",")
IP_AUTH_ENABLED = (CONFIG['security'].get('ip_authentication_enabled') ==
                   'true') if True else False


def auth(func):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        if IP_AUTH_ENABLED:
            ip = request.remote_addr
            if ip in BLACKLIST:
                return {
                    "errors": MESSAGE['whitelist-error']
                }, MESSAGE['whitelist-error']['status']

            if request.method in ["POST", "UPDATE", "PUT"]:
                if ip not in WHITELIST:
                    return {
                        "errors": MESSAGE['whitelist-error']
                    }, MESSAGE['whitelist-error']['status']

        headers = request.headers
        if not "API_KEY" in headers:
            return {
                "errors": MESSAGE['authorization']
            }, MESSAGE['authorization']['status']

        authentication = headers.get("API_KEY")
        if authentication != CONFIG['security']['token']:
            return {
                "errors": MESSAGE['authorization']
            }, MESSAGE['authorization']['status']

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper
