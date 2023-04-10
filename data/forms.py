from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class LoginKeyForm(FlaskForm):
    key = PasswordField('Ключ', validators=[DataRequired()])
    submit = SubmitField('Завершить регистрацию')


class FinishRegisterForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class ChangeFullnameForm(FlaskForm):
    fullname = StringField('ФИО', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class ChangeLoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    new_password_again = PasswordField('Повторите новый пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class AddSchoolForm(FlaskForm):
    school = StringField('Короткое название школы', validators=[DataRequired()])
    fullname = StringField('Полное название школы')
    submit = SubmitField('Подтвердить')
