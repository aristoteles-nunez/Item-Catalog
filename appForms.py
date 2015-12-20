from flask_wtf import Form
from wtforms import SubmitField, StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length


class EditItemForm(Form):
    name = StringField('Name', validators=[Length(min=3, message="Name too short"), DataRequired()])
    description = TextAreaField('Description')
    category_id = IntegerField('Category', validators=[DataRequired()])


class DeleteItemForm(Form):
    delete = SubmitField('Delete')
