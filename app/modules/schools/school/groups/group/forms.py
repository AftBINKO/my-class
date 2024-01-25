from wtforms.fields.choices import SelectField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class EditGroupForm(FlaskForm):
    name = StringField('Название группы', validators=[DataRequired()])
    t = SelectField('Выберите категорию')
    submit = SubmitField('Подтвердить')
