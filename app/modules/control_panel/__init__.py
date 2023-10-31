from flask import Blueprint

bp = Blueprint('control_panel', __name__, url_prefix='/control_panel', template_folder='templates')

from app.modules.control_panel import control_panel
