"""
Measurement resource implementations
"""

import json
from datetime import datetime
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from fitnessbuddy.models import db, Measurements
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from sqlalchemy.exc import IntegrityError

class MeasurementsCollection(Resource):
    """
    Class for measurements
    """
    def get(self, user):
        """
        Get method for MeasurementCollection
        """
        # initialize response body
        body = {"measurements": []}
        # find all users and add them to the response
        for item in Measurements.query.filter_by(user=user).all():
            measurement_item = item.serialize()
            body["measurements"].append(measurement_item)

        # return users
        return Response(json.dumps(body), 200, mimetype="application/json")

    def post(self, user):
        """
        Post method for MeasurementCollection
        """
        # check that request is json
        if not request.is_json:
            raise UnsupportedMediaType
        # check json schema
        try:
            validate(request.json, Measurements.json_schema())
        except ValidationError as error:
            raise BadRequest() from error

        # initialize new user using deserializer
        try:
            measurement = Measurements()
            measurement.deserialize(request.json)
            measurement.user = user
        except (KeyError, ValueError, IntegrityError) as error:
            raise BadRequest() from error
        # add new user to database
        db.session.add(measurement)
        try:
            db.session.commit()
        except (KeyError, ValueError, IntegrityError):
            return Response(str(error), status=400)

        return Response(
            status=201,
            headers={
                "location": str(
                    url_for(
                        "api.measurementsitem",
                        user=measurement.user,
                        measurements=measurement,
                    )
                )
            },
        )


class MeasurementsItem(Resource):
    """
    Class for MeasurementItems
    """
    def get(self, user, measurements):
        """
        Get method for MeasurementItem
        """
        if user != measurements.user:
            raise BadRequest(
                description="requested measurement does not correspond to requested user"
            )
        body = measurements.serialize()
        return Response(json.dumps(body), 200, mimetype="application/json")

    def put(self, user, measurements):
        """
        Put method for MeasurementItem (used for updating entry)
        """
        # check that request is json
        if not request.is_json:
            raise UnsupportedMediaType
        if request.json["user_id"]:
            if not request.json["user_id"] == user.id:
                raise BadRequest(
                    description="UserID mismatch in request address and body"
                )
        else:
            request.json["user_id"] = user.id
        # check json schema
        try:
            validate(request.json, Measurements.json_schema())
        except Exception as error:
            raise BadRequest() from error

        # update database entry
        try:
            measurements.date = datetime.fromisoformat(request.json["date"])
            measurements.weight = request.json["weight"]
            measurements.calories_in = request.json["calories_in"]
            measurements.calories_out = request.json["calories_out"]
            measurements.user_id = request.json["user_id"]
            db.session.commit()
        except (KeyError, ValueError, IntegrityError) as error:
            return Response(str(error), status=400)
        return Response(
            status=204,
            headers={
                "location": str(
                    url_for(
                        "api.measurementsitem",
                        user=measurements.user,
                        measurements=measurements,
                    )
                )
            },
        )

    def delete(self, user, measurements):
        """
        Delete method for MeasurementItem
        """
        db.session.delete(measurements)
        db.session.commit()
        return Response(status=204)
