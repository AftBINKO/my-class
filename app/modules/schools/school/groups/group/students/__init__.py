from flask import Blueprint

bp = Blueprint('students', __name__, url_prefix='/students', template_folder='templates')

from app.modules.schools.school.groups.group.students import students
