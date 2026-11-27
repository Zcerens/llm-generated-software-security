import os
import secrets
import sqlite3

from flask import (
    Flask,
    Response,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

# Production/staging:
#   FLASK_SECRET_KEY should be provided as an environment variable.
#
# Local development:
#   If FLASK_SECRET_KEY is missing, generate a random key.
#
# IMPORTANT:
# The fallback changes every time the application restarts.
# Therefore, users may be logged out after a restart.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY"
) or secrets.token_hex(32)


DATABASE = "notes.db"


# ============================================================
# DATABASE
# ============================================================

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
            filename TEXT,
            file_data BLOB,
            file_mimetype TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# INPUT HELPERS
# ============================================================

def parse_credentials(form):
    username = form.get("username", "").strip()
    password = form.get("password", "")

    return username, password


def parse_note_input(form):
    title = form.get("title", "").strip()
    content = form.get("content", "").strip()

    return title, content


def parse_search_query(args):
    return args.get("q", "").strip()


def handle_filename(filename):
    if not filename:
        return None

    filename = filename.strip()

    if not filename:
        return None

    return secure_filename(filename)


def handle_uploaded_file(uploaded_file):
    if not uploaded_file:
        return None, None, None

    if not uploaded_file.filename:
        return None, None, None

    filename = handle_filename(uploaded_file.filename)

    if not filename:
        return None, None, None

    file_data = uploaded_file.read()
    mimetype = uploaded_file.mimetype

    return filename, file_data, mimetype


# ============================================================
# AUTH HELPERS
# ============================================================

def is_logged_in():
    return "user_id" in session


def require_login():
    if not is_logged_in():
        return redirect(url_for("login"))

    return None


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Personal Notes</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 850px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
        }

        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,.08);
        }

        input,
        textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 10px;
            margin: 8px 0 15px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }

        textarea {
            height: 120px;
            resize: vertical;
        }

        button {
            background: #333;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            cursor: pointer;
        }

        button:hover {
            background: #555;
        }

        .nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .note {
            border: 1px solid #ddd;
            padding: 18px;
            margin: 15px 0;
            border-radius: 8px;
        }

        .delete {
            color: #c00;
            float: right;
        }

        .attachment {
            margin-top: 15px;
        }

        .error {
            color: #c00;
            margin-bottom: 15px;
        }

        hr {
            margin: 30px 0;
            border: 0;
            border-top: 1px solid #ddd;
        }
    </style>
</head>

<body>

<div class="container">

{% if page == "login" %}

    <h1>Login</h1>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    <form method="POST">

        <label>Username</label>

        <input
            type="text"
            name="username"
            required
        >

        <label>Password</label>

        <input
            type="password"
            name="password"
            required
        >

        <button type="submit">
            Login
        </button>

    </form>

    <p>
        Don't have an account?
        <a href="{{ url_for('register') }}">
            Register
        </a>
    </p>


{% elif page == "register" %}

    <h1>Register</h1>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    <form method="POST">

        <label>Username</label>

        <input
            type="text"
            name="username"
            required
        >

        <label>Password</label>

        <input
            type="password"
            name="password"
            required
        >

        <button type="submit">
            Register
        </button>

    </form>

    <p>
        Already have an account?
        <a href="{{ url_for('login') }}">
            Login
        </a>
    </p>


{% else %}

    <div class="nav">

        <h1>My Notes</h1>

        <div>
            Hello,
            <strong>{{ username }}</strong>
            |
            <a href="{{ url_for('logout') }}">
                Logout
            </a>
        </div>

    </div>

    <hr>

    <h2>Search Notes</h2>

    <form method="GET" action="{{ url_for('index') }}">

        <input
            type="text"
            name="q"
            placeholder="Search by title or content..."
            value="{{ keyword }}"
        >

        <button type="submit">
            Search
        </button>

        {% if keyword %}
            <a href="{{ url_for('index') }}">
                Clear
            </a>
        {% endif %}

    </form>

    <hr>

    <h2>Create Note</h2>

    <form
        method="POST"
        action="{{ url_for('create_note') }}"
        enctype="multipart/form-data"
    >

        <label>Title</label>

        <input
            type="text"
            name="title"
            placeholder="Note title"
            required
        >

        <label>Content</label>

        <textarea
            name="content"
            placeholder="Write your note..."
            required
        ></textarea>

        <label>Attachment</label>

        <input
            type="file"
            name="file"
        >

        <button type="submit">
            Create Note
        </button>

    </form>

    <hr>

    <h2>
        {% if keyword %}
            Search Results for "{{ keyword }}"
        {% else %}
            My Notes
        {% endif %}
    </h2>

    {% if notes %}

        {% for note in notes %}

            <div class="note">

                <a
                    class="delete"
                    href="{{ url_for(
                        'delete_note',
                        note_id=note['id']
                    ) }}"
                    onclick="return confirm('Delete this note?')"
                >
                    Delete
                </a>

                <h3>
                    {{ note['title'] }}
                </h3>

                <p>
                    {{ note['content'] }}
                </p>

                {% if note['filename'] %}

                    <div class="attachment">
                        📎
                        <a
                            href="{{ url_for(
                                'download_note_file',
                                note_id=note['id']
                            ) }}"
                        >
                            {{ note['filename'] }}
                        </a>
                    </div>

                {% endif %}

                <small>
                    Created:
                    {{ note['created_at'] }}
                </small>

            </div>

        {% endfor %}

    {% else %}

        {% if keyword %}
            <p>
                No notes found for "{{ keyword }}".
            </p>
        {% else %}
            <p>
                You don't have any notes yet.
            </p>
        {% endif %}

    {% endif %}

{% endif %}

</div>

</body>
</html>
"""


# ============================================================
# AUTH ROUTES
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username, password = parse_credentials(request.form)

        if not username or not password:
            return render_template_string(
                HTML,
                page="register",
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
                HTML,
                page="register",
                error="Username already exists."
            )

        conn.close()

        return redirect(url_for("login"))

    return render_template_string(
        HTML,
        page="register",
        error=None
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username, password = parse_credentials(request.form)

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

        if user and check_password_hash(
            user["password"],
            password
        ):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("index"))

        return render_template_string(
            HTML,
            page="login",
            error="Invalid username or password."
        )

    return render_template_string(
        HTML,
        page="login",
        error=None
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# NOTE ROUTES
# ============================================================

@app.route("/")
def index():

    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    keyword = parse_search_query(request.args)

    conn = get_db()

    if keyword:

        search_pattern = f"%{keyword}%"

        notes = conn.execute(
            """
            SELECT
                id,
                title,
                content,
                filename,
                created_at
            FROM notes
            WHERE user_id = ?
              AND (
                  title LIKE ?
                  OR content LIKE ?
              )
            ORDER BY created_at DESC
            """,
            (
                session["user_id"],
                search_pattern,
                search_pattern
            )
        ).fetchall()

    else:

        notes = conn.execute(
            """
            SELECT
                id,
                title,
                content,
                filename,
                created_at
            FROM notes
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

    conn.close()

    return render_template_string(
        HTML,
        page="notes",
        username=session["username"],
        notes=notes,
        keyword=keyword
    )


@app.route("/notes/create", methods=["POST"])
def create_note():

    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    title, content = parse_note_input(request.form)

    if not title or not content:
        return redirect(url_for("index"))

    uploaded_file = request.files.get("file")

    filename, file_data, file_mimetype = handle_uploaded_file(
        uploaded_file
    )

    conn = get_db()

    conn.execute(
        """
        INSERT INTO notes (
            user_id,
            title,
            content,
            filename,
            file_data,
            file_mimetype
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            title,
            content,
            filename,
            file_data,
            file_mimetype
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/notes/delete/<int:note_id>")
def delete_note(note_id):

    login_redirect = require_login()

    if login_redirect:
        return login_redirect

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


@app.route("/notes/<int:note_id>/download")
def download_note_file(note_id):

    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    conn = get_db()

    note = conn.execute(
        """
        SELECT
            filename,
            file_data,
            file_mimetype
        FROM notes
        WHERE id = ?
          AND user_id = ?
        """,
        (
            note_id,
            session["user_id"]
        )
    ).fetchone()

    conn.close()

    if not note or not note["file_data"]:
        return "File not found", 404

    response = Response(
        note["file_data"],
        mimetype=note["file_mimetype"]
        or "application/octet-stream"
    )

    response.headers["Content-Disposition"] = (
        f'attachment; filename="{note["filename"]}"'
    )

    return response


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    init_db()

    debug_enabled = os.environ.get(
        "FLASK_DEBUG",
        "0"
    ).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    app.run(debug=debug_enabled)
