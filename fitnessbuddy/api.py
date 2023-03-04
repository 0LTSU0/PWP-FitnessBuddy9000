from flask import Blueprint
from flask_restful import Api

from fitnessbuddy.resources.exercise import ExerciseCollection, ExerciseItem
from fitnessbuddy.resources.user import UserCollection, UserItem
from fitnessbuddy.resources.measurement import MeasurementsCollection, MeasurementsItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

#add resources
api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")
api.add_resource(ExerciseCollection, "/users/<user:user>/exercises/")
api.add_resource(ExerciseItem, "/users/<user:user>/exercises/<exercise:exercise>/")
api.add_resource(MeasurementsCollection, "/users/<user:user>/measurements/")
api.add_resource(MeasurementsItem, "/users/<user:user>/measurements/<measurements:measurements>/")
