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
                        errorMessages['4']['message'], errorMessages['4']['status'], errorMessages['4']['type'])
            if settings.machinekit_running == False:
                raise RuntimeError(
                    errorMessages['0']['message'], errorMessages['0']['status'], errorMessages['0']['type'])
            return f(*args, **kwargs)

        except ValidationError as err:
            return {"errors": {"keys": err.messages, "status": 400, "type": "ValidationError"}}, 400
        except ValueError as e:
            message, status, errType = e
            return {"errors": {"message": message, "status": status, "type": errType}}, status
        except RuntimeError as e:
            message, status, errType = e
            return {"errors": {"message": message, "status": status, "type": errType}}, status
        except NameError as e:
            message, status, errType = e
            return {"errors": {"message": message, "status": status, "type": errType}}, status
        except (werkzeug.exceptions.BadRequest) as e:
            message, status, errType = errorMessages['10']
            return {"errors": {"message": errorMessages['10']['message'], "status": errorMessages['10']['status'], "type": errorMessages['10']['type']}}, errorMessages['10']['status']
        except Exception as e:
            return {"errors": {"message": e.message}}, 500

    errorWrapper.__name__ = f.__name__
    return errorWrapper
