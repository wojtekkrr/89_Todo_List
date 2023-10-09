from flask import Flask, render_template, url_for, redirect, request, abort, flash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

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
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    # Create Foreign Key
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "tasks" refers to the tasks property in the User class.
    author = relationship("User", back_populates="tasks")
    text = db.Column(db.String(250), nullable=False)



# User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # This will act like a list of Task objects attached to each User.
    # The "author" refers to the author property in the Task class.
    tasks = relationship("Task", back_populates="author")


with app.app_context():
    db.create_all()


# Create an admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        try:
            if current_user.id != 1:
                return abort(403)
        except AttributeError:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# Create an registered-user-only decorator
def registered_user_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If user is authenticated then return abort with 403 error
        if not current_user.is_authenticated:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# Create an unregistered-user-only decorator
def unregistered_user_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If user is not authenticated then return abort with 403 error
        if current_user.is_authenticated:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


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

    try:
        result = db.session.execute(db.select(Task).where(Task.author_id == current_user.id))
    except AttributeError:
        result = db.session.execute(db.select(Task).where(Task.author_id == None))
    finally:
        tasks = result.scalars().all()

    return render_template("index.html", all_tasks=tasks, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
# @unregistered_user_only
def login():
    if request.method == "POST":
        login_data = request.form
        result = db.session.execute(db.select(User).where(User.email == login_data["email"]))
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, login_data["password"]):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)

            tasks = db.session.query(Task).filter(Task.author_id.is_(None)).all()

            for task in tasks:
                task.author = current_user

            db.session.commit()
            return redirect(url_for('home'))
    return render_template("login.html", current_user=current_user)


@app.route('/logout')
@registered_user_only
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/register", methods=["GET", "POST"])
# @unregistered_user_only
def register():
    if request.method == "POST":
        data = request.form
        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == data["email"]))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        #Securing the password
        hash_and_salted_password = generate_password_hash(
            data["password"],
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=data["email"],
            name=data["name"],
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        tasks = db.session.query(Task).filter(Task.author_id.is_(None)).all()

        for task in tasks:
            task.author = current_user

        db.session.commit()
        return redirect(url_for("home"))
    return render_template("register.html", current_user=current_user)





if __name__ == "__main__":
    app.run(debug=True, port=5002)