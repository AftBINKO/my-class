from flask import Blueprint

bp = Blueprint('errors', __name__)

from app.modules.errors import handlers
