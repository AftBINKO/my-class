from flask import Blueprint

bp = Blueprint('students', __name__, url_prefix='/students', template_folder='templates')

from app.modules.schools.school.classes.school_class.students import students
