from fitnessbuddy.models import Exercise, User, Measurements
import datetime
import os, json


# Dump contents of dummy_data.json to db
def populate_database(db, app):
    try:
        with open(os.path.join(__file__.rstrip("populate_database.py"), "dummy_data.json"), "r") as f:
            dummy_data = json.load(f)
            for user in dummy_data.get("Users"):
                entry = User(name=user.get("name"), email=user.get("email"), age=user.get("age"), user_creation_date=datetime.datetime.strptime(user.get("date"), "%d/%m/%y %H:%M:%S"))
                db.session.add(entry)
            db.session.commit()
            for exercise in dummy_data.get("Exercise_record"):
                entry = Exercise(name=exercise.get("name"), duration=exercise.get("duration"), date=datetime.datetime.strptime(exercise.get("date"), "%d/%m/%y %H:%M:%S"), user_id=exercise.get("user_id"))
                db.session.add(entry)
            db.session.commit()
            for meas in dummy_data.get("Measurements"):
                entry = Measurements(weight=meas.get("weight"), calories_in=meas.get("calories_in"), calories_out=meas.get("calories_out"), date=datetime.datetime.strptime(meas.get("date"), "%d/%m/%y %H:%M:%S"), user_id=meas.get("user_id"))
                db.session.add(entry)
            db.session.commit()
            
            return True

    except Exception:
        return False