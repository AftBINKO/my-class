from flask import Blueprint

bp = Blueprint('profile', __name__, template_folder='templates', url_prefix='/profile')

from app.modules.profile import profile
