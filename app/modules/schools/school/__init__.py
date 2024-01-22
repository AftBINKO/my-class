from flask import Blueprint

bp = Blueprint('school', __name__, url_prefix='/<int:school_id>', template_folder='templates')

from app.modules.schools.school import school

from app.modules.schools.school.moderators import bp as moderators_bp
from app.modules.schools.school.teachers import bp as teachers_bp
from app.modules.schools.school.groups import bp as groups_bp
from app.modules.schools.school.excel import bp as excel_bp
from app.modules.schools.school.types import bp as types_bp

bp.register_blueprint(moderators_bp)
bp.register_blueprint(teachers_bp)
bp.register_blueprint(groups_bp)
bp.register_blueprint(excel_bp)
bp.register_blueprint(types_bp)
