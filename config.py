from os import environ, path

app_dir = path.abspath(path.dirname(__file__))


class BaseConfig(object):
    SECRET_KEY = environ.get('SECRET_KEY') or 'never-never-never-sleep'
    JSON_AS_ASCII = environ.get('JSON_AS_ASCII') or False
    UPLOAD_FOLDER = environ.get('UPLOAD_FOLDER') or "static/files"


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
