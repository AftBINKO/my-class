from flask import Blueprint

bp = Blueprint('qr_group', __name__, url_prefix='/qrs', template_folder='templates')

from app.modules.schools.school.groups.group.qr import qr
