import os
import time
import sqlite3
from urllib.parse import urlparse, urljoin
from flask import Flask, request, redirect, url_for, render_template, g, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date

from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

UPLOAD_FOLDER = 'static/profile_pics'
VIDEO_UPLOAD_FOLDER = 'static/career_videos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','pdf'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
DATABASE = 'career_guidance.db'

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'ab8ff1c3a4662502b0c67289d6317703c493208dfc78ab1d'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VIDEO_UPLOAD_FOLDER'] = VIDEO_UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


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
        self.id = f"{username}:{role}"
        self.username = username
        self.age = age
        self.skills = skills
        self.profile_pic = profile_pic
        self.role = role

    @staticmethod
    def get(user_id):
        if ':' not in user_id:
            return None
        username, role = user_id.split(':', 1)
        db = get_db()
        user_row = db.execute("SELECT * FROM users WHERE username = ? AND role = ?", (username, role)).fetchone()
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


def is_safe_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ('http', 'https') and host_url.netloc == redirect_url.netloc


def init_db():
    with app.app_context():
        db = get_db()
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
            is_vacant INTEGER DEFAULT 1,
            total_labour_vacancy INTEGER DEFAULT 0,
            posted_by TEXT,
            FOREIGN KEY(posted_by) REFERENCES admin_profiles(username)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS career_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            applicant_name TEXT NOT NULL,
            contact_info TEXT,
            resume_filename TEXT,
            FOREIGN KEY(job_id) REFERENCES career_options(id)
        )''')
        db.commit()


@app.route("/")
def home():
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            login_user(User(user['username'], user['password']))

            user_role = user['role']  # Direct access instead of .get()

            if user_role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')



@app.route('/logout')
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
        role = "job_seeker"

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
                    try:
                        file.save(file_path)
                        profile_pic_filename = filename
                    except Exception as e:
                        errors.append(f"Failed to save profile picture: {e}")
                else:
                    errors.append("Only image files (png, jpg, jpeg, gif) are allowed for profile pictures.")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(request.url)

        password = generate_password_hash(password_raw)
        db = get_db()
        try:
            existing = db.execute("SELECT 1 FROM users WHERE username = ? AND role = ?", (username, role)).fetchone()
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
            flash(f"An error occurred during registration: {e}", "error")
            return redirect(request.url)

    return render_template("register.html")

@app.route('/admin/update_vacancy/<int:job_id>/<int:status>')
def update_vacancy(job_id, status):
    db = get_db()
    db.execute("UPDATE career_options SET is_vacant = ? WHERE id = ?", (status, job_id))
    db.commit()
    flash(f"Updated vacancy status for job {job_id} to {status}", "success")
    return redirect(url_for('admin_dashboard'))




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
            existing = db.execute("SELECT 1 FROM users WHERE username = ? AND role = ?", (username, role)).fetchone()
            if existing:
                flash("Username already exists!", "error")
                return render_template("register_admin.html")

            db.execute("INSERT INTO users (username, password, age, profile_pic, role) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_password, age, profile_pic_filename, role))
            db.commit()
            flash("Admin registered successfully, please complete your profile.", "success")
            return redirect(url_for("admin_profile"))
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return render_template("register_admin.html")

    return render_template("register_admin.html")



@app.route("/admin_profile", methods=["GET", "POST"])
def admin_profile():
    db = get_db()

    if request.method == "POST":
        # WARNING: This allows updates without logged-in user!
        shop_name = request.form.get("shop_name", "").strip()
        labour_vacancy = request.form.get("labour_vacancy", "").strip()
        total_staff = request.form.get("total_staff", "").strip()
        location = request.form.get("location", "").strip()
        hand_based_salary = request.form.get("hand_based_salary", "").strip()
        incentives = request.form.get("incentives", "").strip()
        branches = request.form.get("branches", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        written_test = request.form.get("written_test", "").strip()

        # Using a fixed or default username because current_user.username is unavailable
        username = "default_admin"

        try:
            db.execute(
                '''INSERT OR REPLACE INTO admin_profiles
                   (username, shop_name, total_labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (username, shop_name, labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
            )
            db.commit()
            flash("Admin profile updated successfully.", "success")
            return redirect(url_for('post_job'))  # or admin_dashboard
        except Exception as e:
            db.rollback()
            flash(f"Error updating profile: {e}", "error")
            return render_template("admin_profile.html", profile=request.form)

    else:
        # Show profile for default/admin user
        profile = db.execute('SELECT * FROM admin_profiles WHERE username = ?', ("default_admin",)).fetchone()
        return render_template("admin_profile.html", profile=profile)


from flask_login import current_user

from flask import flash, render_template
from flask_login import current_user
from datetime import datetime  # You may need this elsewhere

@app.route("/admin_dashboard")
def admin_dashboard():
    db = get_db()
    # Use logged-in username or fallback to 'default_user'
    username = current_user.username if current_user.is_authenticated else "default_user"

    # Check if profile exists
    profile = db.execute("SELECT * FROM admin_profiles WHERE username = ?", (username,)).fetchone()

    # If profile does not exist, create a default one
    if profile is None:
        try:
            db.execute(
                '''INSERT INTO admin_profiles 
                   (username, shop_name, total_labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (username, "Default Shop", 0, 0, "Default Location", "", "", "", "", "")
            )
            db.commit()
            profile = db.execute("SELECT * FROM admin_profiles WHERE username = ?", (username,)).fetchone()
            flash("Default admin profile created.", "info")
        except Exception as e:
            db.rollback()
            flash(f"Failed to create default admin profile: {e}", "error")
            profile = None

    # Query jobs posted by this user
    query = """
        SELECT c.id, c.name, c.description, c.skills_required, c.is_vacant,
               (SELECT COUNT(*) FROM applications a WHERE a.job_id = c.id) AS applications_received,
               c.total_labour_vacancy
        FROM career_options c
        WHERE c.posted_by = ?
    """
    jobs = db.execute(query, (username,)).fetchall()

    return render_template("admin_dashboard.html", profile=profile, jobs=jobs)


from flask_login import current_user
from flask import flash, redirect, url_for, render_template, request

@app.route('/edit_admin_profile', methods=['GET', 'POST'])
def edit_admin_profile():
    db = get_db()

    # Safely get username whether authenticated or not
    username = current_user.username if current_user.is_authenticated else "default_user"

    if request.method == 'POST':
        shop_name = request.form.get('shop_name')
        total_labour_vacancy = request.form.get('total_labour_vacancy', type=int)
        total_staff = request.form.get('total_staff', type=int)
        location = request.form.get('location')
        hand_based_salary = request.form.get('hand_based_salary')
        incentives = request.form.get('incentives')
        branches = request.form.get('branches')
        contact_info = request.form.get('contact_info')
        written_test = request.form.get('written_test')

        try:
            db.execute('''UPDATE admin_profiles SET 
                shop_name = ?, total_labour_vacancy = ?, total_staff = ?, location = ?, 
                hand_based_salary = ?, incentives = ?, branches = ?, contact_info = ?, written_test = ?
                WHERE username = ?''',
                (shop_name, total_labour_vacancy, total_staff, location, hand_based_salary,
                 incentives, branches, contact_info, written_test, username)
            )
            db.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.rollback()
            flash(f'Failed to update profile: {e}', 'error')

    else:
        profile = db.execute('SELECT * FROM admin_profiles WHERE username = ?', (username,)).fetchone()
        return render_template('edit_admin_profile.html', profile=profile)

from datetime import datetime

from datetime import datetime
from flask import flash, redirect, url_for, render_template, request

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    db = get_db()

    # Get distinct skills for selection
    rows = db.execute(
        "SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''"
    ).fetchall()
    skills_set = set()
    for row in rows:
        for skill in row['skills_required'].split(','):
            skill = skill.strip()
            if skill:
                skills_set.add(skill)
    available_skills = sorted(skills_set)

    if request.method == "POST":
        # Get form data
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        learn_more = request.form.get("learn_more", "").strip()
        skills_required = request.form.get("skills_required", "").strip()
        application_form_url = request.form.get("application_form_url", "").strip()
        total_labour_vacancy = request.form.get("total_labour_vacancy", 0, type=int)

        # Temporary workaround: use fixed poster username since login is disabled
        posted_by = "default_user"

        # Validations
        if not name or not description:
            flash("Job name and description are required.", "error")
            return render_template("post_job.html", available_skills=available_skills)

        if application_form_url and not (
            application_form_url.startswith("http://") or application_form_url.startswith("https://")
        ):
            flash("Application Form URL must start with http:// or https://", "error")
            return render_template("post_job.html", available_skills=available_skills)

        posted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert job into DB
        try:
            db.execute(
                '''INSERT INTO career_options
                   (name, description, learn_more, skills_required, application_form_url, 
                    is_vacant, total_labour_vacancy, posted_by, posted_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    name, description, learn_more, skills_required, application_form_url,
                    1, total_labour_vacancy, posted_by, posted_date
                )
            )
            db.commit()
            flash("Job posted successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"Failed to post job: {e}", "error")

    # Render form with available skills on GET or after errors
    return render_template("post_job.html", available_skills=available_skills)


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM career_options WHERE id = ? AND is_vacant = 1", (job_id,)).fetchone()
    if not job:
        flash("Job not found or not vacant.", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        applicant_name = current_user.username
        contact_info = request.form.get("contact_info", "").strip()
        resume_file = request.files.get("resume")

        resume_filename = None
        if resume_file and resume_file.filename != '':
            if allowed_file(resume_file.filename):
                filename = f"{int(time.time())}_{secure_filename(resume_file.filename)}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    resume_file.save(file_path)
                    resume_filename = filename
                except Exception as e:
                    flash("Failed to save resume file.", "error")
                    return redirect(request.url)
            else:
                flash("Only image (png, jpg, jpeg, gif) and pdf files are allowed for resume.", "error")
                return redirect(request.url)

        try:
            # Insert application into DB
            db.execute(
                '''INSERT INTO applications (job_id, applicant_name, contact_info, resume_filename)
                   VALUES (?, ?, ?, ?)''',
                (job_id, applicant_name, contact_info, resume_filename)
            )

            # Update user skills by merging with job skills
            user_skills = set(current_user.skills.split(',')) if current_user.skills else set()
            job_skills = set([skill.strip() for skill in job['skills_required'].split(',')])
            updated_skills = ','.join(sorted(user_skills.union(job_skills)))

            db.execute(
                "UPDATE users SET skills = ? WHERE username = ?",
                (updated_skills, current_user.username)
            )

            # Commit all DB changes
            db.commit()

            # Update vacancy after application (your existing function)
            update_vacancy_status(job_id)

            flash("Application submitted successfully.", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.rollback()
            flash(f"Failed to submit application: {e}", "error")
            return redirect(request.url)

    # Prepare preferred location list on GET
    preferred_locations = []
    if job['posted_by']:
        admin_profile = db.execute("SELECT location FROM admin_profiles WHERE username = ?", (job['posted_by'],)).fetchone()
        if admin_profile and admin_profile['location']:
            preferred_locations = [loc.strip() for loc in admin_profile['location'].split(',') if loc.strip()]
            preferred_locations.sort()

    return render_template('apply.html', job=job, preferred_locations=preferred_locations)


def update_vacancy_status(job_id):
    db = get_db()
    job = db.execute('''SELECT total_labour_vacancy FROM career_options WHERE id = ?''', (job_id,)).fetchone()

    if not job:
        return False

    try:
        apps_count = db.execute('SELECT COUNT(*) FROM applications WHERE job_id = ?', (job_id,)).fetchone()[0]
        if apps_count >= job['total_labour_vacancy']:
            db.execute('UPDATE career_options SET is_vacant = 0 WHERE id = ?', (job_id,))
            db.commit()
            return True
        else:
            db.execute('UPDATE career_options SET is_vacant = 1 WHERE id = ?', (job_id,))
            db.commit()
            return True
    except Exception:
        return False


from flask_login import current_user
from flask import abort

@app.route('/admin_dashboard/applications/<int:job_id>')
def view_applications(job_id):
    db = get_db()

    username = current_user.username if current_user.is_authenticated else "default_user"

    # Check if job exists and belongs to current admin
    job = db.execute("SELECT * FROM career_options WHERE id = ? AND posted_by = ?", (job_id, username)).fetchone()
    if not job:
        abort(404)

    # Get all applications for this job
    applications = db.execute(
        "SELECT id, applicant_name, contact_info, resume_filename FROM applications WHERE job_id = ?",
        (job_id,)
    ).fetchall()

    return render_template("applications.html", job=job, applications=applications)

@app.route('/resumes/<filename>')
def uploaded_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/debug_jobs')
def debug_jobs():
    db = get_db()
    jobs = db.execute('''SELECT c.id, c.name, c.description, c.skills_required, c.is_vacant,
                         c.total_labour_vacancy, c.posted_by FROM career_options c''').fetchall()
    return '<br>'.join([str(dict(job)) for job in jobs])


@app.route('/career_videos')
def view_videos():
    db = get_db()
    videos = db.execute('SELECT * FROM career_videos ORDER BY upload_date DESC').fetchall()

    if current_user.is_authenticated:
        skills_str = getattr(current_user, 'skills', '') or ''
        user_skills = [skill.strip().lower() for skill in skills_str.split(',') if skill.strip()]
    else:
        user_skills = []

    return render_template('career_videos.html', videos=videos, user_skills=user_skills)
from flask import render_template, g
from flask_login import current_user

@app.route("/dashboard")
def dashboard():
    # Check if user is authenticated and extract information safely
    user = current_user if hasattr(current_user, "is_authenticated") and current_user.is_authenticated else None

    user_skills_list = []
    username = None
    if user and hasattr(user, "skills"):
        skills_str = getattr(user, "skills", "") or ""
        user_skills_list = [s.strip().lower() for s in skills_str.split(",") if s.strip()]
        username = getattr(user, "username", None)

    db = get_db()

    # Jobs matching user's skills (will be empty for guests)
    query = """
        SELECT c.*, ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
        WHERE c.is_vacant = 1
    """
    career_options_db = db.execute(query).fetchall()

    relevant_jobs = []
    for job in career_options_db:
        job_skills_list = [s.strip().lower() for s in (job["skills_required"] or "").split(",") if s.strip()]
        if user_skills_list and any(user_skill in job_skills_list for user_skill in user_skills_list):
            relevant_jobs.append(job)

    # Fetch jobs user applied for, only if user is logged in
    applied_jobs_list = []
    if username:
        applied_jobs = db.execute(
            """
            SELECT c.id, c.name, COUNT(a.id) as application_count
            FROM applications a
            JOIN career_options c ON a.job_id = c.id
            WHERE a.applicant_name = ?
            GROUP BY c.id, c.name
            """,
            (username,)
        ).fetchall()
        applied_jobs_list = [dict(row) for row in applied_jobs]

    return render_template("dashboard.html", user=user, jobs=relevant_jobs, applied_jobs=applied_jobs_list)





@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sender_email = request.form.get('email', '').strip()
        message_body = request.form.get('message', '').strip()

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


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if not current_user.is_authenticated:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for("login"))

    db = get_db()
    user_row = db.execute(
        "SELECT username, age, skills, profile_pic FROM users WHERE username = ? AND role = ?",
        (current_user.username, current_user.role)
    ).fetchone()

    if not user_row:
        flash("User profile not found. Please log in again.", "error")
        logout_user()
        return redirect(url_for("login"))

    rows = db.execute(
        "SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''"
    ).fetchall()
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
            return render_template(
                "edit_profile.html",
                user=user_row,
                current_skills=current_skills_for_template,
                available_skills=available_skills,
            )

        current_profile_pic_filename = user_row['profile_pic']
        profile_pic_filename_to_save = current_profile_pic_filename
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '' and allowed_file(file.filename):
                if current_profile_pic_filename and current_profile_pic_filename != file.filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_profile_pic_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                profile_pic_filename_to_save = filename
            elif file.filename != '':
                flash("Only image (png, jpg, jpeg, gif) files are allowed for profile picture.", "error")
                current_skills_for_template = user_row["skills"].split(",") if user_row and user_row["skills"] else []
                return render_template(
                    "edit_profile.html",
                    user=user_row,
                    current_skills=current_skills_for_template,
                    available_skills=available_skills,
                )

        try:
            db.execute(
                "UPDATE users SET age = ?, skills = ?, profile_pic = ? WHERE username = ? AND role = ?",
                (new_age, new_skills_str, profile_pic_filename_to_save, current_user.username, current_user.role)
            )
            db.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while updating profile: {e}", "error")

    current_skills_for_template = user_row["skills"].split(",") if user_row and user_row["skills"] else []
    return render_template(
        "edit_profile.html",
        user=user_row,
        current_skills=current_skills_for_template,
        available_skills=available_skills,
    )
@app.route('/career_options')
def career_options():
    db = get_db()
    search_query = request.args.get('query', '').strip().lower()

    base_query = """
        SELECT c.id, c.name, c.description, c.skills_required, c.is_vacant,
               c.total_labour_vacancy, c.learn_more, c.application_form_url,
               ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
        WHERE c.is_vacant = 1
    """

    params = []

    if search_query:
        base_query += " AND (LOWER(c.name) LIKE ? OR LOWER(c.skills_required) LIKE ? OR LOWER(c.description) LIKE ?)"
        like_pattern = f"%{search_query}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    base_query += " ORDER BY c.is_vacant DESC, c.name ASC"

    jobs = db.execute(base_query, params).fetchall()

    # Example available_skills dict to link skills to URLs (empty here, replace as needed)
    available_skills = {}

    return render_template('career_options.html', jobs=jobs, available_skills=available_skills, search_query=search_query)

@app.route('/career_interests', methods=['GET', 'POST'])
def career_interests():
    if not current_user.is_authenticated:
        flash("Please log in to select your career interests.", "error")
        return redirect(url_for("login"))

    db = get_db()

    # Fetch all distinct skills from career_options for user to select
    rows = db.execute(
        "SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''"
    ).fetchall()

    skills_set = set()
    for row in rows:
        skills_in_row = [skill.strip() for skill in row['skills_required'].split(',')]
        skills_set.update(skills_in_row)
    available_skills = sorted(skills_set)

    if request.method == 'POST':
        selected_skills = request.form.getlist("skills")  # list of selected skills
        skills_str = ",".join(selected_skills).strip()

        try:
            db.execute(
                "UPDATE users SET skills = ? WHERE username = ? AND role = ?",
                (skills_str, current_user.username, current_user.role),
            )
            db.commit()
            flash("Career interests updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Failed to update career interests: {e}", "error")
            return redirect(url_for("career_interests"))

    # For GET: fetch the user's current skills to pre-check checkboxes
    user_row = db.execute(
        "SELECT skills FROM users WHERE username = ? AND role = ?",
        (current_user.username, current_user.role),
    ).fetchone()

    if user_row and user_row["skills"]:
        user_skills = user_row["skills"].split(",")
    else:
        user_skills = available_skills  # preselect all skills for new users

    return render_template(
        "career_interests.html",
        available_skills=available_skills,
        user_skills=user_skills,
    )

    from datetime import date

@app.route('/todays_jobs')
def todays_jobs():
    db = get_db()
    today = date.today().isoformat()  # 'YYYY-MM-DD'
    query = """
        SELECT c.id, c.name, c.description, c.skills_required, c.is_vacant,
               c.total_labour_vacancy, c.learn_more, c.application_form_url,
               ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
        WHERE c.is_vacant = 1 AND DATE(c.posted_date) = ?
        ORDER BY c.name ASC
    """
    jobs = db.execute(query, (today,)).fetchall()
    return render_template('todays_jobs.html', jobs=jobs)



    
    
    


@app.route('/terms/<int:job_id>')
def terms(job_id):
    # optionally use job_id to customize terms, or ignore it
    return render_template('terms.html', job_id=job_id)



@app.route('/migrate_posted_date')
def migrate_posted_date():
    db = get_db()
    try:
        # Step 1: Add column without default
        db.execute("ALTER TABLE career_options ADD COLUMN posted_date DATETIME;")
        # Step 2: Update existing rows
        db.execute("UPDATE career_options SET posted_date = CURRENT_TIMESTAMP WHERE posted_date IS NULL;")
        db.commit()
        return "Migration success: 'posted_date' column added and populated."
    except Exception as e:
        return f"Migration failed: {e}"

@app.route('/fix_posted_date_nulls')
def fix_posted_date_nulls():
    db = get_db()
    try:
        db.execute("UPDATE career_options SET posted_date = CURRENT_TIMESTAMP WHERE posted_date IS NULL;")
        db.commit()
        return "Null posted_date fields fixed."
    except Exception as e:
        return f"Failed to fix posted_date: {e}"


@app.route('/admin_dashboard/applications')
def view_all_applications():
    db = get_db()
    username = current_user.username if current_user.is_authenticated else "default_user"

    query = """
        SELECT a.id, a.applicant_name, a.contact_info, a.resume_filename, c.id AS job_id, c.name AS job_name
        FROM applications a
        JOIN career_options c ON a.job_id = c.id
        WHERE c.posted_by = ?
        ORDER BY c.name, a.applicant_name
    """

    applications = db.execute(query, (username,)).fetchall()
    return render_template('all_applications.html', applications=applications)




if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['VIDEO_UPLOAD_FOLDER']):
        os.makedirs(app.config['VIDEO_UPLOAD_FOLDER'])
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
