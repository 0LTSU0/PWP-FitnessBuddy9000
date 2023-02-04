from flask import Flask
from flask_sqlalchemy import SQLAlchemy


if __name__ == "__main__":
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
else:
    db = SQLAlchemy() # If imported, don't pass app app object to allow for create_test_app()


# Create separate database for testing
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
    duration = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))

    #initialize relationship
    user = db.relationship("User", back_populates="exercise")

#table for user information (name, email, age, creation date)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    user_creation_date = db.Column(db.DateTime, nullable=False)

    #initialize relationships
    measurements = db.relationship("Measurements", back_populates="user")
    exercise = db.relationship("Exercise", back_populates="user")

#table for daily measurements ( calories in/out, bodyweight, date, user id as foreign key)
class Measurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    calories_in = db.Column(db.Integer, nullable=False)
    calories_out = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))

    #initialize relationship
    user = db.relationship("User", back_populates="measurements")
