from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class EditClassForm(FlaskForm):
    class_number = StringField('Класс', validators=[DataRequired()])
    letter = StringField('Литера')
    submit = SubmitField('Подтвердить')
