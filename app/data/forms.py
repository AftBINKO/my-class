from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class ChangeFullnameForm(FlaskForm):
    fullname = StringField('ФИО', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class SelectUser(FlaskForm):
    select = SelectField('Выберите пользователя')
    submit = SubmitField('Подтвердить')
