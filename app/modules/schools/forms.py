from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class EditSchoolForm(FlaskForm):
    school = StringField('Короткое название школы', validators=[DataRequired()])
    fullname = TextAreaField('Полное название школы')
    submit = SubmitField('Подтвердить')
