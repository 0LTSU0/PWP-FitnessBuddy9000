from werkzeug.routing import BaseConverter
from werkzeug.exceptions import Forbidden, NotFound
from fitnessbuddy.models import User, Measurements, Exercise

class UserConverter(BaseConverter):
    def to_python(self, id):
        user = User.query.filter_by(id=id).first()
        if user is None:
            raise NotFound
        return user
        
    def to_url(self, user):
        return str(user.id)

class MeasurementsConverter(BaseConverter):
    def to_python(self, date):
        measurement = Measurements.query.filter_by(date=date).first()
        if measurement is None:
            raise NotFound
        return measurement
        
    def to_url(self, measurement):
        return str(measurement.date)

class ExerciseConverter(BaseConverter):
    def to_python(self, id):
        exercise = Exercise.query.filter_by(id=id).first()
        if exercise is None:
            raise NotFound
        return exercise
        
    def to_url(self, exercise):
        return str(exercise.id)
