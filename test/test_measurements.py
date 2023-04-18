"""
Tests for measurement resources
"""

import json
import tempfile
import os
from datetime import datetime
import pytest
from fitnessbuddy.models import Exercise, User, Measurements
from fitnessbuddy import create_app, db
from sqlalchemy.engine import Engine
from sqlalchemy import event
import tools.populate_database

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

measurement_schema = {'type': 'object', 'required': ['date', 'user_id'], 'properties': {
    'date': {'description': 'Datetime of the measurement as a string', 'type': 'string'}, 
    'user_id': {'description': 'User id', 'type': 'number'}, 
    'weight': {'description': 'Weight measurement', 'type': 'number'}, 
    'calories_in': {'description': 'Calories eaten', 'type': 'number'}, 
    'calories_out': {'description': 'Calories burnt', 'type': 'number'}}}

# based on https://github.com/enkwolf/pwp-course-sensorhub-api-example
@pytest.fixture
def client():
    """
    Test client
    """
    
    tempfile.tempdir = os.path.dirname(__file__)
    db_fd, db_fname = tempfile.mkstemp(prefix="temppytest_")
    config = {"SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname, "TESTING": True}

    app = create_app(config)

    with app.app_context():
        db.create_all()
        tools.populate_database.populate_database(db, app)

    yield app.test_client()

    os.close(db_fd)
    # os.unlink(db_fname)


def get_dummy_data_by_userid(user_id):
    """
    Get data from dummy_data.json based on user_id
    """
    ddata_path = os.path.join(
        os.path.dirname(__file__), "..", "tools", "dummy_data.json"
    )
    with open(ddata_path, encoding="utf-8") as file:
        cont = json.load(file)
    cont = cont["Measurements"]  # Only interested in exercise records
    res = []
    for item in cont:
        if item.get("user_id") == user_id:
            # convert timestamp to format in reponse (iso format) and duration to float
            item["date"] = datetime.isoformat(
                datetime.strptime(item["date"], "%d/%m/%y %H:%M:%S")
            )
            item["weight"] = float(item["weight"])
            item["calories_in"] = float(item["calories_in"])
            item["calories_out"] = float(item["calories_out"])
            res.append(item)
    return res


def test_MeasurementsCollection_get(client):
    """
    Test get method of MeasurementCollection
    """
    resource_url_valid = "/api/users/1/measurements/"
    resource_url_invalid = "/api/users/12/measurements/"

    # Get from existing user
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    cont = json.loads(resp.data)
    excepted = get_dummy_data_by_userid(1)
    cont = cont["measurements"]
    for item in cont:
        del item["id"]  # dummy data has no id as it is just the primary key in db
        assert item in excepted

    #Verify controls
    controls = json.loads(resp.data)["@controls"]
    expected = {'self': {'href': '/api/users/1/measurements/'}, 
                'fitnessbuddy:user': {'href': '/api/users/1/'}, 
                'fitnessbuddy:add-measurement': {'method': 'POST', 'encoding': 'json', 'title': 'fitnessbuddy:addmeasurement', 'schema': measurement_schema, 'href': '/api/users/1/measurements/'}}
    assert controls == expected

    # Get from nonexisting user
    resp = client.get(resource_url_invalid)
    assert resp.status_code == 404


def test_MeasurementsCollection_post(client):
    """
    Test post method of MeasurementCollection
    """
    resource_url_valid = "/api/users/1/measurements/"
    resource_url_invalid = "/api/users/12/measurements/"
    valid_measurement = {
        "date": "2023-02-11T13:01:56",
        "weight": 100,
        "calories_in": 2500,
        "calories_out": 2500,
        "user_id": 1,
    }
    invalid_measurement = {"thisis": "invalid", "asd": 1}

    invalid_measurement1 = {
        "date": "2023-02-11T13:01:56",
        "weight": "123",
        "calories_in": 2500,
        "calories_out": 2500,
        "user_id": 1,
    }
    invalid_measurement2 = {
        "date": "2023-02-11T13:01:56",
        "weight": 100,
        "calories_in": "123",
        "calories_out": 2500,
        "user_id": 1,
    }
    invalid_measurement3 = {
        "date": "2023-02-11T13:01:56",
        "weight": 100,
        "calories_in": 2500,
        "calories_out": "123",
        "user_id": 1,
    }

    # Valid exercise to valid user (also check that can be get)
    resp = client.post(resource_url_valid, json=valid_measurement)
    assert resp.status_code == 201
    #Verify controls
    controls = json.loads(resp.data)["@controls"]
    expected = {'self': {'href': '/api/users/1/measurements/17/'}}
    assert controls == expected
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    res = json.loads(resp.data).get("measurements")[0]
    del res["id"]  # id is just the primary key
    assert res == valid_measurement

    # Invalid measurement to valid user
    resp = client.post(resource_url_valid, json=invalid_measurement)
    assert resp.status_code == 400

    resp = client.post(resource_url_valid, json=invalid_measurement1)
    assert resp.status_code == 400

    resp = client.post(resource_url_valid, json=invalid_measurement2)
    assert resp.status_code == 400

    resp = client.post(resource_url_valid, json=invalid_measurement3)
    assert resp.status_code == 400

    # Valid exercise to invalid user
    resp = client.post(resource_url_invalid, json=invalid_measurement)
    assert resp.status_code == 404

    # Invalid exercise to invalid user
    resp = client.post(resource_url_invalid, json=invalid_measurement)
    assert resp.status_code == 404

    #no json
    resp = client.post(resource_url_valid, data="asd")
    assert resp.status_code == 415


def test_MeasurementsItem_get(client):
    """
    Test get method of MeasurementItem
    """
    resource_url_valid = "/api/users/3/measurements/1/"
    resource_url_valid_wrong_user = "/api/users/1/measurements/5/"
    resource_url_valid_invalid_user = "/api/users/11/measurements/0/"

    # Get measurment record corresponding to user
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    res = json.loads(resp.data)["measurement"]
    del res["id"]
    excepted = get_dummy_data_by_userid(3)
    assert res == excepted[0]

    #Verify controls
    controls = json.loads(resp.data)["@controls"]
    expected = {'self': {'href': '/api/users/3/measurements/1/'}, 
                'fitnessbuddy:measurements-all': {'title': 'All measurements', 'href': '/api/users/3/measurements/'}, 
                'fitnessbuddy:delete': {'method': 'DELETE', 'title': 'Delete measurements', 'href': '/api/users/3/measurements/1/'}, 
                'edit': {'method': 'PUT', 'encoding': 'json', 'title': 'Edit measurements', 'schema': measurement_schema, 'href': '/api/users/3/measurements/1/'}}
    assert controls == expected

    # Get existing measurement but corresponding to wrong user
    resp = client.get(resource_url_valid_wrong_user)
    assert resp.status_code == 400

    # Get existing exerciose but corresponding to non-existing user
    resp = client.get(resource_url_valid_invalid_user)
    assert resp.status_code == 404


def test_MeasurementsItem_put(client):
    """
    Test put method of MeasurementItem
    """
    resource_url_valid = "/api/users/3/measurements/1/"
    resource_url_valid_wrong_user = "/api/users/1/measurements/1/"
    resource_url_invalid = "/api/users/1/measurements/100/"
    updated_measurement = {
        "date": datetime.isoformat(datetime.now()),
        "weight": 80,
        "calories_in": 2000,
        "calories_out": 2500,
        "user_id": 3,
    }
    invalid_json = {
        "user_id": 1,
        "thisis": "invalid"
    }

    # Update record
    resp = client.put(resource_url_valid, json=updated_measurement)
    assert resp.status_code == 204
    resp = client.get(resource_url_valid)
    print(resp.data)
    res = json.loads(resp.data)["measurement"]
    print(res)
    del res["id"]
    assert res == updated_measurement

    # Update record with user_id mismatch
    resp = client.put(resource_url_valid_wrong_user, json=updated_measurement)
    assert resp.status_code == 400

    # Update nonexisting record
    resp = client.put(resource_url_invalid, json=updated_measurement)
    assert resp.status_code == 404

    #Non json
    resp = client.put(resource_url_valid, data="asd")
    assert resp.status_code == 415

    #invalid json
    resp = client.put(resource_url_valid, json=invalid_json)
    assert resp.status_code == 400


def test_MeasurementsItem_delete(client):
    """
    Test delete method of MeasurementItem
    """
    resource_url_valid = "/api/users/3/measurements/1/"
    resource_url_valid_wrong_user = "/api/users/2/measurements/1/"
    resource_url_invalid = "/api/users/1/measurements/100/"

    # Delete existing record (and verify deletion)
    resp = client.delete(resource_url_valid)
    assert resp.status_code == 204
    resp = client.get(resource_url_valid)
    assert resp.status_code == 404

    # Try deleting from another user (should not be found)
    resp = client.delete(resource_url_valid_wrong_user)
    assert resp.status_code == 404

    # Try deleting nonexisting record
    resp = client.delete(resource_url_invalid)
    assert resp.status_code == 404
