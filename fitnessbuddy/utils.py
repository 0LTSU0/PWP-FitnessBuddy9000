"""
Converter implementations
"""
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound
from fitnessbuddy.models import User, Measurements, Exercise

class UserConverter(BaseConverter):
    """
    Converter for user resource
    """
    def to_python(self, value):
        user = User.query.filter_by(id=value).first()
        if user is None:
            raise NotFound
        return user

    def to_url(self, value):
        return str(value.id)

class MeasurementsConverter(BaseConverter):
    """
    Converter for measurement resource
    """
    def to_python(self, value):
        measurement = Measurements.query.filter_by(id=value).first()
        if measurement is None:
            raise NotFound
        return measurement

    def to_url(self, value):
        return str(value.id)

class ExerciseConverter(BaseConverter):
    """
    Converter for exercise resource
    """
    def to_python(self, value):
        exercise = Exercise.query.filter_by(id=value).first()
        if exercise is None:
            raise NotFound
        return exercise

    def to_url(self, value):
        return str(value.id)
