"""
Implementation for Fitnessbuddy9000
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger, swag_from

db = SQLAlchemy()

# Based on https://github.com/enkwolf/pwp-course-sensorhub-api-example
def create_app(test_config=None):
    """
    Create app based on config or test_config
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    #add API documentation, url: /apidocs/
    app.config["SWAGGER"] = {
        "title": "Fitnessbuddy API",
        "openapi": "3.0.3",
        "uiversion": 3,
    }
    swagger = Swagger(app, template_file="doc/fitnessbuddy.yml")

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError as error:
        print(error)

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
