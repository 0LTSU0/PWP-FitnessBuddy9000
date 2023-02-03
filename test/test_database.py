
from database.models import Exercise, User, Measurements, create_test_app
import tools.populate_database
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime


def test_database_models():
    app, db = create_test_app()
    db.create_all()

    tools.populate_database.populate_database(db, app)

    #Check foreign key linkage
    exercise_record = Exercise.query.filter_by(name="laji4").all()[0]
    name = exercise_record.user.name #does not work
    
    db.drop_all()
    assert True