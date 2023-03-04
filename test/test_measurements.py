from fitnessbuddy.models import Exercise, User, Measurements
from fitnessbuddy import create_app, db
from sqlalchemy.engine import Engine
from sqlalchemy import event
import tools.populate_database
from datetime import datetime
import json
import pathlib
import tempfile
import os
import pytest


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    tempfile.tempdir = os.path.dirname(__file__)
    db_fd, db_fname = tempfile.mkstemp(prefix="temppytest_")
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        tools.populate_database.populate_database(db, app)
        
    yield app.test_client()
    
    os.close(db_fd)
    #os.unlink(db_fname)

def get_dummy_data_by_userid(id):
    ddata_path = os.path.join(os.path.dirname(__file__), "..", "tools", "dummy_data.json")
    with open(ddata_path) as f:
        cont = json.load(f)
    cont = cont["Measurements"] #Only interested in exercise records
    res = []
    for item in cont:
        if item.get("user_id") == id:
            #convert timestamp to format in reponse (iso format) and duration to float
            item["date"] = datetime.isoformat(datetime.strptime(item['date'], '%d/%m/%y %H:%M:%S'))
            item["weight"] = float(item["weight"])
            item["calories_in"] = float(item["calories_in"])
            item["calories_out"]= float(item["calories_out"])
            res.append(item)
    return res


def test_MeasurementsCollection_get(client):
    RESOURCE_URL_VALID = "/api/users/1/measurements/"
    RESOURCE_URL_INVALID = "/api/users/12/measurements/"

    #Get from existing user
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    cont = json.loads(resp.data)
    excepted = get_dummy_data_by_userid(1)
    cont = cont["measurements"]
    for item in cont:
        del item["id"] #dummy data has no id as it is just the primary key in db
        assert item in excepted

    #Get from nonexisting user
    resp = client.get(RESOURCE_URL_INVALID)
    assert resp.status_code == 404


def test_MeasurementsCollection_post(client):
    RESOURCE_URL_VALID = "/api/users/1/measurements/"
    RESOURCE_URL_INVALID = "/api/users/12/measurements/"
    VALID_MEASUREMENT = {
    "date": "2023-02-11T13:01:56",
    "weight": 100,
    "calories_in": 2500,
    "calories_out": 2500,
    "user_id": 1
    }
    INVALID_MEASUREMENT = {
        "thisis": "invalid",
        "asd": 1
    }

    INVALID_MEASUREMENT1 = {
    "date": "2023-02-11T13:01:56",
    "weight": "123",
    "calories_in": 2500,
    "calories_out": 2500,
    "user_id": 1
    }
    INVALID_MEASUREMENT2 = {
    "date": "2023-02-11T13:01:56",
    "weight": 100,
    "calories_in": "123",
    "calories_out": 2500,
    "user_id": 1
    }
    INVALID_MEASUREMENT3 = {
    "date": "2023-02-11T13:01:56",
    "weight": 100,
    "calories_in": 2500,
    "calories_out": "123",
    "user_id": 1
    }

    #Valid exercise to valid user (also check that can be get)
    resp = client.post(RESOURCE_URL_VALID, json=VALID_MEASUREMENT)
    assert resp.status_code == 201
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    res = json.loads(resp.data).get("measurements")[0]
    del res["id"] #id is just the primary key
    assert res == VALID_MEASUREMENT
    
    #Invalid measurement to valid user
    resp = client.post(RESOURCE_URL_VALID, json=INVALID_MEASUREMENT)
    assert resp.status_code == 400

    resp = client.post(RESOURCE_URL_VALID, json=INVALID_MEASUREMENT1)
    assert resp.status_code == 400

    resp = client.post(RESOURCE_URL_VALID, json=INVALID_MEASUREMENT2)
    assert resp.status_code == 400

    resp = client.post(RESOURCE_URL_VALID, json=INVALID_MEASUREMENT3)
    assert resp.status_code == 400

    #Valid exercise to invalid user
    resp = client.post(RESOURCE_URL_INVALID, json=INVALID_MEASUREMENT)
    assert resp.status_code == 404
    
    #Invalid exercise to invalid user
    resp = client.post(RESOURCE_URL_INVALID, json=INVALID_MEASUREMENT)
    assert resp.status_code == 404


def test_MeasurementsItem_get(client):
    RESOURCE_URL_VALID = "/api/users/3/measurements/1/"
    RESOURCE_URL_VALID_WRONG_USER = "/api/users/1/measurements/5/"
    RESOURCE_URL_VALID_INVALID_USER = "/api/users/11/measurements/0/"

    #Get measurment record corresponding to user
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    res = json.loads(resp.data)
    del res["id"]
    excepted = get_dummy_data_by_userid(3)
    assert res == excepted[0]

    #Get existing exercise but corresponding to wrong user
    resp = client.get(RESOURCE_URL_VALID_WRONG_USER)
    assert resp.status_code == 400

    #Get existing exerciose but corresponding to non-existing user
    resp = client.get(RESOURCE_URL_VALID_INVALID_USER)
    assert resp.status_code == 404
    

def test_MeasurementsItem_put(client):
    RESOURCE_URL_VALID = "/api/users/3/measurements/1/"
    RESOURCE_URL_VALID_WRONG_USER = "/api/users/1/measurements/1/"
    RESOURCE_URL_INVALID = "/api/users/1/measurements/100/"
    UPDATED_MEASUREMENT = {
        "date": datetime.isoformat(datetime.now()), 
        "weight": 80, 
        "calories_in": 2000,
        "calories_out": 2500,
        "user_id": 3
    }

    #Update record
    resp = client.put(RESOURCE_URL_VALID, json=UPDATED_MEASUREMENT)
    assert resp.status_code == 204
    resp = client.get(RESOURCE_URL_VALID)
    print(resp.data)
    res = json.loads(resp.data)
    print(res)
    del res["id"]
    assert res == UPDATED_MEASUREMENT

    
    #Update record with user_id mismatch
    resp = client.put(RESOURCE_URL_VALID_WRONG_USER, json=UPDATED_MEASUREMENT)
    assert resp.status_code == 400
    
    #Update nonexisting record
    resp = client.put(RESOURCE_URL_INVALID, json=UPDATED_MEASUREMENT)
    assert resp.status_code == 404


def test_MeasurementsItem_delete(client):
    RESOURCE_URL_VALID = "/api/users/3/measurements/1/"
    RESOURCE_URL_VALID_WRONG_USER = "/api/users/2/measurements/1/"
    RESOURCE_URL_INVALID = "/api/users/1/measurements/100/"

    #Delete existing record (and verify deletion)
    resp = client.delete(RESOURCE_URL_VALID)
    assert resp.status_code == 204
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 404

    #Try deleting from another user (should not be found)
    resp = client.delete(RESOURCE_URL_VALID_WRONG_USER)
    assert resp.status_code == 404

    #Try deleting nonexisting record
    resp = client.delete(RESOURCE_URL_INVALID)
    assert resp.status_code == 404
