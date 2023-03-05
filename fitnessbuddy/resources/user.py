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


class UserCollection(Resource):
    """
    Resource for user collections. Methods: get, post
    """
    def get(self):
        """
        Method for getting all user information
        """
        #initialize response body
        body = {
            "users": []}
        #find all users and add them to the response
        for item in User.query.all():
            user_item = item.serialize()
            body["users"].append(user_item)

        #return users
        return Response(json.dumps(body), 200, mimetype="application/json")

    def post(self):
        """
        Method for adding new user
        """
        #check that request is json
        if not request.json:
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

        return Response(status=201, headers={"location":str(url_for("api.useritem", user=user))})


class UserItem(Resource):
    """
    Resource for single user items. Methods: get, put, delete
    """
    def get(self, user):
        """
        Method for getting user information for a specific user
        """
        body = user.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")

    def put(self, user):
        """
        Method for editing existing user information
        """
        #check that request is json
        if not request.json:
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
        return Response(status=204, headers={"location":url_for("api.useritem", user=user)})

    def delete(self, user):
        """
        Method for deleting existing user
        """
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)
