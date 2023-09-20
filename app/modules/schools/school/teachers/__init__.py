from flask import Blueprint

bp = Blueprint('teachers', __name__, url_prefix='/teachers')

from app.modules.schools.school.teachers import teachers
