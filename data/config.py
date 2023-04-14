from os import environ


class Config(object):
    SECRET_KEY = environ.get('SECRET_KEY') or 'never-never-never-sleep'
    JSON_AS_ASCII = environ.get('JSON_AS_ASCII') or False
