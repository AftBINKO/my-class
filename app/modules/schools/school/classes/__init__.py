from flask import Blueprint

bp = Blueprint('classes', __name__, url_prefix='/classes', template_folder='templates')

from app.modules.schools.school.classes import classes

from app.modules.schools.school.classes.school_class import bp as classes_bp

bp.register_blueprint(classes_bp)
