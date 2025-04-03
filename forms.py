from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL, Email


# WTForm for creating a task
class CreateTaskForm(FlaskForm):
    task = StringField("Task", validators=[DataRequired()])
    complete = BooleanField("Complete")
    starred = StringField("Star")
    due_date = StringField("Due Date")
    submit = SubmitField("Submit Task")