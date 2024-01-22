from flask import Blueprint

bp = Blueprint('group', __name__, url_prefix='/<int:group_id>', template_folder='templates')

from app.modules.schools.school.groups.group import group

from app.modules.schools.school.groups.group.leader import bp as teacher_bp
from app.modules.schools.school.groups.group.schedule import bp as schedule_bp
from app.modules.schools.school.groups.group.students import bp as students_bp
from app.modules.schools.school.groups.group.qr import bp as qr_group_bp

bp.register_blueprint(teacher_bp)
bp.register_blueprint(students_bp)
bp.register_blueprint(schedule_bp)
bp.register_blueprint(qr_group_bp)
