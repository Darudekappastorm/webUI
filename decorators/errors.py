import json
import werkzeug
from marshmallow import ValidationError
from flask import request
import settings

with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)

settings.init()


def errors(func):
    """Decorator that wraps function in try/catch and handles all exceptions"""
    def error_wrapper(*args, **kwargs):
        """Error handler"""
        try:
            if request.method == "POST":
                if not request.json:
                    raise ValueError(MESSAGE['content-not-allowed']['message'],
                                     MESSAGE['content-not-allowed']['status'],
                                     MESSAGE['content-not-allowed']['type'])
            if not settings.machinekit_running:
                raise RuntimeError(MESSAGE['machinekit-down']['message'],
                                   MESSAGE['machinekit-down']['status'],
                                   MESSAGE['machinekit-down']['type'])
            return func(*args, **kwargs)

        except ValidationError as err:
            return {
                "errors": {
                    "keys": err.messages,
                    "status": 400,
                    "type": "ValidationError"
                }
            }, 400
        except ValueError as err:
            message, status, err_type = err
            return {
                "errors": {
                    "message": message,
                    "status": status,
                    "type": err_type
                }
            }, status
        except RuntimeError as err:
            message, status, err_type = err
            return {
                "errors": {
                    "message": message,
                    "status": status,
                    "type": err_type
                }
            }, status
        except NameError as err:
            message, status, err_type = err
            return {
                "errors": {
                    "message": message,
                    "status": status,
                    "type": err_type
                }
            }, status
        except (werkzeug.exceptions.BadRequest) as err:
            message, status, err_type = MESSAGE['invalid-content']
            return {
                "errors": {
                    "message": MESSAGE['invalid-content']['message'],
                    "status": MESSAGE['invalid-content']['status'],
                    "type": MESSAGE['invalid-content']['type']
                }
            }, MESSAGE['invalid-content']['status']
        except Exception as err:
            settings.logger.error(err)
            return {"errors": {"message": err.message}}, 500

    error_wrapper.__name__ = func.__name__
    return error_wrapper
