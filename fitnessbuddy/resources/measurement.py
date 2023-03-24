"""
Measurement resource implementations
"""

import json
from datetime import datetime
from flask import Response, request
from flask import url_for
from flask_restful import Resource
from fitnessbuddy.models import db, Measurements
from fitnessbuddy.utils import MasonBuilder
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from sqlalchemy.exc import IntegrityError

MASON = "application/vnd.mason+json"

class MeasurementsCollection(Resource):
    """
    Class for measurements
    """
    def get(self, user):
        """
        Get method for MeasurementCollection
        """
        # initialize response body
        body = []
        # find all users and add them to the response
        for item in Measurements.query.filter_by(user=user).all():
            measurement_item = item.serialize()
            body.append(measurement_item)

        res = MasonBuilder()
        res["measurements"] = body
        res.add_control("self", url_for("api.measurementscollection", user=user))
        res.add_control_post("fitnessbuddy:add-measurement", "fitnessbuddy:addmeasurement", url_for("api.measurementscollection", user=user), Measurements.json_schema())

        # return users
        return Response(json.dumps(res), 200, mimetype=MASON)

    def post(self, user):
        """
        Post method for MeasurementCollection
        """
        # check that request is json
        if not request.is_json:
            raise UnsupportedMediaType
        request.json["user_id"] = user.id
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

        res = MasonBuilder()
        res.add_control("self", url_for("api.measurementsitem", user=measurement.user, measurements=measurement))
        res.add_control_delete("Delete measurements", url_for("api.measurementsitem", user=measurement.user, measurements=measurement))
        res.add_control_put("Edit measurements", url_for("api.measurementsitem", user=measurement.user, measurements=measurement), Measurements.json_schema())

        return Response(json.dumps(res), 201, mimetype=MASON)


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
                description="Requested measurement does not correspond to requested user"
            )
        
        res = MasonBuilder()
        res["exercise"] = measurements.serialize()
        res.add_control("self", url_for("api.measurementsitem", user=measurements.user, measurements=measurements))
        return Response(json.dumps(res), 200, mimetype=MASON)

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
