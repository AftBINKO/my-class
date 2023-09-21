from flask import Blueprint

bp = Blueprint('schools', __name__, url_prefix='/schools', template_folder='templates')

from app.modules.schools import schools

from app.modules.schools.school import bp as school_bp

bp.register_blueprint(school_bp)
