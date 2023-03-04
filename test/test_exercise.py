


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
    cont = cont["Exercise_record"] #Only interested in exercise records
    res = []
    for item in cont:
        if item.get("user_id") == id:
            #convert timestamp to format in reponse (iso format) and duration to float
            item["date"] = datetime.isoformat(datetime.strptime(item['date'], '%d/%m/%y %H:%M:%S'))
            item["duration"] = float(item["duration"])
            res.append(item)
    return res


def test_ExerciseCollection_get(client):
    RESOURCE_URL_VALID = "/api/users/1/exercises/"
    RESOURCE_URL_INVALID = "/api/users/11/exercises/"

    #Get from existing user
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    cont = json.loads(resp.data)
    excepted = get_dummy_data_by_userid(1)
    cont = cont["exercises"]
    for item in cont:
        del item["id"] #dummy data has no id as it is just the primary key in db
        assert item in excepted

    #Get from nonexisting user
    resp = client.get(RESOURCE_URL_INVALID)
    assert resp.status_code == 404


def test_ExerciseCollection_post(client):
    RESOURCE_URL_VALID = "/api/users/1/exercises/"
    RESOURCE_URL_INVALID = "/api/users/11/exercises/"
    VALID_EXERCISE = {
        "name": "laji",
        "date": datetime.isoformat(datetime.now()),
        "user_id": 1,
        "duration": 12.12
    }
    INVALID_EXERCISE = {
        "thisis": "invalid",
        "asd": 1
    }

    #Valid exercise to valid user (also check that can be get)
    resp = client.post(RESOURCE_URL_VALID, json=VALID_EXERCISE)
    assert resp.status_code == 201
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    res = json.loads(resp.data).get("exercises")[2]
    del res["id"] #id is just the primary key
    assert res == VALID_EXERCISE
    
    #Invalid exercise to valid user
    resp = client.post(RESOURCE_URL_VALID, json=INVALID_EXERCISE)
    assert resp.status_code == 400

    #Valid exercise to invalid user
    resp = client.post(RESOURCE_URL_INVALID, json=VALID_EXERCISE)
    assert resp.status_code == 404
    
    #Invalid exercise to invalid user
    resp = client.post(RESOURCE_URL_INVALID, json=INVALID_EXERCISE)
    assert resp.status_code == 404


def test_ExerciseItem_get(client):
    RESOURCE_URL_VALID = "/api/users/1/exercises/1/"
    RESOURCE_URL_VALID_WRONG_USER = "/api/users/1/exercises/5/"
    RESOURCE_URL_VALID_INVALID_USER = "/api/users/11/exercises/0/"

    #Get exercise record corresponding to user
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    res = json.loads(resp.data)
    del res["id"]
    excepted = get_dummy_data_by_userid(1)
    assert res == excepted[0]

    #Get existing exercise but corresponding to wrong user
    resp = client.get(RESOURCE_URL_VALID_WRONG_USER)
    assert resp.status_code == 400

    #Get existing exerciose but corresponding to non-existing user
    resp = client.get(RESOURCE_URL_VALID_INVALID_USER)
    assert resp.status_code == 404
    

def test_ExerciseItem_put(client):
    RESOURCE_URL_VALID = "/api/users/1/exercises/1/"
    RESOURCE_URL_VALID_WRONG_USER = "/api/users/2/exercises/1/"
    RESOURCE_URL_INVALID = "/api/users/1/exercises/100/"
    UPDATED_EXERCISE = {
        "date": datetime.isoformat(datetime.now()), 
        "name": "updated_laji1", 
        "duration": 123321.0, 
        "user_id": 1
    }

    #Update record
    resp = client.put(RESOURCE_URL_VALID, json=UPDATED_EXERCISE)
    assert resp.status_code == 201
    resp = client.get(RESOURCE_URL_VALID)
    res = json.loads(resp.data)
    del res["id"]
    assert res == UPDATED_EXERCISE
    
    #Update record with user_id mismatch
    resp = client.put(RESOURCE_URL_VALID_WRONG_USER, json=UPDATED_EXERCISE)
    assert resp.status_code == 400
    
    #Update nonexisting record
    resp = client.put(RESOURCE_URL_INVALID, json=UPDATED_EXERCISE)
    assert resp.status_code == 404


def test_ExerciseItem_delete(client):
    RESOURCE_URL_VALID = "/api/users/1/exercises/1/"
    RESOURCE_URL_VALID_WRONG_USER = "/api/users/2/exercises/1/"
    RESOURCE_URL_INVALID = "/api/users/1/exercises/100/"

    #Delete existing record (and verify deletion)
    resp = client.delete(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 404

    #Try deleting from another user (should not be found)
    resp = client.delete(RESOURCE_URL_VALID_WRONG_USER)
    assert resp.status_code == 404

    #Try deleting nonexisting record
    resp = client.delete(RESOURCE_URL_INVALID)
    assert resp.status_code == 404
