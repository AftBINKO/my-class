from flask import Blueprint

bp = Blueprint('qr', __name__, url_prefix='/qr')

from app.modules.qr import qr
