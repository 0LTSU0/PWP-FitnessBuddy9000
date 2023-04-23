import json
import pika
import os
import ssl
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from fitnessbuddy.models import db, Stats, Measurements, Exercise
from fitnessbuddy.utils import MasonBuilder

MASON = "application/vnd.mason+json"

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

usr = ""
pwd = ""

#get credentials from \client directory
cwd = os.getcwd()
credentials_file = str("{}\client\pikacredentials.json".format(cwd))
with open(credentials_file) as f:
    cred = json.load(f)
    usr = cred.get("user")
    pwd = cred.get("password")

class UserStats(Resource):
    """
    Resource for user's statistics. Methods: get, post, delete
    """
    def get(self, user):
        """
        Method for generating new user statistics whenever clients sents a get request.
        """
        #delete old stats
        for item in Stats.query.filter_by(user=user).all():
            db.session.delete(item)
        db.session.commit()

        #send task to generate new stats
        self.send_task(user)
        return Response(status=202)

    def post(self, user):
        """
        Method for posting new user statistics
        """
        print("GOT new post request")
        #check that request is json and has correct user id
        if not request.is_json:
            raise UnsupportedMediaType
        if request.json.get("user_id"):
            if not request.json["user_id"] == user.id:
                raise BadRequest(description="UserID mismatch in request address and body")
        #check json schema
        try:
            validate(request.json, Stats.json_schema())
        except ValidationError as error:
            raise BadRequest(description=str(error)) from error
        
        stats = Stats()
        stats.user = user
        stats.deserialize(request.json)
        db.session.add(stats)
        db.session.commit()
        return Response(status=204)

    def delete(self, user):
        """
        Method for deleting all existing statistics
        """
        for item in Stats.query.filter_by(user=user).all():
            db.session.delete(item)
        db.session.commit()
        return Response(status=204)
    
    def send_task(self, user):
        #get current data from user
        body_excr = []
        body_meas = []
        res = MasonBuilder()
        for item in Exercise.query.filter_by(user=user).all():
            excr_item = item.serialize()
            body_excr.append(excr_item)
        for item in Measurements.query.filter_by(user=user).all():
            measurement_item = item.serialize()
            body_meas.append(measurement_item)
        
        res["exercises"] = body_excr
        res["measurements"] = body_meas
        res["user"] = user.serialize()
        
        res.add_control_post("fitnessbuddy:add-stats", "Post new stats", url_for("api.userstats", user=user), Stats.json_schema())

        #connect to rabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="193.167.189.95",
                port=5672,
                virtual_host="ryhma-jll-vhost",
                credentials=pika.PlainCredentials(usr, pwd),
                ssl_options=pika.SSLOptions(context)
            )
        )
        #publish new task to "stats" queue
        channel = connection.channel()
        channel.queue_declare(queue="stats")
        channel.basic_publish(
            exchange="",
            routing_key="stats",
            body=json.dumps(res)
        )
        connection.close()
