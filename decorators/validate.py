from flask import request
from marshmallow import ValidationError


def validate(schema):
    def realDecorator(f):
        def validateWrapper(*args, **kwargs):
            """ """
            req = request.json
            errors = schema().dump(req)

            if errors.errors:
                raise ValidationError(errors.errors)

            request.sanitizedRequest = errors.data
            return f(*args, **kwargs)

        return validateWrapper
    return realDecorator
