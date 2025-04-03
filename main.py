import datetime
import forms
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Date


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


@app.route("/", methods=["GET", "POST"])
def home():
    form = forms.CreateTaskForm()
    all_lists = db.session.scalars(db.select(TodoList)).all()

    # No lists yet — create one and add task
    if not all_lists:
        if form.validate_on_submit():
            list_name = datetime.datetime.now().strftime("List - %Y-%m-%d %H:%M:%S")
            new_list = TodoList(name=list_name, date=datetime.date.today())
            db.session.add(new_list)
            db.session.flush()

            new_task = TodoTask(
                task=form.task.data,
                todo_list_id=new_list.id,
                complete=form.complete.data,
                starred=form.starred.data,
            )
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("home"))

        return render_template(
            "index.html",
            form=form,
            todo_lists=[],
            active_list=None,
            tasks=[]
        )

    # Lists exist — check if form submitted
    if form.validate_on_submit():
        list_id = request.form.get("list_id")
        if list_id:
            active_list = db.get_or_404(TodoList, list_id)
        else:
            active_list = sorted(all_lists, key=lambda l: l.date, reverse=True)[0]

        new_task = TodoTask(
            task=form.task.data,
            todo_list_id=active_list.id,
            complete=form.complete.data,
            starred=form.starred.data,
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("view_list", list_id=active_list.id))

    # Normal GET
    latest_list = sorted(all_lists, key=lambda l: l.date, reverse=True)[0]
    tasks = latest_list.tasks

    return render_template(
        "index.html",
        form=form,
        todo_lists=all_lists,
        active_list=latest_list,
        tasks=tasks
    )


@app.route("/task/<int:task_id>/update", methods=["POST"])
def update_task(task_id):
    print("update task hit")
    task = db.get_or_404(TodoTask, task_id)
    print(task_id)
    if "toggle_complete" in request.form:
        task.complete = not task.complete

    if "toggle_star" in request.form:
        task.starred = not task.starred

    # here lets just check if the task has actually changed so we don't need to unnecessarily reload the page
    new_task_text = request.form.get("edited_task", "").strip()
    if "edited_task" in request.form and new_task_text != task.task:
        task.task = new_task_text
        db.session.commit()
        return redirect(url_for("view_list", list_id=task.todo_list_id))

    db.session.commit()
    return redirect(url_for("view_list", list_id=task.todo_list_id))


@app.route("/list/<int:list_id>")
def view_list(list_id):
    all_lists = db.session.scalars(db.select(TodoList)).all()
    active_list = db.get_or_404(TodoList, list_id)
    tasks = active_list.tasks

    form = forms.CreateTaskForm()

    return render_template(
        "index.html",
        form=form,
        todo_lists=all_lists,
        active_list=active_list,
        tasks=tasks
    )


@app.route("/list/create", methods=["POST"])
def create_list():
    list_name = datetime.datetime.now().strftime("List - %Y-%m-%d %H:%M:%S")
    new_list = TodoList(name=list_name, date=datetime.date.today())
    db.session.add(new_list)
    db.session.commit()
    return redirect(url_for("view_list", list_id=new_list.id))


@app.route("/list/<int:list_id>/edit", methods=["POST"])
def edit_list_name(list_id):
    todo_list = db.get_or_404(TodoList, list_id)
    new_name = request.form.get("new_name", "").strip()

    if new_name and new_name != todo_list.name:
        todo_list.name = new_name
        db.session.commit()

    return redirect(url_for("view_list", list_id=list_id))


@app.route("/list/<int:list_id>/delete", methods=["POST"])
def delete_list(list_id):
    todo_list = db.get_or_404(TodoList, list_id)
    db.session.delete(todo_list)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)