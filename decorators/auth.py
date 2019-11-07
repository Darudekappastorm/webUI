import json
import configparser
from flask import request
config = configparser.ConfigParser()
config.read("default.ini")

with open("./jsonFiles/errorMessages.json") as f:
    message = json.load(f)

whiteList = config.get("security", "whitelisted").split(",")
blackList = config.get("security", "blackList").split(",")
ip_auth_enabled = (config['security'].get('ip_authentication_enabled') ==
                   'true') if True else False


def auth(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        if ip_auth_enabled:
            ip = request.remote_addr
            if ip in blackList:
                return {
                    "errors": message['whitelist-error']
                }, message['whitelist-error']['status']

            if request.method in ["POST", "UPDATE", "PUT"]:
                if (ip not in whiteList):
                    return {
                        "errors": message['whitelist-error']
                    }, message['whitelist-error']['status']

        headers = request.headers
        if not "API_KEY" in headers:
            return {
                "errors": message['authorization']
            }, message['authorization']['status']

        auth = headers.get("API_KEY")
        if auth != config['security']['token']:
            return {
                "errors": message['authorization']
            }, message['authorization']['status']

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper
