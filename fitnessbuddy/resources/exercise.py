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
from fitnessbuddy.utils import MasonBuilder

MASON = "application/vnd.mason+json"

class ExerciseCollection(Resource):
    """
    Exercise resource
    """
    def get(self, user):
        """
        Get method for Exercise colleciton
        """
        body = []
        for item in Exercise.query.filter_by(user=user).all():
            excr_item = item.serialize()
            body.append(excr_item)

        res = MasonBuilder()
        res["exercises"] = body
        res.add_control("self", url_for("api.exercisecollection", user=user))
        res.add_control_post("add_exercise", "post", url_for("api.exercisecollection", user=user), Exercise.json_schema())

        return Response(json.dumps(res), 200, mimetype=MASON)

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
        
        res = MasonBuilder()
        res.add_control("self", url_for("api.exerciseitem", user=exrc.user, exercise=exrc))
        res.add_control_delete("delete", url_for("api.exerciseitem", user=exrc.user, exercise=exrc))
        res.add_control_put("edit", url_for("api.exerciseitem", user=exrc.user, exercise=exrc), Exercise.json_schema())

        return Response(json.dumps(res), 201, mimetype=MASON)


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
        
        res = MasonBuilder()
        res["exercise"] = exercise.serialize()
        res.add_control("self", url_for("api.exerciseitem", user=user, exercise=exercise))
        return Response(json.dumps(res), 200, mimetype=MASON)

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

        #204 has no response body
        return Response(status=204, headers={"location":str(url_for("api.exerciseitem",
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

        return Response("Entry deleted", status=204)
