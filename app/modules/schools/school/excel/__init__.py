from flask import Blueprint

bp = Blueprint('excel', __name__, url_prefix='/excel', template_folder='templates')

from app.modules.schools.school.excel import excel
