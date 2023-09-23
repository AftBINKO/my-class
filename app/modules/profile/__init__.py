from flask import Blueprint

bp = Blueprint('profile', __name__, template_folder='templates', url_prefix='/profile')
# TODO: переделать в User, убрать зависимость управления пользователем от модели

from app.modules.profile import profile
