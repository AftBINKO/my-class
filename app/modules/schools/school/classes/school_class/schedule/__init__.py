from flask import Blueprint

bp = Blueprint('schedule', __name__, url_prefix='/schedule')

from app.modules.schools.school.classes.school_class.schedule import schedule
