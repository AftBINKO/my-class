from flask import Blueprint

bp = Blueprint('leader', __name__, url_prefix='/leader', template_folder='templates')

from app.modules.schools.school.groups.group.leader import leader
