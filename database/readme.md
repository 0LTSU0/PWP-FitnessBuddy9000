# Database

## Dependancies
Database is implemented using SQLAlchemy. List of requirements for using/testing the database are in requirements.txt

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
