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
    def get(self, user, measurements):
        if user != measurements.user:
            raise BadRequest(description="requested measurement does not correspond to requested user")
        body = measurements.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")
        
    def put(self, user, measurements):
        #check that request is json
        if not request.json:
            raise UnsupportedMediaType
        if request.json["user_id"]:
            if not request.json["user_id"] == user.id:
                raise BadRequest(description="UserID mismatch in request address and body")
        else:
            request.json["user_id"] = user.id
        #check json schema 
        try:
            validate(request.json, Measurements.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        #update database entry
        try:
            measurements.date = datetime.fromisoformat(request.json["date"])
            measurements.weight = request.json["weight"]
            measurements.calories_in = request.json["calories_in"]
            measurements.calories_out = request.json["calories_out"]
            measurements.user_id = request.json["user_id"]
            db.session.commit()
        except Exception as e:
            return Response(str(e), status=400)
        return Response(status=204, headers={"location":str(url_for("api.measurementsitem", user=measurements.user, measurements=measurements))})
    
    def delete(self, user, measurements):
        try:
            db.session.delete(measurements)
            db.session.commit()
        except Exception as e:
            Response(str(e), status=400)

        return Response(status=204)
