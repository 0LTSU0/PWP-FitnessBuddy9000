import json
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from fitnessbuddy.models import db, User
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

#resource for getting all users or adding new user
class UserCollection(Resource):
    def get(self):
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
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        #check json schema 
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
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


#resource for getting single user or modifying existing user
class UserItem(Resource):
    def get(self, user):
        body = user.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")
        
    def put(self, user):
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        #check json schema 
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        #update database entry
        try:
            user.name = request.json["name"]
            user.email = request.json["email"]
            user.age = request.json["age"]
            user.user_creation_date = datetime.fromisoformat(request.json["user_creation_date"])
            db.session.commit()
        except Exception as e:
            return Response(str(e), status=400)
        return Response(status=204, headers={"location":url_for("api.useritem", user=user)})
    
    def delete(self, user):
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)
