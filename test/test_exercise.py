"""
Tests for exercise resources
"""

from datetime import datetime
import json
import tempfile
import os
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy import event
import tools.populate_database
from fitnessbuddy import create_app, db



@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Important
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on https://github.com/enkwolf/pwp-course-sensorhub-api-example
@pytest.fixture
def client():
    """
    Test client
    """
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

def get_dummy_data_by_userid(user_id):
    """
    Get data from dummy_data.json based on user id
    """
    ddata_path = os.path.join(os.path.dirname(__file__), "..", "tools", "dummy_data.json")
    with open(ddata_path, encoding="utf-8") as file:
        cont = json.load(file)
    cont = cont["Exercise_record"] #Only interested in exercise records
    res = []
    for item in cont:
        if item.get("user_id") == user_id:
            #convert timestamp to format in reponse (iso format) and duration to float
            item["date"] = datetime.isoformat(datetime.strptime(item['date'], '%d/%m/%y %H:%M:%S'))
            item["duration"] = float(item["duration"])
            res.append(item)
    return res


def test_ExerciseCollection_get(client):
    """
    Test get method of ExerciseCollection
    """
    resource_url_valid = "/api/users/1/exercises/"
    resource_url_invalid = "/api/users/11/exercises/"

    #Get from existing user
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    cont = json.loads(resp.data)
    excepted = get_dummy_data_by_userid(1)
    cont = cont["exercises"]
    for item in cont:
        del item["id"] #dummy data has no id as it is just the primary key in db
        assert item in excepted

    #Get from nonexisting user
    resp = client.get(resource_url_invalid)
    assert resp.status_code == 404


def test_ExerciseCollection_post(client):
    """
    Test post method of ExerciseCollection
    """
    resource_url_valid = "/api/users/1/exercises/"
    resource_url_invalid = "/api/users/11/exercises/"
    valid_exercise = {
        "name": "laji",
        "date": datetime.isoformat(datetime.now()),
        "user_id": 1,
        "duration": 12.12
    }
    invalid_exercise = {
        "thisis": "invalid",
        "asd": 1
    }

    #Valid exercise to valid user (also check that can be get)
    resp = client.post(resource_url_valid, json=valid_exercise)
    assert resp.status_code == 201
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    res = json.loads(resp.data).get("exercises")[2]
    del res["id"] #id is just the primary key
    assert res == valid_exercise

    #Invalid exercise to valid user
    resp = client.post(resource_url_valid, json=invalid_exercise)
    assert resp.status_code == 400

    #Valid exercise to invalid user
    resp = client.post(resource_url_invalid, json=valid_exercise)
    assert resp.status_code == 404

    #Invalid exercise to invalid user
    resp = client.post(resource_url_invalid, json=invalid_exercise)
    assert resp.status_code == 404


def test_ExerciseItem_get(client):
    """
    Test get method of ExerciseItem
    """
    resource_url_valid = "/api/users/1/exercises/1/"
    resource_url_valid_wrong_user = "/api/users/1/exercises/5/"
    resource_url_valid_invalid_user = "/api/users/11/exercises/0/"

    #Get exercise record corresponding to user
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    res = json.loads(resp.data)
    del res["id"]
    excepted = get_dummy_data_by_userid(1)
    assert res == excepted[0]

    #Get existing exercise but corresponding to wrong user
    resp = client.get(resource_url_valid_wrong_user)
    assert resp.status_code == 400

    #Get existing exerciose but corresponding to non-existing user
    resp = client.get(resource_url_valid_invalid_user)
    assert resp.status_code == 404


def test_ExerciseItem_put(client):
    """
    Test put method of ExerciseItem
    """
    resource_url_valid = "/api/users/1/exercises/1/"
    resource_url_valid_wrong_user = "/api/users/2/exercises/1/"
    resource_url_invalid = "/api/users/1/exercises/100/"
    updated_exercise = {
        "date": datetime.isoformat(datetime.now()),
        "name": "updated_laji1",
        "duration": 123321.0,
        "user_id": 1
    }

    #Update record
    resp = client.put(resource_url_valid, json=updated_exercise)
    assert resp.status_code == 201
    resp = client.get(resource_url_valid)
    res = json.loads(resp.data)
    del res["id"]
    assert res == updated_exercise

    #Update record with user_id mismatch
    resp = client.put(resource_url_valid_wrong_user, json=updated_exercise)
    assert resp.status_code == 400

    #Update nonexisting record
    resp = client.put(resource_url_invalid, json=updated_exercise)
    assert resp.status_code == 404


def test_ExerciseItem_delete(client):
    """
    Test delete method of ExerciseItem
    """
    resource_url_valid = "/api/users/1/exercises/1/"
    resource_url_valid_wrong_user = "/api/users/2/exercises/1/"
    resource_url_invalid = "/api/users/1/exercises/100/"

    #Delete existing record (and verify deletion)
    resp = client.delete(resource_url_valid)
    assert resp.status_code == 200
    resp = client.get(resource_url_valid)
    assert resp.status_code == 404

    #Try deleting from another user (should not be found)
    resp = client.delete(resource_url_valid_wrong_user)
    assert resp.status_code == 404

    #Try deleting nonexisting record
    resp = client.delete(resource_url_invalid)
    assert resp.status_code == 404
