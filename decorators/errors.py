from flask import request
import json
import configparser
import settings
import werkzeug

config = configparser.ConfigParser()
config.read("default.ini")
with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


def errors(f):
    def errorWrapper(*args, **kwargs):
        try:
            if request.method == "POST":
                print(request.json)
                if not request.json:
                    raise ValueError(errorMessages['4'])
            if settings.machinekit_running == False:
                return {"errors": errorMessages['0']}, 500
            return f(*args, **kwargs)

        except ValueError as e:

            if type(e.message) == str:
                return {"errors": {"message": e.message, "status": 400, "type": "ValueError"}}, 400
            else:
                return {"errors": e.message}, e.message['status']
        except RuntimeError as e:
            return {"errors": e.message}, e.message['status']
        except KeyError as e:
            return {"errors": {"message": "Unknown key expected: " + e.message, "status": 400, "type": "KeyError"}}, 400
        except NameError as e:
            return {"errors": e.message}, e.message['status']
        except (werkzeug.exceptions.BadRequest) as e:
            return {"errors": errorMessages['10']}
        except Exception as e:
            return {"errors": {"message": e.message}}

    errorWrapper.__name__ = f.__name__
    return errorWrapper


# def errors(optional_parameter=""):
#     def realDecorator(f):
#         def errorWrapper(*args, **kwargs):
#             """ """
#             try:
#                 if request.method == "POST":
#                     if not request.json:
#                         raise Exception(errorMessages['4'])

#                 if config["storage"]["machinekit_running"] == False:
#                     return {"errors": errorMessages['0']}, 500
#                 return f(*args, **kwargs)
#             except ValueError as e:
#                 if type(e.message) == str:
#                     return {"errors": {"message": e.message, "status": 400, "type": "ValueError"}}, 400
#                 else:
#                     return {"errors": e.message}, 400
#             except RuntimeError as e:
#                 return {"errors": e.message}, 400
#             except KeyError as e:
#                 return {"errors": {"message": "Unknown key expected: " + e.message, "status": 400, "type": "KeyError"}}, 400
#             except NameError as e:
#                 return {"errors": e.message}, 404
#             except Exception as e:
#                 return {"errors": {"message": e.message}}
#         return errorWrapper
#     return realDecorator
