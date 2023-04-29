"""
Module for testing statistics resource
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

stats_schema = {'type': 'object', 'required': ['date', 'user_id'], 'properties': 
               {'date': {'description': "Datetime when these stats were generated", 'type': 'string'}, 
                'user_id': {'description': "User id", 'type': 'number'}, 
                'total_exercises': {'description': "Total amount of exercises this user has done", 'type': 'number'}, 
                'daily_exercises': {'description': "Average number of exercises per day", 'type': 'number'},
                'daily_calories_in': {'description': "Average number of calories eaten per day", 'type': 'number'},
                'daily_calories_out': {'description': "Average number of calories burnt per day", 'type': 'number'}
                }}

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

def test_stats_post(client):
    """
    Function for testing post method on Stats resource
    """
    resource_url_valid = "/api/users/1/stats/"
    resource_url_invalid = "/api/users/21311/stats/"
    valid_body = {
            "date": datetime.isoformat(datetime.now()),
            "user_id": 1,
            "total_exercises": 15,
            "daily_exercises": 0.8,
            "daily_calories_in": 2575.6,
            "daily_calories_out": 2575.6
        }
    invalid_body = {
        "thisis": "nuulo",
        "asd": 22
    }

    #post to valid url with valid body
    resp = client.post(resource_url_valid, json=valid_body)
    assert resp.status_code == 201
    
    #Verify controls
    controls = json.loads(resp.data)["@controls"]
    expected = {'self': {'href': '/api/users/1/stats/'}}
    assert controls == expected

    #Invalid data to valid url
    resp = client.post(resource_url_valid, json=invalid_body)
    assert resp.status_code == 400

    #Valid data to invalid url
    resp = client.post(resource_url_invalid, json=valid_body)
    assert resp.status_code == 404

    #Invalid data to invalid url
    resp = client.post(resource_url_invalid, json=invalid_body)
    assert resp.status_code == 404

    #no json
    resp = client.post(resource_url_valid, data="asd")
    assert resp.status_code == 415

def test_stats_get(client):
    """
    Function for testing get method on Stats resource
    """
    resource_url_valid = "/api/users/1/stats/"
    resource_url_invalid = "/api/users/21311/stats/"

    #Get from valid url
    resp = client.get(resource_url_valid)
    assert resp.status_code == 202

    #Get from invalid url
    resp = client.get(resource_url_invalid)
    assert resp.status_code == 404
