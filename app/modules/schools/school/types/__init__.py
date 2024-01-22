from flask import Blueprint

bp = Blueprint('types', __name__, url_prefix='/types', template_folder='templates')

from app.modules.schools.school.types import types
