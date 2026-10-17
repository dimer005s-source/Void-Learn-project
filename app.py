from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re 
import json

# ИСПРАВЛЕНО: Добавлены подчеркивания __name__
app = Flask(__name__)
app.config['SECRET_KEY'] = 'void-777-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "ДЛЯ ДОСТУПА К ЭТОЙ СТРАНИЦЕ НУЖНО ВОЙТИ"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    score_py = db.Column(db.Integer, default=0)
    score_cpp = db.Column(db.Integer, default=0)
    score_cs = db.Column(db.Integer, default=0)
    score_java = db.Column(db.Integer, default=0)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    google_link = db.Column(db.String(200))
    tags = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Авто-создание базы при запуске
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/save_portfolio', methods=['POST'])
@login_required
def save_portfolio():
    link = request.form.get('google_link')
    lang = request.form.get('lang_tag')
    p_type = request.form.get('type_tag')
    all_tags = f"{lang} {p_type}"
    
    new_work = Portfolio(user_id=current_user.id, google_link=link, tags=all_tags)
    db.session.add(new_work)
    db.session.commit()
    flash("РАБОТА СОХРАНЕНА!", "success")
    return redirect(url_for('profile'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fio = request.form.get('fio')
        email = request.form.get('email')
        password = request.form.get('password')
        school_class = request.form.get('school_class')

        class_pattern = r"^(?:[1-9]|1[0-1])-[a-zA-Zа-яА-Я]$"
        if not re.match(class_pattern, school_class):
            flash("НЕВЕРНЫЙ ФОРМАТ КЛАССА! ПРИМЕР: 9-А", "error")
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("ЭТОТ EMAIL УЖЕ ЗАНЯТ, БРО!", "error")
            return render_template('register.html')

        new_user = User(fio=fio, email=email, password=password, grade=school_class)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user) 
        return redirect(url_for('profile')) 

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user =User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('profile'))
        flash('НЕВЕРНЫЙ ЛОГИН ИЛИ ПАРОЛЬ', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/rating')
@login_required
def rating():
    users = User.query.all()
    users_sorted = sorted(users, key=lambda u: (u.score_py or 0) + (u.score_cpp or 0) + (u.score_cs or 0) + (u.score_java or 0), reverse=True)
    return render_template('rating.html', users=users_sorted)

@app.route('/test_hub')
def test_hub():
    return render_template('tests_hub.html')

@app.route('/lessons')
@login_required
def lessons():
    return render_template('lessons.html')

@app.route('/start_test/<lang>/<int:level>')
def start_test_logic(lang, level): 
    return render_template('test.html', lang=lang, level=level)

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5000) 