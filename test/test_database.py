"""
Tests for database implementation
"""
import json
import pathlib
import tempfile
import os
from datetime import datetime
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from fitnessbuddy.models import Exercise, User, Measurements
from fitnessbuddy import create_app, db
import tools.populate_database


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    This is important function
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    '''
    Fixture
    '''
    tempfile.tempdir = os.path.dirname(__file__)
    db_fd, db_fname = tempfile.mkstemp(prefix="temppytest_")
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    appp = create_app(config)

    with appp.app_context():
        db.create_all()

    yield appp

    os.close(db_fd)
    # os.unlink(db_fname)


# Helper function to make sure some illegal insert throws an error
def insert_illegal(entry):
    """
    Try inserting illegal entry and check that exception happens
    """
    try:
        db.session.add(entry)
        db.session.commit()
        return False
    except Exception as exc:
        print(exc)
        db.session.rollback()
        return True


# Test all core database functionality
def test_database_models(app):
    """
    Test database models
    """
    with app.app_context():
        tools.populate_database.populate_database(db, app)
        with open(pathlib.Path(__file__).parent.parent.joinpath("tools", "dummy_data.json"),
            encoding="utf-8") as file:
            dummy_data = json.load(file)

        # Check that all expected data is in db
        user_data = User.query.all()
        expected_user_data = dummy_data.get("Users")
        i = 0
        for user in user_data:
            assert user.name == expected_user_data[i].get("name")
            assert user.email == expected_user_data[i].get("email")
            assert user.age == expected_user_data[i].get("age")
            assert user.user_creation_date == datetime.strptime(
                expected_user_data[i].get("date"), '%d/%m/%y %H:%M:%S')
            i += 1
        measurement_data = Measurements.query.all()
        expected_measurement_data = dummy_data.get("Measurements")
        i = 0
        for meas in measurement_data:
            assert meas.date == datetime.strptime(
                expected_measurement_data[i].get("date"), '%d/%m/%y %H:%M:%S')
            assert meas.weight == expected_measurement_data[i].get("weight")
            assert meas.calories_in == expected_measurement_data[i].get(
                "calories_in")
            assert meas.calories_out == expected_measurement_data[i].get(
                "calories_out")
            assert meas.user_id == expected_measurement_data[i].get("user_id")
            i += 1
        exercise_data = Exercise.query.all()
        expected_excercise_data = dummy_data.get("Exercise_record")
        i = 0
        for exercise in exercise_data:
            assert exercise.name == expected_excercise_data[i].get("name")
            assert exercise.duration == expected_excercise_data[i].get(
                "duration")
            assert exercise.date == datetime.strptime(
                expected_excercise_data[i].get("date"), '%d/%m/%y %H:%M:%S')
            assert exercise.user_id == expected_excercise_data[i].get(
                "user_id")
            i += 1

        # Check exercise - user linkage ("laji4" should be linked to user id 2)
        test_exercise_record = Exercise.query.filter_by(name="laji4").all()[0]
        assert test_exercise_record.user == User.query.filter_by(id=2)[0]

        # Check measurement - user linkage (meas 13 should be linked to user id 9)
        test_measurement_record = Measurements.query.filter_by(weight=500.5).all()[
            0]
        assert test_measurement_record.user == User.query.filter_by(id=9)[0]

        # Check user - exercise linkage (user id 8 should have laji15 and laji19,
        # user id 9 should not have any)
        test_user_record = User.query.filter_by(id=8)[0]
        assert test_user_record.exercise == [Exercise.query.filter_by(
            name="laji15").all()[0], Exercise.query.filter_by(name="laji16").all()[0]]
        test_user_record = User.query.filter_by(id=9)[0]
        assert test_user_record.exercise == []

        # Check user - measurement linkage (user id 3 should have 2 records, id 1 none)
        test_user_record = User.query.filter_by(id=3)[0]
        assert test_user_record.measurements == [Measurements.query.filter_by(
            calories_in=1000).all()[0], Measurements.query.filter_by(calories_in=1100).all()[0]]
        test_user_record = User.query.filter_by(id=1)[0]
        assert test_user_record.measurements == []


def test_ondeletes(app):
    """
    Test ondelete behavior
    """
    with app.app_context():
        tools.populate_database.populate_database(db, app)

        # Check that Measurements and Excercies are correctly linked to userid 3
        for entry in Measurements.query.filter_by(user_id=3).all():
            assert entry.user.name == "name3"
            assert entry.user.email == "some3@email.com"
            assert entry.user.age == 23
            assert entry.user.user_creation_date == datetime.strptime(
                "03/01/23 03:00:00", "%d/%m/%y %H:%M:%S")
        for entry in Exercise.query.filter_by(user_id=3).all():
            assert entry.user.name == "name3"
            assert entry.user.email == "some3@email.com"
            assert entry.user.age == 23
            assert entry.user.user_creation_date == datetime.strptime(
                "03/01/23 03:00:00", "%d/%m/%y %H:%M:%S")

        # Delete User 3
        User.query.filter_by(id=3).delete()
        db.session.commit()

        # All references to user 3 should be nulled
        for entry in Exercise.query.filter_by(user_id=3).all():
            assert entry.user is None
        for entry in Exercise.query.filter_by(user_id=3).all():
            assert entry.user is None


# Test all nullability constraints
def test_nullability(app):
    """
    Test nullability restrictions
    """
    with app.app_context():
        # Test User
        user_entry = {"date": "01/01/23 01:00:00",
                      "name": "name1", "email": "some1@email.com", "age": 21}
        entry = User(name=None, email=user_entry.get("email"), age=user_entry.get("age"),
            user_creation_date=datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
        assert insert_illegal(entry)
        entry = User(name=user_entry.get("name"), email=None, age=user_entry.get("age"),
            user_creation_date=datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
        assert insert_illegal(entry)
        entry = User(name=user_entry.get("name"), email=user_entry.get("email"), age=None,
            user_creation_date=datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
        assert insert_illegal(entry)
        entry = User(name=user_entry.get("name"), email=user_entry.get(
            "email"), age=user_entry.get("age"), user_creation_date=None)
        assert insert_illegal(entry)

        # Create a valid user to use with excercise/measurements
        entry = User(name=user_entry.get("name"), email=user_entry.get("email"),
            age=user_entry.get("age"),
            user_creation_date=datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
        db.session.add(entry)
        db.session.commit()

        # Test Measurement
        measurement_entry = {"date": "01/01/23 01:00:00", "weight": 10.1,
                             "calories_in": 1000, "calories_out": 100, "user_id": 1}
        entry = Measurements(weight=measurement_entry.get("weight"),
            calories_in=measurement_entry.get("calories_in"),
            calories_out=measurement_entry.get("calories_out"), date=None,
            user_id=measurement_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Measurements(weight=measurement_entry.get("weight"),
            calories_in=measurement_entry.get("calories_in"), calories_out=None,
            date=datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=None)
        assert insert_illegal(entry)

        # Test Excercise
        excercise_entry = {"date": "10/01/23 11:00:00",
                           "name": "laji1", "duration": 100, "user_id": 1}
        entry = Exercise(name=None, duration=excercise_entry.get("duration"),
            date=datetime.strptime(excercise_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=excercise_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Exercise(name=excercise_entry.get("name"), duration=excercise_entry.get(
            "duration"), date=None, user_id=excercise_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Exercise(name=excercise_entry.get("name"), duration=excercise_entry.get(
            "duration"), date=datetime.strptime(excercise_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=None)
        assert insert_illegal(entry)


# Test all fields where type restriction causes an error with wrong data (types: float, datetime)
def test_restrictions(app):
    """
    Test restrictions other than nullables
    """
    with app.app_context():
        # User
        user_entry = {"date": "01/01/23 01:00:00",
                      "name": "name1", "email": "some1@email.com", "age": 21}
        entry = User(name=user_entry.get("name"), email=user_entry.get("email"), age="asd",
            user_creation_date=datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
        assert insert_illegal(entry)
        entry = User(name=user_entry.get("name"), email=user_entry.get(
            "email"), age=123, user_creation_date="asd")
        assert insert_illegal(entry)

        # Valid user to test excercise and measurement
        entry = User(name=user_entry.get("name"), email=user_entry.get("email"),
            age=user_entry.get("age"),
            user_creation_date=datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
        db.session.add(entry)
        db.session.commit()

        # Excercise
        excercise_entry = {"date": "10/01/23 11:00:00",
                           "name": "laji1", "duration": 100, "user_id": 1}
        entry = Exercise(name=excercise_entry.get("name"), duration="asd",
            date=datetime.strptime(excercise_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=excercise_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Exercise(name=excercise_entry.get("name"), duration=excercise_entry.get(
            "duration"), date="asd", user_id=excercise_entry.get("user_id"))
        assert insert_illegal(entry)

        # Measurement
        measurement_entry = {"date": "01/01/23 01:00:00", "weight": 10.1,
                             "calories_in": 1000, "calories_out": 100, "user_id": 1}
        entry = Measurements(weight=measurement_entry.get("weight"),
            calories_in=measurement_entry.get("calories_in"),
            calories_out=measurement_entry.get("calories_out"),
            date="asd", user_id=measurement_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Measurements(weight="asd", calories_in=measurement_entry.get("calories_in"),
            calories_out=measurement_entry.get("calories_out"),
            date=datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=measurement_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Measurements(weight=measurement_entry.get("weight"), calories_in="asd",
            calories_out=measurement_entry.get("calories_out"),
            date=datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=measurement_entry.get("user_id"))
        assert insert_illegal(entry)
        entry = Measurements(weight=measurement_entry.get("weight"),
            calories_in=measurement_entry.get("calories_in"), calories_out="asd",
            date=datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"),
            user_id=measurement_entry.get("user_id"))
        assert insert_illegal(entry)
