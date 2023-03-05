import datetime
import os
import json
from fitnessbuddy.models import Exercise, User, Measurements

def populate_database(db, app):
    """
    Dump contents of dummy_data.json to database
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), "dummy_data.json"), "r",
            encoding="utf-8") as file:
            dummy_data = json.load(file)
            for user in dummy_data.get("Users"):
                entry = User(name=user.get("name"), email=user.get("email"), age=user.get("age"),
                            user_creation_date=datetime.datetime.strptime(user.get("date"),
                            "%d/%m/%y %H:%M:%S"))
                db.session.add(entry)
            db.session.commit()
            for exercise in dummy_data.get("Exercise_record"):
                entry = Exercise(name=exercise.get("name"), duration=exercise.get("duration"),
                    date=datetime.datetime.strptime(exercise.get("date"), "%d/%m/%y %H:%M:%S"),
                    user_id=exercise.get("user_id"))
                db.session.add(entry)
            db.session.commit()
            for meas in dummy_data.get("Measurements"):
                entry = Measurements(weight=meas.get("weight"), calories_in=meas.get("calories_in"),
                    calories_out=meas.get("calories_out"), date=datetime.datetime.strptime(
                    meas.get("date"),"%d/%m/%y %H:%M:%S"), user_id=meas.get("user_id"))
                db.session.add(entry)
            db.session.commit()

            return True

    except Exception:
        return False
