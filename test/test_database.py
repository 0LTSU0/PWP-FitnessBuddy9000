
from database.models import Exercise, User, Measurements, create_test_app
import tools.populate_database
import datetime
import json
import pathlib


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
