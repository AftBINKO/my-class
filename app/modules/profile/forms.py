from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class ChangeLoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    new_password_again = PasswordField('Повторите новый пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
