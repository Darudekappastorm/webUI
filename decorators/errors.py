from flask import request
import json
import configparser
import settings
import werkzeug
from marshmallow import ValidationError

config = configparser.ConfigParser()
config.read("default.ini")
with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


def errors(f):
    def errorWrapper(*args, **kwargs):
        try:
            if request.method == "POST":
                if not request.json:
                    raise ValueError(
                        errorMessages['content-not-allowed']['message'],
                        errorMessages['content-not-allowed']['status'],
                        errorMessages['content-not-allowed']['type'])
            if settings.machinekit_running == False:
                raise RuntimeError(errorMessages['machinekit-down']['message'],
                                   errorMessages['machinekit-down']['status'],
                                   errorMessages['machinekit-down']['type'])
            return f(*args, **kwargs)

        except ValidationError as err:
            return {
                "errors": {
                    "keys": err.messages,
                    "status": 400,
                    "type": "ValidationError"
                }
            }, 400
        except ValueError as e:
            message, status, errType = e
            return {
                "errors": {
                    "message": message,
                    "status": status,
                    "type": errType
                }
            }, status
        except RuntimeError as e:
            message, status, errType = e
            return {
                "errors": {
                    "message": message,
                    "status": status,
                    "type": errType
                }
            }, status
        except NameError as e:
            message, status, errType = e
            return {
                "errors": {
                    "message": message,
                    "status": status,
                    "type": errType
                }
            }, status
        except (werkzeug.exceptions.BadRequest) as e:
            message, status, errType = errorMessages['invalid-content']
            return {
                "errors": {
                    "message": errorMessages['invalid-content']['message'],
                    "status": errorMessages['invalid-content']['status'],
                    "type": errorMessages['invalid-content']['type']
                }
            }, errorMessages['invalid-content']['status']
        except Exception as e:
            return {"errors": {"message": e.message}}, 500

    errorWrapper.__name__ = f.__name__
    return errorWrapper
