import json
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from fitnessbuddy.models import db, Measurements
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest

class MeasurementsCollection(Resource):
    def get(self):
        #initialize response body
        body = {
            "measurements": []}
        #find all users and add them to the response
        for item in Measurements.query.all():
            meausrement_item = item.serialize()
            body.append(meausrement_item)

        #return users
        return Response(json.dumps(body), 200, mimetype="application/json")
    
    def post(self):
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        #check json schema 
        try:
            validate(request.json, Measurements.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        #initialize new user using deserializer
        meausrement = Measurements()
        meausrement.deserialize(request.json)

        #add new user to database
        db.session.add(meausrement)
        db.session.commit()

        return Response(status=201, headers={"api.MeasurementsItem":url_for(MeasurementsItem,meausrement=meausrement)})

class MeasurementsItem(Resource):
    def get(self, meausrement):
        body = meausrement.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")
        
    def put(self, meausrement):
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        #check json schema 
        try:
            validate(request.json, Measurements.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        meausrement.deserialize(request.json)
        return Response(status=204, headers={"api.MeasurementsItem":url_for(MeasurementsItem,meausrement=meausrement)})
    
    def delete(self, meausrement):
        db.session.delete(meausrement)
        db.session.commit()
        return Response(status=204)