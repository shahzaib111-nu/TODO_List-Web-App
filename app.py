


from flask import Flask, render_template, request, redirect, url_for, abort, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    todos = db.relationship('TodoItem', backref='owner', lazy=True)

# Todo model
class TodoItem(db.Model):
    sr = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home / Dashboard
@app.route("/", methods=["GET", "POST"])
@login_required
def render():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        todo = TodoItem(title=title, description=description, owner=current_user)
        db.session.add(todo)
        db.session.commit()
        flash("TODO added successfully!", "success")
    todo_items = TodoItem.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", todo_items=todo_items)

# Show route (duplicate of home)
@app.route("/show")
@login_required
def show():
    todo_items = TodoItem.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", todo_items=todo_items)

# About
@app.route("/about")
def about():
    return render_template("about.html")

# Delete Todo
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    todo_item = TodoItem.query.filter_by(sr=id, user_id=current_user.id).first()
    if not todo_item:
        abort(404)
    db.session.delete(todo_item)
    db.session.commit()
    flash("TODO deleted!", "danger")
    return redirect("/")

# Edit Todo
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    todo_item = TodoItem.query.filter_by(sr=id, user_id=current_user.id).first()
    if not todo_item:
        abort(404)
    if request.method == 'POST':
        todo_item.title = request.form.get('title')
        todo_item.description = request.form.get('description')
        db.session.commit()
        flash("TODO updated!", "info")
        return redirect("/")
    return render_template("edit.html", todo_item=todo_item)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "warning")
            return redirect('/register')
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect("/")
    return render_template("register.html")

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        print("Form Username:", username)
        print("User from DB:", user)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")
        else:
            flash("Invalid credentials", "danger")
            return redirect('/login')
    return render_template("login.html")

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect("/login")

# DB init
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
# Note: Make sure to set a strong secret key in production.

