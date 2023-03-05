"""
Module for testing user resource
"""
import json
import tempfile
import os
from datetime import datetime
from fitnessbuddy import create_app, db
from sqlalchemy.engine import Engine
from sqlalchemy import event
import tools.populate_database
import pytest

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    This is important function
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on https://github.com/enkwolf/pwp-course-sensorhub-api-example
@pytest.fixture
def client():
    """
    Initialize client for testing purposes
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

def get_user_dummy_data():
    """
    Function for retrieving user data from dummy_data.json file
    """
    ddata_path = os.path.join(os.path.dirname(__file__), "..", "tools", "dummy_data.json")
    with open(ddata_path) as tmp_file:
        cont = json.load(tmp_file)
    cont = cont["Users"]
    res = []
    for item in cont:
        #convert timestamp to format in reponse (iso format) and duration to float
        #use "user_creation_date" instead of "date"
        item["user_creation_date"] = datetime.isoformat(
            datetime.strptime(item['date'], '%d/%m/%y %H:%M:%S'))
        del item["date"]
        item["age"] = float(item["age"])
        res.append(item)
    return res

def test_usercollection_post(client):
    """
    Function for testing post method on UserCollection resource
    """
    resource_url_valid = "/api/users/"
    resource_url_invalid = "/api/ubers/"
    valid_user = {
        "name": "niilo",
        "email": "example@com",
        "age": 22,
        "user_creation_date": datetime.isoformat(datetime.now()),
    }
    invalid_user = {
        "thisis": "nuulo",
        "asd": 22
    }

    #Valid exercise to valid user (also check that can be get)
    resp = client.post(resource_url_valid, json=valid_user)
    assert resp.status_code == 201
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    #check that last user is the one we just added
    res = json.loads(resp.data).get("users")
    assert res[len(res)-1] == valid_user

    #Invalid data to valid url
    resp = client.post(resource_url_valid, json=invalid_user)
    assert resp.status_code == 400

    #Valid data to invalid url
    resp = client.post(resource_url_invalid, json=valid_user)
    assert resp.status_code == 404

    #Invalid data to invalid url
    resp = client.post(resource_url_invalid, json=invalid_user)
    assert resp.status_code == 404

    #no json
    resp = client.post(resource_url_valid, data="asd")
    assert resp.status_code == 415

def test_usercollection_get(client):
    """
    Function for testing get method on UserCollection resource
    """
    resource_url_valid = "/api/users/"
    resource_url_invalid = "/api/ubers/"

    #Get from valid url
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    cont = json.loads(resp.data)["users"]
    excepted = get_user_dummy_data()
    print("EX",excepted)
    print("GOT:", cont)
    for item in cont:
        assert item in excepted

    #Get from invalid url
    resp = client.get(resource_url_invalid)
    assert resp.status_code == 404

def test_useritem_get(client):
    """
    Function for testing get method on UserItem resource
    """
    resource_url_valid = "/api/users/1/"
    resource_url_not_exist = "/api/users/999/"

    #Get user from valid url
    resp = client.get(resource_url_valid)
    assert resp.status_code == 200
    res = json.loads(resp.data)
    expected = get_user_dummy_data()
    assert res==expected[0]

    #Get not existing user
    resp = client.get(resource_url_not_exist)
    assert resp.status_code == 404
    

def test_useritem_put(client):
    """
    Function for testing put method on UserItem resource
    """
    resource_url_valid = "/api/users/1/"
    resource_url_not_exist = "/api/users/999/"
    updated_user = {
        "name": "niilo",
        "email": "example@com",
        "age": 22,
        "user_creation_date": datetime.isoformat(datetime.now()),
    }
    invalid_json = {
        "user_id": 1,
        "thisis": "invalid"
    }

    #Put updated user
    resp = client.put(resource_url_valid, json=updated_user)
    assert resp.status_code == 204
    #get updated user and check that it matches
    resp = client.get(resource_url_valid)
    res = json.loads(resp.data)
    assert res == updated_user

    #Put on not existing user
    resp = client.put(resource_url_not_exist, json=updated_user)
    assert resp.status_code == 404

    #Non json
    resp = client.put(resource_url_valid, data="asd")
    assert resp.status_code == 415

    #invalid json
    resp = client.put(resource_url_valid, json=invalid_json)
    assert resp.status_code == 400


def test_useritem_del(client):
    """
    Function for testing delete method on UserItem resource
    """
    resource_url_valid = "/api/users/1/"
    resource_url_not_exist = "/api/users/999/"

    #Delete existing user
    resp = client.delete(resource_url_valid)
    assert resp.status_code == 204
    #Check that this user can't be found anymore
    resp = client.get(resource_url_valid)
    assert resp.status_code == 404

    #Try to delete not existing user
    resp = client.delete(resource_url_not_exist)
    assert resp.status_code == 404
