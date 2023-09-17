from os import path, environ, getcwd

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

app = Flask(__name__)
app.config.from_object(environ.get('FLASK_ENV') or 'config.DevelopmentConfig')

global_init(DB_PATH, echo=app.config["DEBUG"])

bootstrap = Bootstrap(app)

login_manager = LoginManager(app)

scheduler = APScheduler(app=app)
scheduler.start()

check_and_clear_times(CONFIG_PATH, echo=app.config["DEBUG"])

from . import views
