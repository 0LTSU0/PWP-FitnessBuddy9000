from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import click
from flask.cli import with_appcontext
from fitnessbuddy import db

# Create database
def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    app.app_context().push()
    return app, db

# Create database for testing
def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pytest.db"
    db.init_app(app)
    app.app_context().push()
    return app, db

#table for exercise information (exercise name, duration in minutes, date, user id as foreign key)
class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="exercise")

    def serialize(self):
        return{
            "name": self.name,
            "duration": self.duration,
            "date": self.date,
            "user_id": self.user_id
        }
    def deserialize(self, doc):
        self.name = doc["name"]
        self.duration = doc["duration"]
        self.date = datetime.fromisoformat(str(doc["date"]))
        self.user_id = doc["user_id"]

    @staticmethod
    def json_schema():
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
            "description": "Datetime of the measurement as a string",
            "type": "string"
        }
        props["user_id"] = {
            "description": "User id",
            "type": "number"
        }
        return schema

#table for user information (name, email, age, creation date)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Float, nullable=False)
    user_creation_date = db.Column(db.DateTime, nullable=False)

    #initialize relationships
    measurements = db.relationship("Measurements", cascade="all, delete-orphan", back_populates="user")
    exercise = db.relationship("Exercise", cascade="all, delete-orphan", back_populates="user")

    def serialize(self):
        return{
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "user_creation_date": datetime.isoformat(self.user_creation_date)
        }

    def deserialize(self, doc):
        self.name = doc["name"]
        self.email = doc["email"]
        self.age = doc["age"]
        self.user_creation_date = datetime.fromisoformat(str(doc["user_creation_date"]))

    @staticmethod
    def json_schema():
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

#table for daily measurements ( calories in/out, bodyweight, date, user id as foreign key)
class Measurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    calories_in = db.Column(db.Float, nullable=True)
    calories_out = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="cascade"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="measurements")

    def serialize(self):
        return{
            "date": self.date,
            "weight": self.weight,
            "calories_in": self.calories_in,
            "calories_out": self.calories_out,
            "user_id": self.user_id
        }

    def deserialize(self, doc):
        self.date = datetime.fromisoformat(str(doc["date"]))
        self.weight = doc["weight"]
        self.calories_in = doc["calories_in"]
        self.calories_out = doc["calories_out"]
        self.user_id = doc["user_id"]

    @staticmethod
    def json_schema():
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
        return schema

@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
