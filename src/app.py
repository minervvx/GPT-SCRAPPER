from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import json
from werkzeug.security import generate_password_hash, check_password_hash
import os
from scrape import scrape

app = Flask(__name__)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "gptscraper"),
    "port": os.getenv("DB_PORT", "3306")
} 
config = DB_CONFIG

# SQLAlchemy configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'supersecretkey'

# Initalize SQLAlchemy
db = SQLAlchemy(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique = True)
    password = db.Column(db.String(255), nullable = False)

    # One to Many relationship with Conversations
    conversations = db.relationship('Conversation', backref='user', lazy=True)

class Conversation(db.Model):
    conversation_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    title = db.Column(db.String(255), nullable = False)
    link = db.Column(db.Text, nullable = False)
    text = db.Column(db.Text, nullable = False)
    lowercased_text = db.Column(db.Text, nullable = False)
    created_at = db.Column(db.TIMESTAMP, server_default = db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default = db.func.current_timestamp(), onupdate = db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods = ['GET'])
@login_required
def index():
    conversations = Conversation.query.filter_by(user_id=current_user.id).all()
    for conversation in conversations:
        print("conversation", conversation)
        conversation.text = json.loads(conversation.text)
    
    # print(json.loads(conversations[0].text))
    
    return render_template('beranda.html', conversations=conversations, home = True, user = current_user)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username')
    password = request.form.get('password')

    # Basic validation
    if not username.strip() or not password.strip():
        return render_template('login.html', error="Username or password cannot be empty")

    existing_user = User.query.filter_by(username=username).first()
    if not existing_user or not check_password_hash(existing_user.password, password):
        return render_template('login.html', error="Incorrect username or password")

    login_user(existing_user)
    return redirect('/')


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username')
    password = request.form.get('password')

    # Basic validation
    if not username.strip() or not password.strip():
        return render_template('register.html', error="Username or password cannot be empty")

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return render_template('register.html', error="Username already exists")

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password = hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect('/login')

@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/conversations/<int:conversation_id>', methods = ['GET'])
@login_required
def get_conversation(conversation_id):
    conversations = Conversation.query.filter_by(user_id=current_user.id).all()

    if len(conversations) == 0:
        return redirect('/')

    for conversation in conversations:
        conversation.text = json.loads(conversation.text)
    conversation = next((conversation for conversation in conversations if conversation.conversation_id == conversation_id))
    
    if not conversation:
        return "Conversation not found"
    
    if conversation.user_id != current_user.id:
        return redirect('/')

    return render_template('beranda.html', conversations = conversations, conversation=conversation, home = False, user = current_user)
    

@app.route('/insert', methods = ["POST"])
@login_required
def insert_conversation_route():
    # req_data = request.get_json()
    # title = req_data['title']
    # link = req_data['link']

    title = request.form.get('title')
    link = request.form.get('link')

    user_chat, assitant_chat =  scrape(link, headless=True)
    text = []
    lowercased_text = []

    if not title or not link:
        return "Error: Title or link is empty"

    if len(user_chat) != len(assitant_chat):
        return "Error: User and assistant chat length mismatch"
    
    for i in range(len(user_chat)):
        text.append({"user": user_chat[i], "assistant": assitant_chat[i]})
        lowercased_text.append({"user": user_chat[i].lower(), "assistant": assitant_chat[i].lower()})
    
    new_conv = Conversation(user_id = current_user.id, title = title, link = link, text = json.dumps(text), lowercased_text = json.dumps(lowercased_text))
    db.session.add(new_conv)
    db.session.commit()
    return redirect(f'/conversations/{new_conv.conversation_id}')
@app.route('/history', methods=['GET'])
@login_required
def history():
    # Ambil semua data conversations user
    history_items = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.created_at.desc()).all()
    
    # Hitung beberapa statistik untuk sidebar
    total_scrapers = len(history_items)
    
    # Hitung scraper bulan ini (gunakan library datetime)
    from datetime import datetime
    current_month = datetime.now().month
    current_year = datetime.now().year
    scrapers_this_month = Conversation.query.filter_by(user_id=current_user.id).filter(
        db.extract('month', Conversation.created_at) == current_month,
        db.extract('year', Conversation.created_at) == current_year
    ).count()
    
    # Anda bisa menambahkan logika untuk Active/Inactive jika diperlukan
    active_scrapers = total_scrapers  # Sebagai contoh, semua dianggap aktif
    inactive_scrapers = 0
    
    # Ambil recent activity (5 terakhir)
    recent_activities = Conversation.query.filter_by(user_id=current_user.id).order_by(
        Conversation.updated_at.desc()
    ).limit(5).all()
    
    return render_template(
        'history.html', 
        history_items=history_items, 
        user=current_user,
        total_scrapers=total_scrapers,
        scrapers_this_month=scrapers_this_month,
        active_scrapers=active_scrapers,
        inactive_scrapers=inactive_scrapers,
        recent_activities=recent_activities
    )

@app.route('/delete_scraper', methods=['POST'])
@login_required
def delete_scraper():
    conversation_id = request.form.get('conversation_id')
    
    if not conversation_id:
        return "Error: No conversation ID provided", 400
        
    # Verifikasi bahwa conversation milik user yang sedang login
    conversation = Conversation.query.filter_by(
        conversation_id=conversation_id, 
        user_id=current_user.id
    ).first()
    
    if not conversation:
        return "Error: Conversation not found or unauthorized", 404
    
    # Hapus conversation
    db.session.delete(conversation)
    db.session.commit()
    
    # Redirect ke halaman history
    return redirect('/history')

@app.route('/search_history', methods=['GET'])
@login_required
def search_history():
    search_term = request.args.get('q', '')
    
    if search_term:
        # Cari berdasarkan title atau link yang mengandung search_term
        history_items = Conversation.query.filter_by(user_id=current_user.id).filter(
            db.or_(
                Conversation.title.like(f'%{search_term}%'),
                Conversation.link.like(f'%{search_term}%')
            )
        ).order_by(Conversation.created_at.desc()).all()
    else:
        # Jika tidak ada search term, tampilkan semua
        history_items = Conversation.query.filter_by(user_id=current_user.id).order_by(
            Conversation.created_at.desc()
        ).all()
    
    # Hitung statistik yang sama seperti route /history
    # (kode yang sama seperti di atas)
    total_scrapers = Conversation.query.filter_by(user_id=current_user.id).count()
    
    from datetime import datetime
    current_month = datetime.now().month
    current_year = datetime.now().year
    scrapers_this_month = Conversation.query.filter_by(user_id=current_user.id).filter(
        db.extract('month', Conversation.created_at) == current_month,
        db.extract('year', Conversation.created_at) == current_year
    ).count()
    
    active_scrapers = total_scrapers
    inactive_scrapers = 0
    
    recent_activities = Conversation.query.filter_by(user_id=current_user.id).order_by(
        Conversation.updated_at.desc()
    ).limit(5).all()
    
    return render_template(
        'history.html', 
        history_items=history_items, 
        user=current_user,
        search_term=search_term,
        total_scrapers=total_scrapers,
        scrapers_this_month=scrapers_this_month,
        active_scrapers=active_scrapers,
        inactive_scrapers=inactive_scrapers,
        recent_activities=recent_activities
    )

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            print("Database created successfully!")
    except Exception as e:
        print("Error creating database: ", e)
    app.run(debug = True)


