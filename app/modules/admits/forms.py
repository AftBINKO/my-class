from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class AdmitForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
