from flask import Blueprint

bp = Blueprint('school', __name__, url_prefix='/<int:school_id>', template_folder='templates')

from app.modules.schools.school import school

from app.modules.schools.school.moderators import bp as moderators_bp
from app.modules.schools.school.teachers import bp as teachers_bp
from app.modules.schools.school.classes import bp as classes_bp

bp.register_blueprint(moderators_bp)
bp.register_blueprint(teachers_bp)
bp.register_blueprint(classes_bp)
