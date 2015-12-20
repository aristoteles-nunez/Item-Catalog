from flask_wtf import Form
from wtforms import SubmitField, validators


class DeleteItemForm(Form):
    delete = SubmitField('submitDelete')
