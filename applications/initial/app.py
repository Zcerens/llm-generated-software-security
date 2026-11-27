from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DATABASE = "notes.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Notes App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
        }

        .container {
            background: white;

            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,.08);
        }

        input, textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 10px;
            margin: 8px 0 15px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }

        textarea {
            min-height: 120px;
        }

        button {
            background: #333;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
        }

        a {
            color: #333;
        }

        .nav {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .note {
            border: 1px solid #ddd;
            padding: 15px;

            margin: 15px 0;
            border-radius: 8px;
        }

        .delete {
            color: #c00;
            float: right;
        }

        .error {
            color: #c00;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
<div class="container">
    {% block content %}{% endblock %}
</div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
{% extends "base" %}
{% block content %}

<h1>Login</h1>

{% if error %}
<div class="error">{{ error }}</div>
{% endif %}

<form method="POST">
    <label>Username</label>
    <input type="text" name="username" required>

    <label>Password</label>
    <input type="password" name="password" required>

    <button type="submit">Login</button>
</form>

<p>
    Don't have an account?
    <a href="{{ url_for('register') }}">Register</a>
</p>

{% endblock %}
"""

REGISTER_TEMPLATE = """
{% extends "base" %}
{% block content %}

<h1>Register</h1>

{% if error %}
<div class="error">{{ error }}</div>
{% endif %}

<form method="POST">
    <label>Username</label>
    <input type="text" name="username" required>

    <label>Password</label>
    <input type="password" name="password" required>

    <button type="submit">Register</button>
</form>

<p>
    Already have an account?
    <a href="{{ url_for('login') }}">Login</a>
</p>

{% endblock %}
"""

NOTES_TEMPLATE = """
{% extends "base" %}
{% block content %}

<div class="nav">
    <h1>My Notes</h1>
    <div>
        Hello, <strong>{{ username }}</strong> |
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>
</div>

<h2>New Note</h2>

<form method="POST" action="{{ url_for('add_note') }}">
    <input
        type="text"
        name="title"
        placeholder="Note title"
        required
    >

    <textarea
        name="content"
        placeholder="Write your note..."
        required
    ></textarea>

    <button type="submit">Add Note</button>
</form>

<hr>

<h2>Your Notes</h2>

{% if notes %}
    {% for note in notes %}
        <div class="note">

            <a
                class="delete"
                href="{{ url_for('delete_note', note_id=note['id']) }}"
                onclick="return confirm('Delete this note?')"
            >
                Delete
            </a>

            <h3>{{ note['title'] }}</h3>
            <p>{{ note['content'] }}</p>
            <small>{{ note['created_at'] }}</small>
        </div>
    {% endfor %}
{% else %}
    <p>You don't have any notes yet.</p>
{% endif %}

{% endblock %}
"""

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    notes = conn.execute(
        """
        SELECT *
        FROM notes
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template_string(
        NOTES_TEMPLATE,
        username=session["username"],
        notes=notes
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            return render_template_string(
                REGISTER_TEMPLATE,
                error="Username and password are required."
            )

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO users (username, password)
                VALUES (?, ?)
                """,
                (
                    username,
                    generate_password_hash(password)
                )
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()

            return render_template_string(
                REGISTER_TEMPLATE,

                error="Username already exists."
            )

        conn.close()

        return redirect(url_for("login"))

    return render_template_string(
        REGISTER_TEMPLATE,
        error=None
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("index"))

        return render_template_string(
            LOGIN_TEMPLATE,

            error="Invalid username or password."
        )

    return render_template_string(
        LOGIN_TEMPLATE,
        error=None
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/add-note", methods=["POST"])
def add_note():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"].strip()
    content = request.form["content"].strip()

    if title and content:
        conn = get_db()

        conn.execute(
            """
            INSERT INTO notes (user_id, title, content)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                title,
                content
            )
        )

        conn.commit()
        conn.close()

    return redirect(url_for("index"))

@app.route("/delete-note/<int:note_id>")
def delete_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM notes
        WHERE id = ?
        AND user_id = ?
        """,
        (
            note_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))

# Allow {% extends "base" %} to work with render_template_string
app.jinja_loader = type(
    "Loader",
    (),
    {
        "get_source": lambda self, environment, template:
            (BASE_HTML, None, lambda: True)
            if template == "base"
            else (_ for _ in ()).throw(Exception("Template not found"))
    }
)()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
