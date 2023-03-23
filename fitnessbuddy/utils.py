"""
Converter implementations
"""
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound
from fitnessbuddy.models import User, Measurements, Exercise

class UserConverter(BaseConverter):
    """
    Converter for user resource
    """
    def to_python(self, value):
        user = User.query.filter_by(id=value).first()
        if user is None:
            raise NotFound
        return user

    def to_url(self, value):
        return str(value.id)

class MeasurementsConverter(BaseConverter):
    """
    Converter for measurement resource
    """
    def to_python(self, value):
        measurement = Measurements.query.filter_by(id=value).first()
        if measurement is None:
            raise NotFound
        return measurement

    def to_url(self, value):
        return str(value.id)

class ExerciseConverter(BaseConverter):
    """
    Converter for exercise resource
    """
    def to_python(self, value):
        exercise = Exercise.query.filter_by(id=value).first()
        if exercise is None:
            raise NotFound
        return exercise

    def to_url(self, value):
        return str(value.id)


class MasonBuilder(dict):
    """
    Class for creating mason controls, taken from exercise examples
    """
    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href
    
    """
    Class for building Mason objects, taken mostly from course exercise examples 
    """
    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.
        
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """
    
        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )
    
    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.
        
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """
        
        self.add_control(
            "delete",
            href,
            method="DELETE",
            title=title,
        )