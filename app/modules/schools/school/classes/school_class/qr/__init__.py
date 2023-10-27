from flask import Blueprint

bp = Blueprint('qr_class', __name__, url_prefix='/qrs', template_folder='templates')

from app.modules.schools.school.classes.school_class.qr import qr
