from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from PIL import Image, ImageDraw, ImageFont
import os
import json
import datetime
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'void-777-key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'new_users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = ""

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Модели БД ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(100))
    school_class = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    exp = db.Column(db.Integer, default=0)
    score_py = db.Column(db.Integer, default=0)
    score_cpp = db.Column(db.Integer, default=0)
    score_cs = db.Column(db.Integer, default=0)
    score_java = db.Column(db.Integer, default=0)
    score_html = db.Column(db.Integer, default=0)
    score_css = db.Column(db.Integer, default=0)

    total_questions_attempted = db.Column(db.Integer, default=0) # Всего вопросов, на которые отвечал
    total_correct_answers = db.Column(db.Integer, default=0)     # Всего правильных ответов
    most_frequent_test = db.Column(db.String(50), default="НЕТ ДАННЫХ") # Самый частый тест
    
    portfolio_items = db.relationship('Portfolio', backref='author', lazy=True)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    google_link = db.Column(db.String(200))
    img_link = db.Column(db.String(200), default='')
    tags = db.Column(db.String(200))
    is_visible = db.Column(db.Boolean, default=True)

# --- Context Processor для передачи текущего XP в каждый шаблон ---
@app.context_processor
def inject_user_exp():
    if current_user.is_authenticated:
        # Важно: всегда запрашиваем актуальный XP из БД
        # current_user.exp может быть неактуален после AJAX-запроса,
        # если пользователь не перезагрузил страницу.
        # Запрашиваем из БД для гарантированной актуальности.
        user = User.query.get(current_user.id)
        return {'global_user_exp': user.exp if user else 0}
    return {'global_user_exp': 0}

# --- Маршруты ---
@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('profile'))
        flash("ОШИБКА ДОСТУПА", "error")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        fio = request.form.get('fio')
        email = request.form.get('email')
        password = request.form.get('password')
        school_class = request.form.get('school_class')
        
        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует", "error")
            return redirect(url_for('register'))
            
        new_user = User(fio=fio, email=email, password=password, school_class=school_class, exp=0)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('profile'))
    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    items = Portfolio.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', current_user=current_user, items=items)

@app.route('/portfolios')
@login_required
def portfolios():
    all_items = Portfolio.query.filter(
        (Portfolio.is_visible == True) | (Portfolio.user_id == current_user.id)
    ).all()
    
    output = []
    for item in all_items:
        author_name = item.author.fio if item.author else "Root_User"
        output.append({
            'title': item.title,
            'description': item.description,
            'tags': item.tags if item.tags else "#void",
            'google_link': item.google_link,
            'author_name': author_name
        })
    return render_template('portfolios.html', items=output)

@app.route('/rating')
@login_required
def rating():
    u_list = User.query.order_by(User.exp.desc()).all()
    return render_template('rating.html', users=u_list)

@app.route('/save_portfolio', methods=['POST'])
@login_required
def save_portfolio():
    title = request.form.get('title')
    description = request.form.get('description')
    g_link = request.form.get('google_link')
    tags = f"{request.form.get('lang_tag', '')} {request.form.get('type_tag', '')}".strip()
    
    new_item = Portfolio(
        user_id=current_user.id, 
        title=title, 
        description=description,
        google_link=g_link, 
        tags=tags
    )
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
    html_ids = ["q8F2L5J_kUo", "nL5yN_k8wE0", "H7w3W_f0YI0", "S4xV6_z1KqY", "G9jP8_a2BlX", "M0cR1_t3NfP", "Q1fG4_v5BcJ", "Y2hA7_d8XeW", "Z3xI0_u9VpL", "A4sD1_e0FjK", "B5gH2_i1LnM", "C6kL3_m2NpO", "D7qR4_s3TvU", "E8wX5_y4ZwC", "F9aB6_c5DeF"]
    css_ids = ["xY7cZ_d9EwF", "aB1cD_e2F_G", "hI3jK_l4M_N", "oP5qR_s6T_U", "vW7xY_z8A_B", "C9dE0_f1G_H", "I2jK3_l4M_N", "O5pQ6_r7S_T", "U8vW9_x0Y_Z", "1a2b3_c4d5e", "6f7g8_h9i0j", "1k2l3_m4n5o", "6p7q8_r9s0t", "1u2v3_w4x5y", "6z7A8_B9C0D"]

    modules = {
        "Python": [{"title": f"PYTHON: УРОК {idx+1}", "video_id": vid} for idx, vid in enumerate(python_ids)],
        "C++": [{"title": f"C++: УРОК {idx+1}", "video_id": vid} for idx, vid in enumerate(cpp_ids)],
        "C#": [{"title": f"C#: УРОК {idx+1}", "video_id": vid} for idx, vid in enumerate(csharp_ids)],
        "Java": [{"title": f"JAVA: УРОК {idx+1}", "video_id": vid} for idx, vid in enumerate(java_ids)],
        "HTML": [{"title": f"HTML: УРОК {idx+1}", "video_id": vid} for idx, vid in enumerate(html_ids)],
        "CSS": [{"title": f"CSS: УРОК {idx+1}", "video_id": vid} for idx, vid in enumerate(css_ids)]
    }
    return render_template('lessons.html', modules=modules)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def load_questions_from_json():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'questions.json')
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения JSON: {e}")
        return {}

@app.route('/test/<lang>')
@login_required
def test_page(lang):
    display_names = {
        "python": "PYTHON", "cpp": "C++", "csharp": "C#", "java": "JAVA",
        "html": "HTML 5", "css": "CSS 3"
    }
    return render_template('test.html',lang_name=display_names.get(lang.lower(), lang.upper()), 
                           lang_code=lang.lower())

@app.route('/api/questions/<lang>')
@app.route('/api/questions/<lang>/<level>')
def get_questions(lang, level="1"):
    try:
        questions_data = load_questions_from_json()
        lang_data = questions_data.get(lang.lower(), {})
        questions = lang_data.get("1", [])
        return jsonify(questions)
    except Exception as e:
        print(f"Ошибка получения вопросов: {e}")
        return jsonify([]), 500

@app.route('/api/save_score', methods=['POST'])
@login_required
def save_score():
    data = request.json or {}
    score = int(data.get('score', 0)) # Количество правильных ответов в текущем тесте
    total_questions_in_test = int(data.get('total_questions', 0)) # Общее количество вопросов в текущем тесте
    lang_code = data.get('lang', '').lower()
    
    user = current_user
    
    # Обновляем общий exp
    user.exp = (user.exp or 0) + score
    
    # Обновляем специфические очки по языкам
    if lang_code == 'python':
        user.score_py = (user.score_py or 0) + score
    elif lang_code == 'cpp':
        user.score_cpp = (user.score_cpp or 0) + score
    elif lang_code == 'csharp':
        user.score_cs = (user.score_cs or 0) + score
    elif lang_code == 'java':
        user.score_java = (user.score_java or 0) + score
    elif lang_code == 'html':
        user.score_html = (user.score_html or 0) + score
    elif lang_code == 'css':
        user.score_css = (user.score_css or 0) + score
    
    # ОБНОВЛЕНИЕ ДЛЯ СТАТИСТИКИ СЕРТИФИКАТА
    user.total_correct_answers = (user.total_correct_answers or 0) + score
    user.total_questions_attempted = (user.total_questions_attempted or 0) + total_questions_in_test

    # Определяем самый частый тест (немного упрощенно, можно улучшить)
    # Здесь просто смотрим, где больше всего очков.
    lang_scores = {
        'Python': user.score_py, 'C++': user.score_cpp, 'C#': user.score_cs,
        'Java': user.score_java, 'HTML': user.score_html, 'CSS': user.score_css
    }
    
    if any(s > 0 for s in lang_scores.values()): # Если хоть какие-то очки есть
        user.most_frequent_test = max(lang_scores, key=lang_scores.get)
    else:
        user.most_frequent_test = "НЕТ ДАННЫХ"

    db.session.add(user)
    db.session.commit()

    return jsonify({'status': 'ok', 'new_exp': user.exp})

@app.route('/tests_hub')
@login_required
def tests_hub():
    return render_template('tests_hub.html')

@app.route('/certificate')
@login_required
def generate_certificate():
    fio = current_user.fio
    user_exp = current_user.exp or 0

    if user_exp < 60:
        return f"<h1 style='color: white; background: #000; padding: 20px;'>НЕДОСТАТОЧНО XP! У вас {user_exp}/60 XP. Пройдите все тесты, чтобы получить сертификат!</h1>", 403

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'static', 'certs', 'template.jpg')
    font_path = os.path.join(base_dir, 'static', 'fonts', 'Black acute.ttf')

    if not os.path.exists(template_path):
        return "Файл шаблона static/certs/template.jpg не найден!", 404

    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    img_w, img_h = img.size

    # Загружаем шрифт (разные размеры для разных строк)
    try:
        font_fio = ImageFont.truetype(font_path, 60) # Для ФИО
        font_main_text = ImageFont.truetype(font_path, 35) # Для основного текста
        font_small_text = ImageFont.truetype(font_path, 25) # Для мелкого текста
        font_date = ImageFont.truetype(font_path, 30) # Для даты
    except Exception:
        # Если шрифт не найден, используем дефолтный
        font_fio = ImageFont.load_default()
        font_main_text = ImageFont.load_default()
        font_small_text = ImageFont.load_default()
        font_date = ImageFont.load_default()

    # --- ТЕКСТОВЫЕ СТРОКИ ДЛЯ СЕРТИФИКАТА ---
    # Можно использовать данные из current_user, если они там есть.
    # Пример: user_grade = current_user.school_class
    # В данный момент используем статичные или вычисляемые значения.
    
    line1_text = fio.upper() # ФИО пользователя
    line2_text = "НАСТОЯЩИЙ МАСТЕР КОДА"
    line3_text = f"УСПЕШНО ЗАВЕРШИЛ ВСЕ МОДУЛИ ОБУЧЕНИЯ"
    line4_text = f"И НАБРАЛ {user_exp} ОЧКОВ ОПЫТА!" # Используем exp из current_user
    line5_text = "VOID_OS_TERMINAL: ДОСТУП РАЗРЕШЕН"

    date_str = datetime.datetime.now().strftime("%d.%m.%Y")

    # --- Отрисовка строк с разными стилями и позициями ---
    
    # 1. ФИО (самый крупный, по центру, неоновый)
    # y_fio = img_h * 0.45; я его чуть поднял, чтобы влезли 5 строк
    y_current = img_h * 0.38 
    text_color_neon = (188, 19, 254) # Неоновый фиолетовый
    
    bbox = draw.textbbox((0, 0), line1_text, font=font_fio)
    text_w = bbox[2] - bbox[0]
    draw.text(((img_w - text_w) / 2, y_current), line1_text, font=font_fio, fill=text_color_neon)
    y_current += font_fio.size + 15 # Отступ после первой строки

    # 2. Основной текст 1 (чуть меньше, по центру, белый/светлый)
    text_color_white = (255, 255, 255)
    bbox = draw.textbbox((0, 0), line2_text, font=font_main_text)
    text_w = bbox[2] - bbox[0]
    draw.text(((img_w - text_w) / 2, y_current), line2_text, font=font_main_text, fill=text_color_white)
    y_current += font_main_text.size + 10 # Отступ

    # 3. Основной текст 2 (по центру, белый)
    bbox = draw.textbbox((0, 0), line3_text, font=font_main_text)
    text_w = bbox[2] - bbox[0]
    draw.text(((img_w - text_w) / 2, y_current), line3_text, font=font_main_text, fill=text_color_white)
    y_current += font_main_text.size + 10 # Отступ

    # 4. Мелкий текст с XP (по центру, серый/зеленый)
    text_color_grey = (150, 255, 150) # Светло-зеленый
    bbox = draw.textbbox((0, 0), line4_text, font=font_small_text)
    text_w = bbox[2] - bbox[0]
    draw.text(((img_w - text_w) / 2, y_current), line4_text, font=font_small_text, fill=text_color_grey)
    y_current += font_small_text.size + 20 # Отступ побольше

    # 5. Подпись (еще мельче, по центру, светло-синий/мятный)
    text_color_mint = (0, 255, 200) # Мятный
    bbox = draw.textbbox((0, 0), line5_text, font=font_small_text) # Используем тот же font_small_text
    text_w = bbox[2] - bbox[0]
    draw.text(((img_w - text_w) / 2, y_current), line5_text, font=font_small_text, fill=text_color_mint)
    # y_current += font_small_text.size + 10 # Отступ

    # Дата (снизу справа, как было)
    draw.text((img_w * 0.7, img_h * 0.85), f"DATE: {date_str}", font=font_date, fill=(255, 255, 255))


    # Сохраняем в буфер памяти
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg', as_attachment=False, download_name=f'Certificate_{fio}.jpg')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)