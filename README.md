# PWP SPRING 2023
# PROJECT NAME
# Group information
* Student 1. Jouni Annamaa jannamaa19@student.oulu.fi
* Student 2. Lauri Sundelin lsundeli19@student.oulu.fi
* Student 3. Lassi Tölli ltolli19@student.oulu.fi
* Student 4. Name and email

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

# Requirements
Required external libraries can be found in requirements.txt

# Running API, Client and auxilary service
Running the API:

Linux
- API:
    - export FLASK_APP=fitnessbuddy
    - export FLASK_ENV=development
    - flask init-db
    - (optional: flask fill-db)
    - flask run
- Auxilary service worker (in /worker. Also need to have pika credential json in /client)
    - python3 worker.py
- Client (in /client. Also need to have pika credential json here)
    - python3 client.py

Windows
- API:
    - set FLASK_APP=fitnessbuddy
    - set FLASK_ENV=development
    - flask init-db
    - (optional: flask fill-db)
    - flask run
- Auxilary service worker (in /worker. Also need to have pika credential json in /client)
    - python worker.py
- Client (in /client. Also need to have pika credential json here)
    - python client.py

# Tests
Running tests:

Linux
in PWP-FitnessBuddy9000/test/ run: python3 -m pytest

Windows
in PWP-FitnessBuddy9000/test/ run: run_pytest.bat


# Database (outdated)

## Dependancies
Database is implemented using SQLAlchemy. List of requirements for using/testing the database are in requirements.txt

## Playing with databsae manually (and populating it with dummy data)
In ..\PWP-FitnessBuddy9000 run the following commands:
- "python3"
- ">>> from database.models import *"
- ">>> from tools.populate_database import *" 
- ">>> app, db = create_app()"
- ">>> db.create_all()"
- ">>> populate_database(db, app)"
- Run wanted commands e.g. ">>> User.query.filter_by(id=1)[0].name"