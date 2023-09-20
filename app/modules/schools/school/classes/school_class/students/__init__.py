from flask import Blueprint

bp = Blueprint('students', __name__, url_prefix='/students')

from app.modules.schools.school.classes.school_class.students import students
