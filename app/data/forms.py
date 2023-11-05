from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, widgets
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class MultiCheckboxField(SelectMultipleField):
  widget = widgets.ListWidget(prefix_label=False)  # noqa
  option_widget = widgets.CheckboxInput()  # noqa


class ChangeFullnameForm(FlaskForm):
    fullname = StringField('ФИО', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class SelectUser(FlaskForm):
    select = SelectField('Выберите пользователя')
    submit = SubmitField('Подтвердить')
