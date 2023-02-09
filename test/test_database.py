
from database.models import Exercise, User, Measurements, create_test_app
import tools.populate_database
import datetime
import json
import pathlib
import time


def insert_with_null(db, entry):
    try:
        db.session.add(entry)
        db.session.commit()
        return False
    except Exception:
        db.session.rollback()
        return True
        

def test_database_models():
    app, db = create_test_app()
    db.create_all()

    tools.populate_database.populate_database(db, app)
    with open(pathlib.Path(__file__).parent.parent.joinpath("tools", "dummy_data.json")) as f:
        dummy_data = json.load(f)

    #Check that all expected data is in db
    user_data = User.query.all()
    expected_user_data = dummy_data.get("Users")
    i = 0
    for user in user_data:
        assert user.name == expected_user_data[i].get("name")
        assert user.email == expected_user_data[i].get("email")
        assert user.age == expected_user_data[i].get("age")
        assert user.user_creation_date == datetime.datetime.strptime(expected_user_data[i].get("date"), '%d/%m/%y %H:%M:%S')
        i += 1
    measurement_data = Measurements.query.all()
    expected_measurement_data = dummy_data.get("Measurements")
    i = 0
    for meas in measurement_data:
        assert meas.date == datetime.datetime.strptime(expected_measurement_data[i].get("date"), '%d/%m/%y %H:%M:%S')
        assert meas.weight == expected_measurement_data[i].get("weight")
        assert meas.calories_in == expected_measurement_data[i].get("calories_in")
        assert meas.calories_out == expected_measurement_data[i].get("calories_out")
        assert meas.user_id == expected_measurement_data[i].get("user_id")
        i += 1
    exercise_data = Exercise.query.all()
    expected_excercise_data = dummy_data.get("Exercise_record")
    i = 0
    for exercise in exercise_data:
        assert exercise.name == expected_excercise_data[i].get("name")
        assert exercise.duration == expected_excercise_data[i].get("duration")
        assert exercise.date == datetime.datetime.strptime(expected_excercise_data[i].get("date"), '%d/%m/%y %H:%M:%S')
        assert exercise.user_id == expected_excercise_data[i].get("user_id")
        i += 1

    #Check exercise - user linkage ("laji4" should be linked to user id 2)
    test_exercise_record = Exercise.query.filter_by(name="laji4").all()[0]
    assert test_exercise_record.user == User.query.filter_by(id=2)[0]

    #Check measurement - user linkage (meas 13 should be linked to user id 9)
    test_measurement_record = Measurements.query.filter_by(weight=500.5).all()[0]
    assert test_measurement_record.user == User.query.filter_by(id=9)[0]

    #Check user - exercise linkage (user id 8 should have laji15 and laji19, user id 9 should not have any)
    test_user_record = User.query.filter_by(id=8)[0]
    assert test_user_record.exercise == [Exercise.query.filter_by(name="laji15").all()[0], Exercise.query.filter_by(name="laji16").all()[0]]
    test_user_record = User.query.filter_by(id=9)[0]
    assert test_user_record.exercise == []

    #Check user - measurement linkage (user id 3 should have 2 records, id 1 none)
    test_user_record = User.query.filter_by(id=3)[0]
    assert test_user_record.measurements == [Measurements.query.filter_by(calories_in=1000).all()[0], Measurements.query.filter_by(calories_in=1100).all()[0]]
    test_user_record = User.query.filter_by(id=1)[0]
    assert test_user_record.measurements == []
    
    db.drop_all()


def test_ondeletes():
    app, db = create_test_app()
    db.create_all()

    tools.populate_database.populate_database(db, app)

    #Check that Measurements and Excercies are correctly linked to userid 3
    for entry in Measurements.query.filter_by(user_id=3).all():
        assert entry.user.name == "name3"
        assert entry.user.email == "some3@email.com"
        assert entry.user.age == 23
        assert entry.user.user_creation_date == datetime.datetime.strptime("03/01/23 03:00:00", "%d/%m/%y %H:%M:%S")
    for entry in Exercise.query.filter_by(user_id=3).all():
        assert entry.user.name == "name3"
        assert entry.user.email == "some3@email.com"
        assert entry.user.age == 23
        assert entry.user.user_creation_date == datetime.datetime.strptime("03/01/23 03:00:00", "%d/%m/%y %H:%M:%S")

    #Delete User 3
    User.query.filter_by(id=3).delete()
    db.session.commit()
    
    #All references to user 3 should be nulled
    for entry in Exercise.query.filter_by(user_id=3).all():
        assert entry.user == None
    for entry in Exercise.query.filter_by(user_id=3).all():
        assert entry.user == None

    db.drop_all()


def test_nullability():
    app, db = create_test_app()
    db.create_all()

    #Test User
    user_entry = {"date": "01/01/23 01:00:00", "name": "name1", "email": "some1@email.com", "age": 21}
    entry = User(name=None, email=user_entry.get("email"), age=user_entry.get("age"), user_creation_date=datetime.datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
    assert insert_with_null(db, entry)
    entry = User(name=user_entry.get("name"), email=None, age=user_entry.get("age"), user_creation_date=datetime.datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
    assert insert_with_null(db, entry)
    entry = User(name=user_entry.get("name"), email=user_entry.get("email"), age=None, user_creation_date=datetime.datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
    assert insert_with_null(db, entry)
    entry = User(name=user_entry.get("name"), email=user_entry.get("email"), age=user_entry.get("age"), user_creation_date=None)
    assert insert_with_null(db, entry)

    #Create a valid user to use with excercise/measurements
    entry = User(name=user_entry.get("name"), email=user_entry.get("email"), age=user_entry.get("age"), user_creation_date=datetime.datetime.strptime(user_entry.get("date"), "%d/%m/%y %H:%M:%S"))
    db.session.add(entry)
    db.session.commit()

    #Test Measurement
    measurement_entry = {"date":"01/01/23 01:00:00", "weight": 10.1, "calories_in": 1000, "calories_out": 100, "user_id": 1}
    entry = Measurements(weight=None, calories_in=measurement_entry.get("calories_in"), calories_out=measurement_entry.get("calories_out"), date=datetime.datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"), user_id=measurement_entry.get("user_id"))
    assert insert_with_null(db, entry)
    entry = Measurements(weight=measurement_entry.get("weight"), calories_in=None, calories_out=measurement_entry.get("calories_out"), date=datetime.datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"), user_id=measurement_entry.get("user_id"))
    assert insert_with_null(db, entry)
    entry = Measurements(weight=measurement_entry.get("weight"), calories_in=measurement_entry.get("calories_in"), calories_out=None, date=datetime.datetime.strptime(measurement_entry.get("date"), "%d/%m/%y %H:%M:%S"), user_id=measurement_entry.get("user_id"))
    assert insert_with_null(db, entry)
    entry = Measurements(weight=measurement_entry.get("weight"), calories_in=measurement_entry.get("calories_in"), calories_out=measurement_entry.get("calories_out"), date=None, user_id=measurement_entry.get("user_id"))
    assert insert_with_null(db, entry)

    #Test Excercise
    excercise_entry = {"date": "10/01/23 11:00:00", "name": "laji1", "duration": 100, "user_id": 1}
    entry = Exercise(name=None, duration=excercise_entry.get("duration"), date=datetime.datetime.strptime(excercise_entry.get("date"), "%d/%m/%y %H:%M:%S"), user_id=excercise_entry.get("user_id"))
    assert insert_with_null(db, entry)
    entry = Exercise(name=excercise_entry.get("name"), duration=None, date=datetime.datetime.strptime(excercise_entry.get("date"), "%d/%m/%y %H:%M:%S"), user_id=excercise_entry.get("user_id"))
    assert insert_with_null(db, entry)
    entry = Exercise(name=excercise_entry.get("name"), duration=excercise_entry.get("duration"), date=None, user_id=excercise_entry.get("user_id"))
    assert insert_with_null(db, entry)
    
    db.drop_all()
