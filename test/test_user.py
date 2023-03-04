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

def get_user_dummy_data():
    ddata_path = os.path.join(os.path.dirname(__file__), "..", "tools", "dummy_data.json")
    with open(ddata_path) as f:
        cont = json.load(f)
    cont = cont["Users"]
    res = []
    for item in cont:
        #convert timestamp to format in reponse (iso format) and duration to float and use "user_creation_date" instead of "date"
        item["user_creation_date"] = datetime.isoformat(datetime.strptime(item['date'], '%d/%m/%y %H:%M:%S'))
        del item["date"]
        item["age"] = float(item["age"])
        res.append(item)
    return res

def test_UserCollection_post(client):
    RESOURCE_URL_VALID = "/api/users/"
    RESOURCE_URL_INVALID = "/api/ubers/"
    VALID_USER = {
        "name": "niilo",
        "email": "example@com",
        "age": 22,
        "user_creation_date": datetime.isoformat(datetime.now()),
    }
    INVALID_USER = {
        "thisis": "nuulo",
        "asd": 22
    }

    #Valid exercise to valid user (also check that can be get)
    resp = client.post(RESOURCE_URL_VALID, json=VALID_USER)
    assert resp.status_code == 201
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    #check that last user is the one we just added
    res = json.loads(resp.data).get("users")
    assert res[len(res)-1] == VALID_USER
    
    #Invalid data to valid url
    resp = client.post(RESOURCE_URL_VALID, json=INVALID_USER)
    assert resp.status_code == 400

    #Valid data to invalid url
    resp = client.post(RESOURCE_URL_INVALID, json=VALID_USER)
    assert resp.status_code == 404
    
    #Invalid data to invalid url
    resp = client.post(RESOURCE_URL_INVALID, json=INVALID_USER)
    assert resp.status_code == 404

def test_UserCollection_get(client):
    RESOURCE_URL_VALID = "/api/users/"
    RESOURCE_URL_INVALID = "/api/ubers/"

    #Get from valid url
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    cont = json.loads(resp.data)["users"]
    excepted = get_user_dummy_data()
    print("EX",excepted)
    print("GOT:", cont)
    for item in cont:
        assert item in excepted

    #Get from invalid url
    resp = client.get(RESOURCE_URL_INVALID)
    assert resp.status_code == 404

def test_UserItem_get(client):
    RESOURCE_URL_VALID = "/api/users/1/"
    RESOURCE_URL_NOT_EXIST = "/api/users/999/"

    #Get user from valid url
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 200
    res = json.loads(resp.data)
    expected = get_user_dummy_data()
    assert res==expected[0]

    #Get not existing user
    resp = client.get(RESOURCE_URL_NOT_EXIST)
    assert resp.status_code == 404
    

def test_UserItem_put(client):
    RESOURCE_URL_VALID = "/api/users/1/"
    RESOURCE_URL_NOT_EXIST = "/api/users/999/"
    UPDATED_USER = {
        "name": "niilo",
        "email": "example@com",
        "age": 22,
        "user_creation_date": datetime.isoformat(datetime.now()),
    }
    #Put updated user
    resp = client.put(RESOURCE_URL_VALID, json=UPDATED_USER)
    assert resp.status_code == 204
    #get updated user and check that it matches
    resp = client.get(RESOURCE_URL_VALID)
    res = json.loads(resp.data)
    assert res == UPDATED_USER
    
    #Put on not existing user
    resp = client.put(RESOURCE_URL_NOT_EXIST, json=UPDATED_USER)
    assert resp.status_code == 404


def test_UserItem_del(client):
    RESOURCE_URL_VALID = "/api/users/1/"
    RESOURCE_URL_NOT_EXIST = "/api/users/999/"

    #Delete existing user
    resp = client.delete(RESOURCE_URL_VALID)
    assert resp.status_code == 204
    #Check that this user can't be found anymore
    resp = client.get(RESOURCE_URL_VALID)
    assert resp.status_code == 404

    #Try to delete not existing user
    resp = client.delete(RESOURCE_URL_NOT_EXIST)
    assert resp.status_code == 404
