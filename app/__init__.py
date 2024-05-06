from os import path, environ

from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask import Flask

from .data.db_session import global_init
from .data.functions import check_and_clear_times

dir_name = path.dirname(path.realpath(__file__))

CONFIG_PATH = path.join(dir_name, path.join("data", "config.json"))
DB_PATH = path.join(dir_name, path.join("db", "data.sqlite3"))
RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
SERVICE_MODE = False

app = Flask(__name__)
app.config.from_object(environ.get('FLASK_ENV') or 'config.ProductionConfig')

global_init(DB_PATH, echo=app.config["DEBUG"])

bootstrap = Bootstrap(app)

login_manager = LoginManager(app)

scheduler = APScheduler(app=app)
scheduler.start()

check_and_clear_times(CONFIG_PATH, echo=app.config["DEBUG"])

from app.modules.control_panel import bp as control_bp
from app.modules.profile import bp as profile_bp
from app.modules.schools import bp as schools_bp
from app.modules.admits import bp as admits_bp
from app.modules.errors import bp as errors_bp
from app.modules.auth import bp as auth_bp
from app.modules.qr import bp as qr_bp

app.register_blueprint(control_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(schools_bp)
app.register_blueprint(admits_bp)
app.register_blueprint(errors_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(qr_bp)

from . import main

from app.modules import work_scheduler
