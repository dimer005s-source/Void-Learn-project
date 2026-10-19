from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'void-777-key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'new_users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = ""

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
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    google_link = db.Column(db.String(200))
    img_link = db.Column(db.String(200))
    tags = db.Column(db.String(200))
    is_visible = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('profile'))
        flash("ОШИБКА ДОСТУПА", "error")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fio = request.form.get('fio')
        email = request.form.get('email')
        password = request.form.get('password')
        grade = request.form.get('school_class')
        if User.query.filter_by(email=email).first():
            return redirect(url_for('register'))
        new_user = User(fio=fio, email=email, password=password, grade=grade)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('profile'))
    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    user_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', items=user_items)

@app.route('/portfolios')
@login_required
def portfolios():
    all_items = Portfolio.query.filter((Portfolio.is_visible == True) | (Portfolio.user_id == current_user.id)).all()
    output = []
    for item in all_items:
        author = User.query.get(item.user_id)
        output.append({
            'title': item.title,
            'description': item.description,
            'tags': item.tags if item.tags else "#void",
            'google_link': item.google_link,
            'author_name': author.fio if author else "Root_User"
        })
    return render_template('portfolios.html', items=output)

@app.route('/rating')
@login_required
def rating():
    u_list = User.query.all()
    u_sorted = sorted(u_list, key=lambda u: (u.score_py or 0) + (u.score_cpp or 0) + (u.score_cs or 0) + (u.score_java or 0), reverse=True)
    return render_template('rating.html', users=u_sorted)

@app.route('/save_portfolio', methods=['POST'])
@login_required
def save_portfolio():
    title = request.form.get('title')
    g_link = request.form.get('google_link')
    tags = f"{request.form.get('lang_tag', '')} {request.form.get('type_tag', '')}".strip()
    new_item = Portfolio(user_id=current_user.id, title=title, google_link=g_link, tags=tags)
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/lessons')
@login_required
def lessons():
    python_ids = ["34Rp6KVGIEM", "CfqX2_xY8VQ", "ML5tP8m6SHw", "DZvNZ9l9NT4", "SUDNfS_0X-Q", "vMD6-jzgDvI", "-X2ubBdP2Ak", "pqaBWcsBGyA", "cQfu-hYo2o4", "W2oO1Y-QDzo", "6eNtZ8wY7qI", "6K5v4--G__U", "t-xQAhLNYSs", "3nveLco08Y0", "uGsSTZjUoIc"]
    cpp_ids = ["5l9nxwh5Wiw", "FKwZqkfGyjc", "AnJWQoKmG7M", "93MfXvA1Qq8", "UB1eyj1LJyI", "Rd10XYY94dI", "702lSkBg5so", "P8oANnmWNM8", "zQ8YBJCpsx4", "Jm8y4OQsNpM", "3GALXU-F3C8", "DKkAJtaE0w0", "f63JnOf1FHo", "b7meCwo7SRE", "Y0jHwddTzX8"]
    csharp_ids = ["_8yZYhAkQjQ", "3MireZUB3Hw", "8q200PT8jTU", "L4PkgGMJTgI", "agse5YvwKoo", "rHHM7pzg7Z8", "e0ajLLezBPE", "MrEelmsSoC0", "DYoXXSjzbaU", "K5gqIUTBey0", "rj9KHVLXaME", "ij__675AuqM", "hzi4xWFFnBU", "TpkMZprzoXE", "ktVCHcsdIWU"]
    java_ids = ["U2OliQwRb6c", "-1LLzZC-9cU", "CEMhFQZrVzw", "mTucAnRpxcQ", "-RXEXP4-Iic", "SdGp-5pcPeA", "wlKQBgJqPRs", "4oRyzq6Z4KE", "MzNoISmsmpk", "kbYVt54Emxw", "XU4crdUR1DI", "7UJyp2A5lQ8", "sfDFZPE9tuw", "lr8SsTi9uKI", "z_Us76GSf_Y"]
    
    modules = {
        "Python": [{"title": f"PYTHON: УРОК {idx+1}", "video_url": f"https://www.youtube.com/embed/{vid}"} for idx, vid in enumerate(python_ids)],
        "C++": [{"title": f"C++: УРОК {idx+1}", "video_url": f"https://www.youtube.com/embed/{vid}"} for idx, vid in enumerate(cpp_ids)],
        "C#": [{"title": f"C#: УРОК {idx+1}", "video_url": f"https://www.youtube.com/embed/{vid}"} for idx, vid in enumerate(csharp_ids)],
        "Java": [{"title": f"JAVA: УРОК {idx+1}", "video_url": f"https://www.youtube.com/embed/{vid}"} for idx, vid in enumerate(java_ids)]
    }
    return render_template('lessons.html', modules=modules)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)