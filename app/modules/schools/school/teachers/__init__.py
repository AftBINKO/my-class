from flask import Blueprint

bp = Blueprint('teachers', __name__, url_prefix='/teachers', template_folder='templates')

from app.modules.schools.school.teachers import teachers
