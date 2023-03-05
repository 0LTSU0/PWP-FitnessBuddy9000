"""
Implementation for exercise resources
"""

import json
from datetime import datetime
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from fitnessbuddy.models import db, Exercise

class ExerciseCollection(Resource):
    """
    Exercise resource
    """
    def get(self, user):
        """
        Get method for Exercise colleciton
        """
        body = {"exercises": []}
        for item in Exercise.query.filter_by(user=user).all():
            excr_item = item.serialize()
            body["exercises"].append(excr_item)
        return Response(json.dumps(body), 200, mimetype="application/json")

    def post(self, user):
        """
        Post method for Exercise colleciton
        """
        #Validate request
        if not request.is_json:
            raise UnsupportedMediaType
        request.json["user_id"] = user.id
        try:
            validate(request.json, Exercise.json_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err)) from err

        exrc = Exercise()
        exrc.deserialize(request.json)
        exrc.user = user

        #Add entry to db
        db.session.add(exrc)
        try:
            db.session.commit()
        except Exception as exeption:
            return Response(str(exeption), status=400)

        return Response(status=201, headers={"location":str(url_for("api.exerciseitem",
            user=exrc.user, exercise=exrc))})


class ExerciseItem(Resource):
    """
    ExerciseItem resource
    """
    def get(self, user, exercise):
        """
        Get method for ExerciseItem
        """
        if user != exercise.user:
            raise BadRequest(description=
                "requested exercise does not correspond to requested user")
        body = exercise.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")

    def put(self, user, exercise):
        """
        Put method for ExerciseItem (used for modifying records)
        """
        if not request.is_json:
            raise UnsupportedMediaType
        if request.json.get("user_id"):
            if not request.json["user_id"] == user.id:
                raise BadRequest(description="UserID mismatch in request address and body")
        else:
            request.json["user_id"] = user.id
        try:
            validate(request.json, Exercise.json_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err)) from err

        #update database entry
        try:
            exercise.name = request.json["name"]
            exercise.duration = request.json["duration"]
            exercise.user_id = request.json["user_id"]
            exercise.date = datetime.fromisoformat(request.json["date"])
            db.session.commit()
        except Exception as err:
            return Response(str(err), status=400)

        return Response(status=201, headers={"location":str(url_for("api.exerciseitem",
            user=exercise.user, exercise=exercise))})

    def delete(self, user, exercise):
        """
        Delete method for ExerciseItem
        """
        try:
            db.session.delete(exercise)
            db.session.commit()
        except Exception as err:
            Response(str(err), status=400)

        return Response("Entry deleted", status=200)
