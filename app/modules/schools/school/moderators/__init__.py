from flask import Blueprint

bp = Blueprint('moderators', __name__, url_prefix='/moderators')

from app.modules.schools.school.moderators import moderators
