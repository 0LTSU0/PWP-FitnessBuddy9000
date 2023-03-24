"""
Resources for User
"""
import json
from datetime import datetime
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from sqlalchemy.exc import IntegrityError
from fitnessbuddy.models import db, User
from fitnessbuddy.utils import MasonBuilder

MASON = "application/vnd.mason+json"

class UserCollection(Resource):
    """
    Resource for user collections. Methods: get, post
    """
    def get(self):
        """
        Method for getting all user information
        """
        #initialize response body
        body = []
        res = MasonBuilder()
        #find all users and add them to the response
        for item in User.query.all():
            user_item = item.serialize()
            body.append(user_item)

        res["users"] = body
        res.add_control("self", "/api/users/")
        res.add_control_post("fitnessbuddy:add-user", "Add user", "/api/users/", User.json_schema())

        #return users
        return Response(json.dumps(res), 200, mimetype=MASON)

    def post(self):
        """
        Method for adding new user
        """
        #check that request is json
        if not request.is_json:
            raise UnsupportedMediaType
        #check json schema
        try:
            validate(request.json, User.json_schema())
        except ValidationError as error:
            raise BadRequest(description=str(error)) from error

        #initialize new user using deserializer
        user = User()
        user.deserialize(request.json)

        #add new user to database
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            return Response(status=400)
        
        res = MasonBuilder()
        res.add_control("self", url_for("api.useritem", user=user))
        res.add_control_delete("Delete user", url_for("api.useritem", user=user))
        res.add_control_put("Edit user", url_for("api.useritem", user=user), User.json_schema())

        return Response(json.dumps(res), 201, mimetype=MASON)


class UserItem(Resource):
    """
    Resource for single user items. Methods: get, put, delete
    """
    def get(self, user):
        """
        Method for getting user information for a specific user
        """
        res = MasonBuilder()
        res["user"] = user.serialize()
        res.add_control("self", url_for("api.useritem", user=user))
        res.add_control("fitnessbuddy:exercises-all", url_for("api.exercisecollection", user=user), title="All exercises")
        res.add_control("fitnessbuddy:measurements-all", url_for("api.measurementscollection", user=user), title="All measurements")
        res.add_control_delete("Delete user", url_for("api.useritem", user=user))
        res.add_control_put("Edit user", url_for("api.useritem", user=user), User.json_schema())
        
        return Response(json.dumps(res), 200, mimetype=MASON)

    def put(self, user):
        """
        Method for editing existing user information
        """
        #check that request is json
        if not request.is_json:
            raise UnsupportedMediaType
        #check json schema
        try:
            validate(request.json, User.json_schema())
        except ValidationError as error:
            raise BadRequest(description=str(error)) from error

        #update database entry
        try:
            user.name = request.json["name"]
            user.email = request.json["email"]
            user.age = request.json["age"]
            user.user_creation_date = datetime.fromisoformat(request.json["user_creation_date"])
            db.session.commit()
        except Exception as error:
            return Response(str(error), status=400)
        
        #204 has no response body
        return Response(status=204, headers={"location":url_for("api.useritem", user=user)})

    def delete(self, user):
        """
        Method for deleting existing user
        """
        db.session.delete(user)
        db.session.commit()
        #204 has no response body
        return Response(status=204)
