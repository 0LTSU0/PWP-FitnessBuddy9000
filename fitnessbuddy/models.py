"""
Module for initializing database tables, json schemas and serializers
"""
import os
import json
from datetime import datetime
import click
from flask import Flask
from flask.cli import with_appcontext
from fitnessbuddy import db

class Exercise(db.Model):
    """
    Database model for exercise information
    (exercise name, duration in minutes, date, user id as foreign key)
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="exercise")

    def serialize(self):
        """
        Function for serializing exercise data item
        """
        return{
            "name": self.name,
            "duration": self.duration,
            "date": datetime.isoformat(self.date),
            "user_id": self.user_id,
            "id": self.id
        }
    def deserialize(self, doc):
        """
        Function for deserializing exercise data item
        """
        self.name = doc["name"]
        self.duration = doc["duration"]
        self.date = datetime.fromisoformat(str(doc["date"]))
        self.user_id = doc["user_id"]

    @staticmethod
    def json_schema():
        """
        JSON schema for exercise
        """
        schema = {
            "type": "object",
            "required": ["name", "date", "user_id"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Name of the exercise",
            "type": "string"
        }
        props["date"] = {
            "description": "Datetime of the exercise as a string",
            "type": "string"
        }
        props["user_id"] = {
            "description": "User id",
            "type": "number"
        }
        props["duration"] = {
            "description": "Duration of exercise",
            "type": "number"
        }
        return schema

class User(db.Model):
    """
    Database model for user information (name, email, age, creation date)
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Float, nullable=False)
    user_creation_date = db.Column(db.DateTime, nullable=False)

    #initialize relationships
    measurements = db.relationship("Measurements", cascade="all, delete-orphan",
                                    back_populates="user")
    exercise = db.relationship("Exercise", cascade="all, delete-orphan", back_populates="user")
    stats = db.relationship("Stats", cascade="all, delete-orphan", back_populates="user")

    def serialize(self):
        """
        Function for serializing user data item
        """
        return{
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "user_creation_date": datetime.isoformat(self.user_creation_date),
            "id": self.id
        }

    def deserialize(self, doc):
        """
        Function for deserializing user data item
        """
        self.name = doc["name"]
        self.email = doc["email"]
        self.age = doc["age"]
        self.user_creation_date = datetime.fromisoformat(str(doc["user_creation_date"]))

    @staticmethod
    def json_schema():
        """
        JSON schema for user
        """
        schema = {
            "type": "object",
            "required": ["name", "email", "age", "user_creation_date"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "User's name",
            "type": "string"
        }
        props["email"] = {
            "description": "User's email",
            "type": "string"
        }
        props["age"] = {
            "description": "User's age",
            "type": "number"
        }
        props["user_creation_date"] = {
            "description": "User's creation datetime as a string",
            "type": "string"
        }
        return schema

class Measurements(db.Model):
    """
    Database model for daily measurements
    (calories in/out, bodyweight, date, user id as foreign key)
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    calories_in = db.Column(db.Float, nullable=True)
    calories_out = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="measurements")

    def serialize(self):
        """
        Function for serializing measurements data item
        """
        return{
            "date": datetime.isoformat(self.date),
            "weight": self.weight,
            "calories_in": self.calories_in,
            "calories_out": self.calories_out,
            "user_id": self.user_id,
            "id": self.id
        }

    def deserialize(self, doc):
        """
        Function for deserializing measurements data item
        """
        self.date = datetime.fromisoformat(str(doc["date"]))
        self.weight = doc["weight"]
        self.calories_in = doc["calories_in"]
        self.calories_out = doc["calories_out"]
        self.user_id = doc["user_id"]

    @staticmethod
    def json_schema():
        """
        JSON schema for measurement
        """
        schema = {
            "type": "object",
            "required": ["date", "user_id"]
        }
        props = schema["properties"] = {}
        props["date"] = {
            "description": "Datetime of the measurement as a string",
            "type": "string"
        }
        props["user_id"] = {
            "description": "User id",
            "type": "number"
        }
        props["weight"] = {
            "description": "Weight measurement",
            "type": "number"
        }
        props["calories_in"] = {
            "description": "Calories eaten",
            "type": "number"
        }
        props["calories_out"] = {
            "description": "Calories burnt",
            "type": "number"
        }
        return schema
    
class Stats(db.Model):
    """
    Database model for user stats
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    total_exercises = db.Column(db.Integer, nullable=True)
    daily_exercises = db.Column(db.Float, nullable=True)
    daily_calories_in = db.Column(db.Float, nullable=True)
    daily_calories_out = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="stats")
    
    def serialize(self):
        """
        Function for serializing stats data
        """
        return{
            "date": datetime.isoformat(self.date),
            "total_exercises": self.total_exercises,
            "daily_exercises": self.daily_exercises,
            "daily_calories_in": self.daily_calories_in,
            "daily_calories_out": self.daily_calories_out,
            "user_id": self.user_id,
            "id": self.id
        }

    def deserialize(self, doc):
        """
        Function for deserializing stats data
        """
        self.date = datetime.fromisoformat(str(doc["date"]))
        self.total_exercises = doc["total_exercises"]
        self.daily_exercises = doc["daily_exercises"]
        self.daily_calories_in = doc["daily_calories_in"]
        self.daily_calories_out = doc["daily_calories_out"]
        self.user_id = doc["user_id"]
        
    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["date", "user_id"]
        }
        props = schema["properties"] = {}
        props["date"] = {
            "description": "Datetime when these stats were generated",
            "type": "string",
            "format": "date-time"
        }
        props["user_id"] = {
            "description": "User id",
            "type": "number"
        }
        props["total_exercises"] = {
            "description": "Total amount of exercises this user has done",
            "type": "number"
        }
        props["daily_exercises"] = {
            "description": "Average number of exercises per day",
            "type": "number"
        }
        props["daily_calories_in"] = {
            "description": "Average number of calories eaten per day",
            "type": "number"
        }
        props["daily_calories_out"] = {
            "description": "Average number of calories burnt per day",
            "type": "number"
        }
        return schema

@click.command("init-db")
@with_appcontext
def init_db_command():
    """
    Command for creating database
    """
    db.create_all()

@click.command("fill-db")
@with_appcontext
def fill_db_command():
    """
    Command for putting dummy data to database
    """
    with open(os.path.join(os.path.dirname(__file__), "..", "tools", "dummy_data.json"), "r",
        encoding="utf-8") as file:
        dummy_data = json.load(file)
        for user in dummy_data.get("Users"):
            entry = User(name=user.get("name"), email=user.get("email"), age=user.get("age"),
                        user_creation_date=datetime.strptime(user.get("date"),
                        "%d/%m/%y %H:%M:%S"))
            db.session.add(entry)
        db.session.commit()
        for exercise in dummy_data.get("Exercise_record"):
            entry = Exercise(name=exercise.get("name"), duration=exercise.get("duration"),
                date=datetime.strptime(exercise.get("date"), "%d/%m/%y %H:%M:%S"),
                user_id=exercise.get("user_id"))
            db.session.add(entry)
        db.session.commit()
        for meas in dummy_data.get("Measurements"):
            entry = Measurements(weight=meas.get("weight"), calories_in=meas.get("calories_in"),
                calories_out=meas.get("calories_out"), date=datetime.strptime(
                meas.get("date"),"%d/%m/%y %H:%M:%S"), user_id=meas.get("user_id"))
            db.session.add(entry)
        db.session.commit()
