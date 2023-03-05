# PWP SPRING 2023
# PROJECT NAME
# Group information
* Student 1. Jouni Annamaa jannamaa19@student.oulu.fi
* Student 2. Lauri Sundelin lsundeli19@student.oulu.fi
* Student 3. Lassi Tölli ltolli19@student.oulu.fi
* Student 4. Name and email

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

How to run the app:
Linux
- export FLASK_APP=fitnessbuddy
- export FLASK_ENV=development
- flask init-db
- flask run
Windows
- set FLASK_APP=fitnessbuddy
- set FLASK_ENV=development
- flask init-db
- flask run

# Database

## Dependancies
Database is implemented using SQLAlchemy. List of requirements for using/testing the database are in requirements.txt

pip install -r requirements.txt

## Testing database automatically
In ..\PWP-FitnessBuddy9000\test run "python3 -m pytest"

## Playing with databsae manually (and populating it with dummy data)
In ..\PWP-FitnessBuddy9000 run the following commands:
- "python3"
- ">>> from database.models import *"
- ">>> from tools.populate_database import *" 
- ">>> app, db = create_app()"
- ">>> db.create_all()"
- ">>> populate_database(db, app)"
- Run wanted commands e.g. ">>> User.query.filter_by(id=1)[0].name"
