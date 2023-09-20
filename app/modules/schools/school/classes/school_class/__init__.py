from flask import Blueprint

bp = Blueprint('school_class', __name__, url_prefix='/<class_id>')

from app.modules.schools.school.classes.school_class import school_class

from app.modules.schools.school.classes.school_class.class_teacher import bp as teacher_bp
from app.modules.schools.school.classes.school_class.schedule import bp as schedule_bp
from app.modules.schools.school.classes.school_class.students import bp as students_bp

bp.register_blueprint(teacher_bp)
bp.register_blueprint(students_bp)
bp.register_blueprint(schedule_bp)
