from flask import Blueprint

bp = Blueprint('admin_tools', __name__, url_prefix='/admin_tools')

from app.modules.admin_tools import admin_tools
