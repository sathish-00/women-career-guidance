import os
import sqlite3
from add_row_column import migrate_add_role_column, migrate_add_career_columns

from functools import wraps

from flask import Flask, request, redirect, url_for, render_template, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'career_guidance.db'

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'ab8ff1c3a4662502b0c67289d6317703c493208dfc78ab1d'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Where to redirect for login


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()


class User(UserMixin):
    def __init__(self, username, age=None, skills=None, profile_pic=None, role='job_seeker'):
        # Use composite id to uniquely identify user with role included
        self.id = f"{username}:{role}"
        self.username = username
        self.age = age
        self.skills = skills
        self.profile_pic = profile_pic
        self.role = role

    @staticmethod
    def get(user_id):
        # Parse composite id
        if ':' not in user_id:
            return None
        username, role = user_id.split(':', 1)
        db = get_db()
        user_row = db.execute(
            "SELECT * FROM users WHERE username = ? AND role = ?",
            (username, role)
        ).fetchone()
        if not user_row:
            return None
        return User(
            username=user_row['username'],
            age=user_row['age'],
            skills=user_row['skills'],
            profile_pic=user_row['profile_pic'],
            role=user_row['role']
        )


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin access required.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def init_db():
    with app.app_context():
        db = get_db()
        # Drop old table for development (optional, handle carefully in production)
        # db.execute("DROP TABLE IF EXISTS users")
        # Create users table with composite primary key (username, role)
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            profile_pic TEXT,
            skills TEXT,
            role TEXT NOT NULL DEFAULT 'job_seeker',
            PRIMARY KEY (username, role)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS admin_profiles (
            username TEXT PRIMARY KEY,
            shop_name TEXT,
            total_labour_vacancy INTEGER,
            total_staff INTEGER,
            location TEXT,
            hand_based_salary TEXT,
            incentives TEXT,
            branches TEXT,
            contact_info TEXT,
            written_test TEXT,
            FOREIGN KEY(username) REFERENCES users(username)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS career_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            learn_more TEXT NOT NULL,
            skills_required TEXT,
            application_form_url TEXT,
            is_vacant INTEGER,
            posted_by TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()


@app.route("/")
def home():
    return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form.get('role', 'job_seeker')  # Role must be provided by the login form (e.g. dropdown)
        password = request.form['password']
        db = get_db()
        user_row = db.execute(
            "SELECT * FROM users WHERE username = ? AND role = ?",
            (username, role)
        ).fetchone()
        if user_row and check_password_hash(user_row['password'], password):
            user_obj = User.get(f"{username}:{role}")
            login_user(user_obj)
            flash("Logged in successfully!", "success")
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash("Invalid username, role, or password", "error")
    return render_template("login.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password_raw = request.form.get("password", "")
        age_raw = request.form.get("age", "").strip()
        profile_pic_filename = None
        role = "job_seeker"  # registration for job seekers

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password_raw:
            errors.append("Password is required.")
        elif len(password_raw) < 8:
            errors.append("Password must be at least 8 characters long.")
        try:
            age = int(age_raw)
            if age < 0:
                errors.append("Age must be a non-negative number.")
        except ValueError:
            errors.append("A valid age number is required.")

        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    profile_pic_filename = filename
                else:
                    errors.append("Only image files (png, jpg, jpeg, gif) are allowed for profile pictures.")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(request.url)

        password = generate_password_hash(password_raw)
        db = get_db()
        try:
            # Check username+role uniqueness before inserting
            existing = db.execute(
                "SELECT 1 FROM users WHERE username = ? AND role = ?",
                (username, role)
            ).fetchone()
            if existing:
                flash("Username already exists! Please choose another.", "error")
                return redirect(request.url)

            db.execute(
                "INSERT INTO users (username, password, age, profile_pic, role) VALUES (?, ?, ?, ?, ?)",
                (username, password, age, profile_pic_filename, role)
            )
            db.commit()

            user_obj = User.get(f"{username}:{role}")
            login_user(user_obj)

            flash("Registration successful! Please select your skills to personalize your experience.", "success")
            return redirect(url_for("career_interests"))

        except Exception as e:
            db.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(request.url)

    return render_template("register.html")


@app.route("/register_admin", methods=["GET", "POST"])
def register_admin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        age_raw = request.form.get("age", "").strip()
        profile_pic_file = request.files.get('profile_pic')
        role = "admin"

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password or not confirm_password:
            errors.append("Password and confirmation are required.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        try:
            age = int(age_raw)
            if age <= 21:
                errors.append("Admins must be older than 21.")
        except ValueError:
            errors.append("Valid age is required.")

        profile_pic_filename = None
        if profile_pic_file and profile_pic_file.filename != '':
            if allowed_file(profile_pic_file.filename):
                filename = secure_filename(profile_pic_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic_file.save(file_path)
                profile_pic_filename = filename
            else:
                errors.append("Profile picture must be an image file (png, jpg, jpeg, gif).")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register_admin.html")

        hashed_password = generate_password_hash(password)
        db = get_db()
        try:
            # Check username+role uniqueness before inserting
            existing = db.execute(
                "SELECT 1 FROM users WHERE username = ? AND role = ?",
                (username, role)
            ).fetchone()
            if existing:
                flash("Username already exists!", "error")
                return render_template("register_admin.html")

            db.execute(
                "INSERT INTO users (username, password, age, profile_pic, role) VALUES (?, ?, ?, ?, ?)",
                (username, hashed_password, age, profile_pic_filename, role)
            )
            db.commit()
            flash("Admin registered successfully, please complete your profile.", "success")
            return redirect(url_for("admin_profile"))
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return render_template("register_admin.html")

    return render_template("register_admin.html")


@app.route("/admin_profile", methods=["GET", "POST"])
@admin_required
def admin_profile():
    if request.method == "POST":
        shop_name = request.form.get("shop_name", "").strip()
        labour_vacancy = request.form.get("labour_vacancy", "").strip()
        total_staff = request.form.get("total_staff", "").strip()
        location = request.form.get("location", "").strip()
        hand_based_salary = request.form.get("hand_based_salary", "").strip()
        incentives = request.form.get("incentives", "").strip()
        branches = request.form.get("branches", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        written_test = request.form.get("written_test", "").strip()

        db = get_db()
        try:
            db.execute(
                '''INSERT OR REPLACE INTO admin_profiles
                   (username, shop_name, total_labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (current_user.username, shop_name, labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
            )
            db.commit()
            flash("Admin profile updated successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"Error updating profile: {e}", "error")

    return render_template("admin_profile.html")


@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    jobs = db.execute("SELECT * FROM career_options").fetchall()
    return render_template("admin_dashboard.html", jobs=jobs)


@app.route("/admin/post_job", methods=["GET", "POST"])
@admin_required
def post_job():
    db = get_db()

    rows = db.execute("SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''").fetchall()
    skills_set = set()
    for row in rows:
        for skill in row['skills_required'].split(','):
            skill = skill.strip()
            if skill:
                skills_set.add(skill)
    available_skills = sorted(skills_set)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        learn_more = request.form.get("learn_more", "").strip()
        skills_required = request.form.get("skills_required", "").strip()
        application_form_url = request.form.get("application_form_url", "").strip()
        is_vacant = 1

        if not name or not description:
            flash("Job name and description are required.", "error")
            return render_template("post_job.html", available_skills=available_skills)

        if application_form_url and not (application_form_url.startswith("http://") or application_form_url.startswith("https://")):
            flash("Application Form URL must start with http:// or https://", "error")
            return render_template("post_job.html", available_skills=available_skills)

        try:
            db.execute(
                '''INSERT INTO career_options
                   (name, description, learn_more, skills_required, application_form_url, is_vacant, posted_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (name, description, learn_more, skills_required, application_form_url, is_vacant, current_user.username)
            )
            db.commit()
            flash("Job posted successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"Failed to post job: {e}", "error")

    return render_template("post_job.html", available_skills=available_skills)


@app.route('/career_interests', methods=['GET', 'POST'])
@login_required
def career_interests():
    username = current_user.username
    db = get_db()

    rows = db.execute("SELECT skills_required FROM career_options").fetchall()
    skill_set = set()
    for row in rows:
        if row['skills_required']:
            skills = [skill.strip() for skill in row['skills_required'].split(',') if skill.strip()]
            skill_set.update(skills)

    dynamic_skills = {skill: {"description": "Skill required for job postings", "reference": "#"} for skill in skill_set}

    if request.method == 'POST':
        selected_skills = request.form.getlist('skills')
        skills_str = ",".join(selected_skills)
        try:
            db.execute("UPDATE users SET skills = ? WHERE username = ? AND role = ?", (skills_str, username, current_user.role))
            db.commit()
            flash("Skills updated successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.rollback()
            flash(f"Failed to update skills: {e}", "error")

    current_skills = []
    user_row = db.execute("SELECT skills FROM users WHERE username = ? AND role = ?", (username, current_user.role)).fetchone()
    if user_row and user_row['skills']:
        current_skills = [s.strip() for s in user_row['skills'].split(',') if s.strip()]
    return render_template('career_interests.html', available_skills=dynamic_skills, current_skills=current_skills)


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user

    user_skills_list = [s.strip().lower() for s in (getattr(user, 'skills', '') or "").split(',') if s.strip()]
    db = get_db()

    query = """
        SELECT c.*, a.shop_name, a.location, a.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles a ON c.posted_by = a.username
        WHERE c.is_vacant = 1
    """
    career_options_db = db.execute(query).fetchall()

    relevant_jobs = []
    for job in career_options_db:
        job_skills_list = [s.strip().lower() for s in (job['skills_required'] or "").split(',') if s.strip()]
        if any(user_skill in job_skills_list for user_skill in user_skills_list):
            relevant_jobs.append(job)

    return render_template("dashboard.html", user=user, jobs=relevant_jobs)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    db = get_db()
    user_row = db.execute("SELECT username, age, skills, profile_pic FROM users WHERE username = ? AND role = ?", (current_user.username, current_user.role)).fetchone()
    if not user_row:
        flash("User profile not found. Please log in again.", "error")
        logout_user()
        return redirect(url_for("login"))

    rows = db.execute("SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''").fetchall()
    skills_set = set()
    for row in rows:
        skills_set.update([skill.strip() for skill in row['skills_required'].split(',')])
    available_skills = sorted(skills_set)

    if request.method == "POST":
        new_age = request.form.get("age", type=int)
        new_skills_list = request.form.getlist("skills")
        new_skills_str = ",".join(new_skills_list)

        if new_age is None or new_age < 0:
            flash("Age must be a non-negative number.", "error")
            current_skills_for_template = user_row["skills"].split(",") if user_row and user_row["skills"] else []
            return render_template("edit_profile.html", user=user_row, current_skills=current_skills_for_template, available_skills=available_skills)

        current_profile_pic_filename = user_row['profile_pic']
        profile_pic_filename_to_save = current_profile_pic_filename
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '' and allowed_file(file.filename):
                if current_profile_pic_filename and current_profile_pic_filename != file.filename:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_profile_pic_filename)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                profile_pic_filename_to_save = filename
            elif file.filename != '':
                flash("Only image (png, jpg, jpeg, gif) files are allowed for profile picture.", "error")
                current_skills_for_template = user_row["skills"].split(",") if user_row and user_row["skills"] else []
                return render_template("edit_profile.html", user=user_row, current_skills=current_skills_for_template, available_skills=available_skills)

        try:
            db.execute("UPDATE users SET age = ?, skills = ?, profile_pic = ? WHERE username = ? AND role = ?", (new_age, new_skills_str, profile_pic_filename_to_save, current_user.username, current_user.role))
            db.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while updating profile: {e}", "error")

    current_skills_for_template = user_row["skills"].split(",") if user_row and user_row["skills"] else []
    return render_template("edit_profile.html", user=user_row, current_skills=current_skills_for_template, available_skills=available_skills)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        sender_email = request.form.get('email')
        message_body = request.form.get('message')

        if not name or not sender_email or not message_body:
            flash("All fields are required. Please fill out the form completely.", "error")
            return redirect(url_for('contact'))

        try:
            db = get_db()
            db.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)", (name, sender_email, message_body))
            db.commit()
            flash("Your message has been saved. We'll get back to you soon!", "success")
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f"Failed to save message. Error: {e}", "error")
            return render_template('contact.html')

    return render_template('contact.html')


@app.route('/admin/contact_messages')
@admin_required
def view_contact_messages():
    db = get_db()
    messages = db.execute("SELECT * FROM contact_messages ORDER BY timestamp DESC").fetchall()
    return render_template('admin_contact.html', messages=messages)


@app.route('/career_options')
def career_options():
    db = get_db()
    careers = db.execute("SELECT * FROM career_options WHERE is_vacant = 1").fetchall()
    return render_template('career_options.html', careers=careers)


@app.route('/career_videos')
def career_videos():
    username = None
    user_skills = []

    if current_user.is_authenticated:
        username = current_user.username
        db = get_db()
        user_row = db.execute("SELECT skills FROM users WHERE username = ? AND role = ?", (username, current_user.role)).fetchone()
        if user_row and user_row['skills']:
            user_skills = [s.strip().lower() for s in user_row['skills'].split(',') if s.strip()]

    videos = [
        {"title": "How to prepare for jobs", "url": "https://www.youtube.com/embed/somevideoid", "skills": ["python", "java"]},
        {"title": "Career guidance tips", "url": "https://www.youtube.com/embed/anothervideoid", "skills": ["html", "css"]},
    ]

    return render_template('career_videos.html', videos=videos, user_skills=user_skills)


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    with app.app_context():
        init_db()
        migrate_add_role_column()
        migrate_add_career_columns()
    app.run(host='0.0.0.0', port=5000, debug=True)
