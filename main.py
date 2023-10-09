from flask import Flask, render_template, url_for, redirect, request, abort, flash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Flask_Key'

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
db = SQLAlchemy()
db.init_app(app)


# CREATE TABLE
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250), nullable=False)


# User table for all your registered users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        task_data = request.form

        new_task = Task(
            text=task_data["text"],
        )

        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("home"))

    result = db.session.execute(db.select(Task))
    tasks = result.scalars().all()
    return render_template("index.html", all_tasks=tasks, current_user=current_user)




if __name__ == "__main__":
    app.run(debug=True, port=5002)