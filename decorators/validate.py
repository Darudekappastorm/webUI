from flask import request
from marshmallow import ValidationError


def validate(schema):
    """Validates a marshmallow schema"""
    def real_decorator(func):
        def validate_wrapper(*args, **kwargs):
            """Validate marshmallow schema"""
            req = request.json
            errors = schema().load(req)

            if errors.errors:
                raise ValidationError(errors.errors)

            request.sanitizedRequest = errors.data
            return func(*args, **kwargs)

        return validate_wrapper

    return real_decorator
