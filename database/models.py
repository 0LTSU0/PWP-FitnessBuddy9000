from flask import Flask
from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()

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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="exercise")

#table for user information (name, email, age, creation date)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Float, nullable=False)
    user_creation_date = db.Column(db.DateTime, nullable=False)

    #initialize relationships
    measurements = db.relationship("Measurements", back_populates="user")
    exercise = db.relationship("Exercise", back_populates="user")

#table for daily measurements ( calories in/out, bodyweight, date, user id as foreign key)
class Measurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    calories_in = db.Column(db.Float, nullable=True)
    calories_out = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    #initialize relationship
    user = db.relationship("User", back_populates="measurements")
