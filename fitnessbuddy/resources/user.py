import json
from flask_restful import Resource, Response, request
from fitnessbuddy.api import api
from fitnessbuddy.models import db, User
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest

#resource for getting all users or adding new user
class UserCollection(Resource):
    def get(self):
        #initialize response body
        body = {
            "users": []}
        #find all users and add them to the response
        for item in User.query.all():
            user_item = item.serialize()
            body.append(user_item)

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
        db.session.commit()

        return Response(status=201, headers={"Location":api.url_for(UserItem,user=user)})

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
        
        user.deserialize(request.json)
        return Response(status=204, headers={"Location":api.url_for(UserItem,user=user)})
    
    def delete(self, user):
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)
