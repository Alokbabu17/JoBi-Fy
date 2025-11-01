from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "jobify_secret_key_change_this"

DB_PATH = "jobify.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    fullname TEXT
                    )''')
        c.execute('''CREATE TABLE posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    skills TEXT,
                    amount INTEGER,
                    author TEXT
                    )''')
        # sample user: username: test, password: test123
        pw = generate_password_hash("test123")
        c.execute("INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)",
                  ("test", pw, "Test User"))
        # sample posts
        sample_posts = [
            ("Need a Prompt Engineer", "I need someone to write optimized prompts for ChatGPT for e-commerce product descriptions.", "prompt-writing, ai", 300, "CompanyA"),
            ("Merge 5 PDFs", "Merge 5 pdf files into one and optimize size.", "pdf, typing", 100, "Rahul"),
            ("HTML Landing Page tweak", "Small UI fixes on an existing landing page (responsive + fonts).", "html, css", 400, "DesignTeam")
        ]
        c.executemany("INSERT INTO posts (title, description, skills, amount, author) VALUES (?, ?, ?, ?, ?)",
                      sample_posts)
        conn.commit()
        conn.close()
        print("DB initialized with sample data.")
    else:
        print("DB already exists.")

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        fullname = request.form.get('fullname','')
        if not username or not password:
            flash("Enter username & password")
            return redirect(url_for('register'))
        pw_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)",
                         (username, pw_hash, fullname))
            conn.commit()
            conn.close()
            flash("Registration successful. Please login.")
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Username already exists.")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password']
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['user'] = user['username']
        session['fullname'] = user['fullname']
        return redirect(url_for('home'))
    else:
        flash("Invalid credentials")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('home.html', posts=posts, user=session['user'])

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if not post:
        return "Post not found", 404
    return render_template('post.html', post=post)

# Optional: route to create posts (for testing)
@app.route('/create_post', methods=['GET','POST'])
def create_post():
    if 'user' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        skills = request.form['skills']
        amount = request.form['amount'] or 0
        author = session['user']
        conn = get_db_connection()
        conn.execute("INSERT INTO posts (title, description, skills, amount, author) VALUES (?, ?, ?, ?, ?)",
                     (title, description, skills, amount, author))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return """
    <form method="post">
      Title: <input name="title"><br>
      Desc: <textarea name="description"></textarea><br>
      Skills: <input name="skills"><br>
      Amount: <input name="amount"><br>
      <button type="submit">Add</button>
    </form>
    """

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
