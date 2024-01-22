from wtforms import SubmitField, DateField
from wtforms.validators import Optional
from flask_wtf import FlaskForm

from app.data.forms import MultiCheckboxField


class GenerateForm(FlaskForm):
    groups = MultiCheckboxField('Группы', coerce=int)
    start_date = DateField("От", validators=[Optional()])
    end_date = DateField("До", validators=[Optional()])
    submit = SubmitField('Сгенерировать')
