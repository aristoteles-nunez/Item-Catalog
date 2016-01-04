from flask_wtf import Form
from wtforms import SubmitField, StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed, FileField


class ItemForm(Form):
    """It defines the fields to render in WTForms for each item
    """
    name = StringField('Name', validators=[Length(min=3, message="Name too short"),
                                           DataRequired()])
    description = TextAreaField('Description')
    category_id = IntegerField('Category', validators=[DataRequired()])
    photo = FileField('Image for item', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Format not supported')])
    save = SubmitField('Save')


class DeleteForm(Form):
    """It defines the fields to delete items and categories
    """
    delete = SubmitField('Delete')


class CategoryForm(Form):
    """It defines the fields to render in WTForms for each Category
    """
    name = StringField('Name', validators=[Length(min=2, message="Name too short"),
                                           DataRequired()])
    save = SubmitField('Save')
