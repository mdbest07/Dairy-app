from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SECRET_KEY'] = 'secretkey2026'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    entries = db.relationship('Entry', backref='author', lazy=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def index():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', entries=entries)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template('register.html', error="Username taken")
        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
        return render_template('login.html', error="Wrong credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/new_add', methods=['GET', 'POST'])
@login_required
def add_new_entries():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        now = datetime.now()
        date = f"{now.day}/{now.month}/{str(now.year)[2:]} {now.strftime('%I:%M%p')}"
        new_entry = Entry(
            user_id=current_user.id,
            title=title,
            body=body,
            date=date
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect('/')
    return render_template('add.html')

@app.route('/entry/<int:uid>')
@login_required
def view_entry(uid):
    entry = Entry.query.filter_by(id=uid, user_id=current_user.id).first()
    if not entry:
        return redirect('/')
    return render_template('entry.html', entry=entry)

@app.route('/delete/<int:uid>', methods=['POST'])
@login_required
def delete(uid):
    entry = Entry.query.filter_by(id=uid, user_id=current_user.id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect('/')

@app.route('/edit/<int:uid>', methods=['GET', 'POST'])
@login_required
def edit(uid):
    entry = Entry.query.filter_by(id=uid, user_id=current_user.id).first()
    if request.method == 'POST':
        entry.title = request.form.get('title')
        entry.body = request.form.get('body')
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', entry=entry)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        term = request.form.get('title')
        entries = Entry.query.filter(
            Entry.user_id == current_user.id,
            Entry.title.contains(term)
        ).all()
        return render_template('index.html', entries=entries)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)