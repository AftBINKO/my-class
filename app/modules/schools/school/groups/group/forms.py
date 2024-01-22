from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class EditGroupForm(FlaskForm):
    name = StringField('Название группы', validators=[DataRequired()])  # TODO: переделать
    submit = SubmitField('Подтвердить')
