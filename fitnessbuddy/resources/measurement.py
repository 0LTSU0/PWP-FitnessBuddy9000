import json
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from fitnessbuddy.models import db, Measurements
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from datetime import datetime

class MeasurementsCollection(Resource):
    def get(self, user):
        #initialize response body
        body = {
            "measurements": []}
        #find all users and add them to the response
        for item in Measurements.query.filter_by(user=user).all():
            measurement_item = item.serialize()
            body["measurements"].append(measurement_item)

        #return users
        return Response(json.dumps(body), 200, mimetype="application/json")
    
    def post(self, user):
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        #check json schema 
        try:
            validate(request.json, Measurements.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        #initialize new user using deserializer
        measurement = Measurements()
        measurement.deserialize(request.json)
        measurement.user=user

        #add new user to database
        db.session.add(measurement)
        try:
            db.session.commit()
        except Exception as e:
            return Response(str(e), status=400)

        return Response(status=201, headers={"location":str(url_for("api.measurementsitem", user=measurement.user, measurements=measurement))})

class MeasurementsItem(Resource):
    def get(self, user, measurement):
        if user != measurement.user:
            raise BadRequest(description="requested measurement does not correspond to requested user")
        body = measurement.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")
        
    def put(self, user, measurement):
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        #check json schema 
        try:
            validate(request.json, Measurements.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        #update database entry
        try:
            measurement.date = datetime.fromisoformat(request.json["date"])
            measurement.weight = request.json["weight"]
            measurement.calories_in = request.json["calories_in"]
            measurement.calories_out = request.json["calories_out"]
            measurement.user_id = user.user_id
            db.session.commit()
        except Exception as e:
            return Response(str(e), status=400)
        return Response(status=204, headers={"api.MeasurementsItem":url_for(MeasurementsItem,meausrement=measurement)})
    
    def delete(self, user,  measurement):
        db.session.delete(measurement)
        db.session.commit()
        return Response(status=204)