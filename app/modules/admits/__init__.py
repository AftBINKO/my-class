from flask import Blueprint

bp = Blueprint('admit', __name__, url_prefix='/admits', template_folder='templates')

from app.modules.admits import admits
