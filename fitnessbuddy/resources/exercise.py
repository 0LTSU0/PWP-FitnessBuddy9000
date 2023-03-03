import json
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from fitnessbuddy.models import db, Exercise
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from datetime import datetime

class ExerciseCollection(Resource):
    def get(self, user):
        body = {"exercises": []}
        for item in Exercise.query.filter_by(user=user).all():
            excr_item = item.serialize()
            body["exercises"].append(excr_item)
        return Response(json.dumps(body), 200, mimetype="application/json")


    def post(self, user):
        #Validate request
        if not request.json:
            raise UnsupportedMediaType
        request.json["user_id"] = user.id
        try:
            validate(request.json, Exercise.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        exrc = Exercise()
        exrc.deserialize(request.json)
        exrc.user = user

        #Add entry to db
        db.session.add(exrc)
        try:
            db.session.commit()
        except Exception as e:
            return Response(str(e), status=400)

        return Response(status=201, headers={"location":str(url_for("api.exerciseitem", user=exrc.user, exercise=exrc))})


class ExerciseItem(Resource):
    def get(self, user, exercise):
        body = exercise.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")

    def put(self, user, exercise):
        if not request.json:
            raise UnsupportedMediaType
        if request.json["user_id"]:
            if not request.json["user_id"] == user.id:
                raise BadRequest(description="UserID mismatch in request address and body")
        else:
            request.json["user_id"] = user.id
        try:
            validate(request.json, Exercise.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        #update database entry
        try:
            exercise.name = request.json["name"]
            exercise.duration = request.json["duration"]
            exercise.user_id = request.json["user_id"]
            exercise.date = datetime.fromisoformat(request.json["date"])
            db.session.commit()
        except Exception as e:
            return Response(str(e), status=400)
        
        return Response(status=201, headers={"location":str(url_for("api.exerciseitem", user=exercise.user, exercise=exercise))})

        
    def delete(self, user, exercise):
        try:
            db.session.delete(exercise)
            db.session.commit()
        except Exception as e:
            Response(str(e), status=400)

        return Response("Entry deleted", status=200)
