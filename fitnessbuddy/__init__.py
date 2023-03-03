import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import click
from flask.cli import with_appcontext

db = SQLAlchemy()

# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
        
    try:
        os.makedirs(app.instance_path)
    except OSError as e:
        print(e)


    db.init_app(app)

    from . import models
    from . import api
    from fitnessbuddy.utils import UserConverter, MeasurementsConverter, ExerciseConverter
    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["exercise"] = ExerciseConverter
    app.url_map.converters["measurements"] = MeasurementsConverter
    app.cli.add_command(models.init_db_command)
    app.register_blueprint(api.api_bp)
    
    return app


