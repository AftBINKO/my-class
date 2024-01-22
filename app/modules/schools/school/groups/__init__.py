from flask import Blueprint

bp = Blueprint('groups', __name__, url_prefix='/groups', template_folder='templates')

from app.modules.schools.school.groups import groups

from app.modules.schools.school.groups.group import bp as groups

bp.register_blueprint(groups)
