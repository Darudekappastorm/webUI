from flask import request
import json
import configparser
config = configparser.ConfigParser()
config.read("default.ini")

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


def auth(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        headers = request.headers
        if not "API_KEY" in headers:
            return {"errors": errorMessages['1']}, 403

        auth = headers.get("API_KEY")
        if auth != config['security']['token']:
            return {"errors": errorMessages['1']}, 403

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper
