from flask import Blueprint

bp = Blueprint('class_teacher', __name__, url_prefix='/class_teacher')

from app.modules.schools.school.classes.school_class.class_teacher import class_teacher
