import datetime
import forms
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Date
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, URL


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

### SET UP DB ###
class Base(DeclarativeBase):
    pass


# Connect to DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)



# CONFIGURE TABLES

class TodoList(db.Model):
    __tablename__ = "todo_list"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    # This acts as a list of to.do item objects attached to each User.
    tasks = relationship("TodoTask", back_populates="todo_list", cascade="all, delete")


class TodoTask(db.Model):
    __tablename__ = "todo_task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    todo_list_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("todo_list.id", ondelete="CASCADE"))
    task: Mapped[str] = mapped_column(String(256), nullable=False)
    complete: Mapped[bool] = mapped_column(Boolean, default=False)
    starred: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    todo_list = relationship("TodoList", back_populates="tasks")

with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", "POST"])
def home():
    form = forms.CreateTaskForm()

    # Handle form submission BEFORE querying for data
    if form.validate_on_submit():
        print("Form submitted with task:", form.task.data)
        todo_lists = db.session.scalars(db.select(TodoList)).all()
        if not todo_lists:
            # Create new list
            list_name = datetime.datetime.now().strftime("List - %Y-%m-%d %H:%M:%S")
            new_list = TodoList(name=list_name, date=datetime.date.today())
            db.session.add(new_list)
            db.session.flush()

            new_task = TodoTask(task=form.task.data, todo_list_id=new_list.id)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("home"))

        else:

            first_list = todo_lists[0]
            new_task = TodoTask(task=form.task.data, todo_list_id=first_list.id)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("home"))

    # Now pull the todo_lists AFTER any form logic has had a chance to modify the DB
    todo_lists = db.session.scalars(db.select(TodoList)).all()
    return render_template("index.html", form=form, todo_lists=todo_lists)


@app.route("/task/<int:task_id>/update", methods=["POST"])
def update_task(task_id):
    task = db.get_or_404(TodoTask, task_id)

    if "toggle_complete" in request.form:
        task.complete = not task.complete

    if "toggle_star" in request.form:
        task.starred = not task.starred

    db.session.commit()
    return redirect(url_for("home"))



if __name__ == "__main__":
    app.run(debug=True)