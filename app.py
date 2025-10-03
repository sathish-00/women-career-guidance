# app.py (Full Code with Automatic Status Logic Removed)

import os
import time
import sqlite3
from urllib.parse import urlparse, urljoin
from flask import Flask, request, redirect, url_for, render_template, g, flash, abort, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date, datetime
from functools import wraps

import requests # <-- ADD THIS IMPORT


from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from googleapiclient.discovery import build # For YouTube API

from add_row_column import migrate_add_role_column, migrate_add_career_columns

# app.py (Near the top)
# ...
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from googleapiclient.discovery import build # For YouTube API

from add_row_column import migrate_add_role_column, migrate_add_career_columns
from security_migrations import migrate_add_security_columns 
# ...       


# --- GLOBAL CONSTANTS ---
UPLOAD_FOLDER = 'static/profile_pics'
VIDEO_UPLOAD_FOLDER = 'static/career_videos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','pdf'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
DATABASE = 'career_guidance.db'

# --- 1. FLASK APP CREATION AND CONFIGURATION ---
app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'ab8ff1c3a4662502b0c67289d6317703c493208dfc78ab1d'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VIDEO_UPLOAD_FOLDER'] = VIDEO_UPLOAD_FOLDER
app.config['RECAPTCHA_SITE_KEY'] = '6LdoFdkrAAAAALeNBLUV_gK59KDusy3jR3uRxJLC'
app.config['RECAPTCHA_SECRET_KEY'] = '6LdoFdkrAAAAAFnLLaGiiKo95rn1xzmyq3tPDkoI'

# --- RECAPTCHA CONFIGURATION (Using your provided keys) ---
# Your Site Key (Public key for the HTML widget)


# Initialize ReCaptcha


# Load API Key variables securely from .env file
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', 'AIzaSyC8hIIBnhqDhjIBZHoKGfLZP6_V0cDAefQ')


# --- 3. FLASK-LOGIN SETUP ---
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
            posted_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS career_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            video_tags TEXT 
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
            user_id TEXT NOT NULL,
            applicant_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            dob TEXT,
            address TEXT,
            pincode TEXT,
            applicant_email TEXT,
            applicant_phone TEXT,
            experience TEXT,
            skills_applied TEXT,
            preferred_location TEXT,
            resume_filename TEXT,
            FOREIGN KEY(job_id) REFERENCES career_options(id)
        )''')
        db.commit()


# --- New Vacancy Status Function ---
def get_vacancy_status(username):
    """Calculates total, posted, and remaining vacancies for a given admin."""
    db = get_db()
    
    profile = db.execute(
        "SELECT total_labour_vacancy FROM admin_profiles WHERE username = ?", 
        (username,)
    ).fetchone()
    
    vacancy_limit = profile['total_labour_vacancy'] if profile and profile['total_labour_vacancy'] is not None else 0
    
    posted_vacancies_row = db.execute(
        "SELECT SUM(total_labour_vacancy) FROM career_options WHERE posted_by = ?",
        (username,)
    ).fetchone()
    
    posted_vacancies_sum = posted_vacancies_row[0] if posted_vacancies_row and posted_vacancies_row[0] is not None else 0

    remaining_capacity = max(0, vacancy_limit - posted_vacancies_sum)
    
    return {
        'limit': vacancy_limit, 
        'posted': posted_vacancies_sum, 
        'remaining_post_capacity': remaining_capacity,
        'can_post': remaining_capacity > 0 
    }
# ------------------------------------
def verify_recaptcha(response_token):
    """Verifies the CAPTCHA token with Google."""
    SECRET_KEY = app.config.get('RECAPTCHA_SECRET_KEY')
    
    if not SECRET_KEY:
        print("ERROR: RECAPTCHA_SECRET_KEY not configured!")
        return False
        
    payload = {
        'secret': SECRET_KEY,
        'response': response_token
    }
    
    # Send verification request to Google
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify', 
        data=payload
    )
    
    result = response.json()
    
    # Returns True if verification was successful
    return result.get('success', False)
# --------------------------------------------------------------------


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
            # Pass user details (including role) to the Flask-Login User object
            login_user(User(
                username=user['username'], 
                age=user['age'], 
                skills=user['skills'], 
                profile_pic=user['profile_pic'], 
                role=user['role']
            ))

            user_role = user['role']

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

# Assuming:
# 1. 'from flask_recaptcha import ReCaptcha' is imported at the top.
# 2. ReCaptcha is initialized globally: recaptcha = ReCaptcha(app)
# 3. Your SITE_KEY and SECRET_KEY are configured: 
#    app.config['RECAPTCHA_SITE_KEY'] = '6LfjzNgrAAAAAHVtQet4nUzmfpTLr_GKfHEsW1Tp'
#    app.config['RECAPTCHA_SECRET_KEY'] = '6LfjzNgrAAAAAC3zoJZ8EvWer8I-yoYOTwyc4vPh' 

# app.py (The complete, corrected register route)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if 'terms_agree' not in request.form:
            flash('You must agree to the Terms and Conditions to register.', 'error')
            return redirect(url_for('register'))

        
        # --- CAPTCHA Verification (Placeholder) ---
        # Assuming verify_recaptcha() is called here if you are using manual CAPTCHA
        # Example:
        # recaptcha_response = request.form.get('g-recaptcha-response')
        # if not recaptcha_response or not verify_recaptcha(recaptcha_response):
        #     flash("CAPTCHA verification failed. Please try again.", "error")
        #     return redirect(request.url)
        # -------------------------------------------
        
        username = request.form.get("username", "").strip()
        password_raw = request.form.get("password", "")
        age_raw = request.form.get("age", "").strip()
        profile_pic_filename = None
        role = "job_seeker"
        
        # --- FIX: Initialize 'age' variable to prevent UnboundLocalError if validation fails ---
        age = None 
        
        security_question = request.form.get("security_question", "").strip()
        security_answer = request.form.get("security_answer", "").strip()

        errors = []
        
        # 1. Standard Validation
        if not username:
            errors.append("Username is required.")
        if not password_raw:
            errors.append("Password is required.")
        elif len(password_raw) < 8:
            errors.append("Password must be at least 8 characters long.")
            
        # 2. Age Validation (Restored and Corrected)
        try:
            age = int(age_raw)
            if age < 0:
                errors.append("Age must be a non-negative number.")
        except ValueError:
            errors.append("A valid age number is required.")
        
        # 3. Security Fields Validation
        if not security_question or not security_answer:
            errors.append("Security Question and Answer are required for password recovery.")
            
        # 4. File Upload Validation
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

        # Execution continues only if no errors were found
        password = generate_password_hash(password_raw)
        db = get_db()
        try:
            existing = db.execute("SELECT 1 FROM users WHERE username = ? AND role = ?", (username, role)).fetchone()
            if existing:
                flash("Username already exists! Please choose another.", "error")
                return redirect(request.url)

            # --- INSERT Query (Includes all 7 fields) ---
            db.execute(
                """
                INSERT INTO users 
                (username, password, age, profile_pic, role, security_question, security_answer) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (username, password, age, profile_pic_filename, role, security_question, security_answer)
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
@admin_required
def update_vacancy(job_id, status):
    db = get_db()
    
    job_check = db.execute("SELECT posted_by FROM career_options WHERE id = ?", (job_id,)).fetchone()
    if not job_check or job_check['posted_by'] != current_user.username:
        flash("Unauthorized action.", "error")
        return redirect(url_for('admin_dashboard'))
    
    # This manual action is the ONLY way the vacancy status is changed.
    db.execute("UPDATE career_options SET is_vacant = ? WHERE id = ?", (status, job_id))
    db.commit()
    flash(f"Updated vacancy status for job {job_id} to {'Vacant' if status == 1 else 'Closed'}.", "success")
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
                try:
                    profile_pic_file.save(file_path)
                    profile_pic_filename = filename
                except Exception as e:
                    errors.append(f"Failed to save profile picture: {e}")
            else:
                errors.append("Profile picture must be an image file (png, jpg, jpeg, gif).")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register_admin.html")

        hashed_password = generate_password_hash(password)
        db = get_db()
        
        existing = db.execute("SELECT 1 FROM users WHERE username = ? AND role = ?", (username, role)).fetchone()
        if existing:
            flash("Username already exists!", "error")
            return render_template("register_admin.html")

        try:
            db.execute("INSERT INTO users (username, password, age, profile_pic, role) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_password, age, profile_pic_filename, role))
            db.commit()
            
            user_obj = User.get(f"{username}:{role}")
            login_user(user_obj)
            
            flash("Admin account created successfully, please complete your profile.", "success")
            return redirect(url_for("admin_profile"))
            
        except sqlite3.IntegrityError:
            db.rollback()
            flash("Username already exists! Please choose another one.", "error")
            return render_template("register_admin.html")
        except Exception as e:
            db.rollback()
            flash(f"An error occurred: {e}", "error")
            return render_template("register_admin.html")

    flash("Fill out this form to create a new admin account.", "admin")
    return render_template("register_admin.html")

@app.route("/admin_profile", methods=["GET", "POST"])
@admin_required 
def admin_profile():
    db = get_db()
    
    if request.method == "POST":
        shop_name = request.form.get("shop_name", "").strip()
        labour_vacancy = request.form.get("labour_vacancy", 0, type=int) 
        total_staff = request.form.get("total_staff", 0, type=int)
        location = request.form.get("location", "").strip()
        hand_based_salary = request.form.get("hand_based_salary", "").strip()
        incentives = request.form.get("incentives", "").strip()
        branches = request.form.get("branches", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        written_test = request.form.get("written_test", "").strip()

        try:
            db.execute(
                '''INSERT OR REPLACE INTO admin_profiles
                   (username, shop_name, total_labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (current_user.username, shop_name, labour_vacancy, total_staff, location, hand_based_salary, incentives, branches, contact_info, written_test)
            )
            db.commit()
            flash("Admin profile updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.rollback()
            flash(f"Error updating profile: {e}", "error")
            return render_template("admin_profile.html", profile=request.form)

    else:
        profile = db.execute('SELECT * FROM admin_profiles WHERE username = ?', (current_user.username,)).fetchone()
        return render_template("admin_profile.html", profile=profile)


@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    username = current_user.username
    
    vacancy_status = get_vacancy_status(username) 
    
    query = """
        SELECT c.*, COUNT(a.id) AS applications_received
        FROM career_options c
        LEFT JOIN applications a ON c.id = a.job_id
        WHERE c.posted_by = ?
        GROUP BY c.id
        ORDER BY c.name
    """
    
    profile = db.execute("SELECT * FROM admin_profiles WHERE username = ?", (username,)).fetchone()
    jobs = db.execute(query, (username,)).fetchall()
    
    return render_template(
        "admin_dashboard.html", 
        profile=profile, 
        jobs=jobs, 
        vacancy_status=vacancy_status
    )

@app.route('/edit_admin_profile', methods=['GET', 'POST'])
@admin_required
def edit_admin_profile():
    db = get_db()
    username = current_user.username

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

        if total_labour_vacancy is not None and total_staff is not None and total_labour_vacancy > total_staff:
            flash('Total vacancies cannot be greater than total staff.', 'error')
            profile = {
                'shop_name': shop_name, 'total_labour_vacancy': total_labour_vacancy,
                'total_staff': total_staff, 'location': location,
                'hand_based_salary': hand_based_salary, 'incentives': incentives,
                'branches': branches, 'contact_info': contact_info,
                'written_test': written_test
            }
            return render_template('edit_admin_profile.html', profile=profile)

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

@app.route('/post_job', methods=['GET', 'POST'])
@admin_required
def post_job():
    db = get_db()
    username = current_user.username
    
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
        total_labour_vacancy = request.form.get("total_labour_vacancy", 0, type=int)
        
        # is_vacant is set to 1 (Open) upon posting
        is_vacant = 1 if total_labour_vacancy > 0 else 0

        posted_by = username

        if not name or not description:
            flash("Job name and description are required.", "error")
            return render_template("post_job.html", available_skills=available_skills)

        vacancy_status = get_vacancy_status(username)
        admin_vacancy_limit = vacancy_status['limit']
        current_vacancies_sum = vacancy_status['posted']
        
        if (current_vacancies_sum + total_labour_vacancy) > admin_vacancy_limit:
            flash(
                f"Your total vacancies (currently {current_vacancies_sum}) will exceed your limit of {admin_vacancy_limit}. Please update or change your vacancy limit in your admin profile through the edit button.", 
                "error"
            )
            return render_template("post_job.html", available_skills=available_skills)

        if application_form_url and not (application_form_url.startswith("http://") or application_form_url.startswith("https://")):
            flash("Application Form URL must start with http:// or https://", "error")
            return render_template("post_job.html", available_skills=available_skills)

        try:
            cursor = db.cursor()
            cursor.execute(
                '''INSERT INTO career_options
                   (name, description, learn_more, skills_required, application_form_url, 
                    is_vacant, total_labour_vacancy, posted_by, posted_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, description, learn_more, skills_required, application_form_url,
                 is_vacant, total_labour_vacancy, posted_by, datetime.now().isoformat())
            )
            
            new_job_id = cursor.lastrowid
            db.commit()
            
            # Since we removed the automatic closing logic, this call is just for legacy code/consistency
            if new_job_id:
                update_vacancy_status(new_job_id) 

            flash("Job posted successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"Failed to post job: {e}", "error")

    return render_template("post_job.html", available_skills=available_skills)


from datetime import date, datetime, timedelta # Ensure this is the import line at the top of app.py 

# ... (rest of your code) ...

def update_vacancy_status(job_id):
    """
    Automatically closes the job if 
    1. Applications RECEIVED > Vacancies, AND
    2. The job has been posted for more than 30 days.
    """
    db = get_db()
    
    # 1. Fetch job details, including posted_date (MUST be in ISO format, e.g., YYYY-MM-DD HH:MM:SS)
    job = db.execute(
        '''SELECT total_labour_vacancy, posted_date, is_vacant FROM career_options WHERE id = ?''', 
        (job_id,)
    ).fetchone()

    if not job:
        return False
        
    try:
        apps_count = db.execute(
            'SELECT COUNT(*) FROM applications WHERE job_id = ?', 
            (job_id,)
        ).fetchone()[0]
        
        # --- Configuration ---
        DEACTIVATION_DAYS = 30  
        VACANCY_THRESHOLD = job['total_labour_vacancy']
        # --- End Configuration ---
        
        # Convert posted_date string to a datetime object
        posted_date = datetime.fromisoformat(job['posted_date'])
        
        # Calculate the expiration threshold
        expiration_date = posted_date + timedelta(days=DEACTIVATION_DAYS)
        
        # Check Conditions for Auto-Closing:
        is_saturated = apps_count > VACANCY_THRESHOLD
        is_expired = datetime.now() > expiration_date

        if is_saturated and is_expired:
            # Condition met: Close the vacancy
            new_status = 0
        else:
            # Condition not met: Ensure it stays Open
            new_status = 1

        # Only update the database if the status is changing (prevents unnecessary commits)
        if new_status != job['is_vacant']:
            db.execute('UPDATE career_options SET is_vacant = ? WHERE id = ?', (new_status, job_id))
            db.commit()
            
        return True
            
    except Exception as e:
        print(f"Error checking job expiration status for {job_id}: {e}")
        return False
    
    
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    db = get_db()
    
    # --- 1. INITIAL DUPLICATE CHECK (For GET request - prevents loading form) ---
    existing_application = db.execute(
        "SELECT id FROM applications WHERE user_id = ? AND job_id = ?",
        (current_user.id, job_id)
    ).fetchone()

    if existing_application:
        flash("You have already applied for this job.", "error")
        # CRUCIAL: Redirect immediately to prevent rendering the form
        return redirect(url_for('dashboard')) 
    # -------------------------------------------------------------------------

    # 2. Get Job Details
    job = db.execute("SELECT * FROM career_options WHERE id = ?", (job_id,)).fetchone()
    
    if not job:
        flash("Job not found.", "error")
        return redirect(url_for('dashboard'))

    # --- POST REQUEST HANDLING (Form Submission) ---
    if request.method == 'POST':
        
        # --- FIX: SECOND DUPLICATE CHECK (Stops multiple submissions/browser back button issue) ---
        existing_application_post = db.execute(
            "SELECT id FROM applications WHERE user_id = ? AND job_id = ?",
            (current_user.id, job_id)
        ).fetchone()

        if existing_application_post:
            # Block the database INSERT if the application already exists
            flash("Submission blocked: You have already applied for this job.", "error")
            return redirect(url_for('dashboard')) 
        # ------------------------------------------------------------------------------------------
        
        try:
            resume_file = request.files.get("resume")
            resume_filename = None

            if resume_file and resume_file.filename != '':
                if allowed_file(resume_file.filename):
                    filename = f"{int(time.time())}_{secure_filename(resume_file.filename)}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    resume_file.save(file_path)
                    resume_filename = filename
                else:
                    flash("Invalid resume file type. Only image and PDF files are allowed.", "error")
                    return redirect(request.url)
            else:
                recent_app_for_resume = db.execute(
                    "SELECT resume_filename FROM applications WHERE user_id = ? AND resume_filename IS NOT NULL ORDER BY id DESC LIMIT 1",
                    (current_user.id,)
                ).fetchone()
                if recent_app_for_resume:
                    resume_filename = recent_app_for_resume['resume_filename']

            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            dob = request.form.get("dob", "").strip()
            address = request.form.get("address", "").strip()
            pincode = request.form.get("pincode", "").strip()
            applicant_email = request.form.get("applicant_email", "").strip()
            applicant_phone = request.form.get("applicant_phone", "").strip()
            experience = request.form.get("experience", "").strip()
            skills_applied = request.form.get("skills", "").strip()
            preferred_location = request.form.get("preferred_location", "").strip()

            db.execute(
                '''INSERT INTO applications (
                    job_id, user_id, applicant_name, first_name, last_name, dob, address, 
                    pincode, applicant_email, applicant_phone, experience, 
                    skills_applied, preferred_location, resume_filename
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    job_id, current_user.id, current_user.username, first_name, last_name, dob, address,
                    pincode, applicant_email, applicant_phone, experience, 
                    skills_applied, preferred_location, resume_filename
                )
            )

            user_skills = set(current_user.skills.split(',')) if current_user.skills else set()
            job_skills = set([skill.strip() for skill in job['skills_required'].split(',')]) if job['skills_required'] else set()
            updated_skills_set = user_skills.union(job_skills)
            updated_skills_set.discard('')
            updated_skills = ','.join(sorted(list(updated_skills_set)))
            
            db.execute("UPDATE users SET skills = ? WHERE username = ? AND role = ?", 
                       (updated_skills, current_user.username, current_user.role))
            
            db.commit()

            flash("Application submitted successfully!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.rollback()
            flash(f"An error occurred while submitting your application: {e}", "error")
            return redirect(request.url)

    # --- GET REQUEST HANDLING (Renders the form) ---
    recent_application_row = db.execute(
        "SELECT * FROM applications WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (current_user.id,)
    ).fetchone()
    
    recent_application = dict(recent_application_row) if recent_application_row else None
    
    preferred_locations = []
    if job['posted_by']:
        admin_profile = db.execute("SELECT location FROM admin_profiles WHERE username = ?", (job['posted_by'],)).fetchone()
        if admin_profile and admin_profile['location']:
            locations = [loc.strip() for loc in admin_profile['location'].split(',') if loc.strip()]
            preferred_locations = sorted(locations)
            
    return render_template(
        'apply.html', 
        job=job, 
        preferred_locations=preferred_locations,
        recent_application=recent_application
    )

@app.route('/admin_dashboard/applications/<int:job_id>')
@admin_required
def view_applications(job_id):
    db = get_db()
    username = current_user.username
    job = db.execute("SELECT * FROM career_options WHERE id = ? AND posted_by = ?", (job_id, username)).fetchone()
    if not job:
        abort(404)
        
    query = """
        SELECT 
            a.id, 
            a.applicant_name, 
            a.applicant_email, 
            a.applicant_phone, 
            a.resume_filename,
            u.age, 
            u.skills, 
            u.profile_pic
        FROM applications a
        LEFT JOIN users u ON a.applicant_name = u.username
        WHERE a.job_id = ?
    """
    applications = db.execute(query, (job_id,)).fetchall()

    return render_template("applications.html", job=job, applications=applications)

@app.route('/resumes/<filename>')
def uploaded_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- ROUTE 1: THE INITIAL FILTER FORM PAGE ---
@app.route('/career_videos/select', methods=['GET'])
def select_video_skills():
    db = get_db()
    
    posted_skills_rows = db.execute(
        """
        SELECT DISTINCT skills_required FROM career_options 
        WHERE is_vacant = 1 AND skills_required IS NOT NULL AND skills_required != ''
        """
    ).fetchall()

    posted_skills_set = set()
    for row in posted_skills_rows:
        skills = row['skills_required'].split(',')
        posted_skills_set.update(skill.strip() for skill in skills)
    
    available_skills = sorted(list(posted_skills_set))

    return render_template(
        'select_video_skills.html', 
        available_skills=available_skills
    )


# --- ROUTE 2: PERFORMS LIVE YOUTUBE SEARCH AND DISPLAYS RESULTS ---
@app.route('/career_videos/results', methods=['POST'])
def display_filtered_videos():
    selected_skills = request.form.getlist('skill')
    
    if not selected_skills:
        flash("Please select at least one skill to search for videos.", "error")
        return redirect(url_for('select_video_skills'))
        
    query_term = " OR ".join(selected_skills)
    
    videos_list = []
    
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        search_response = youtube.search().list(
            q=query_term,
            part="id,snippet",
            maxResults=10, 
            type="video"
        ).execute()
        
        for search_result in search_response.get("items", []):
            video_id = search_result["id"]["videoId"]
            embed_link = f"https://www.youtube.com/embed/{video_id}" 

            videos_list.append({
                'title': search_result["snippet"]["title"],
                'filename': embed_link,
                'description': search_result["snippet"]["description"],
                'is_relevant': True,
            })

    except Exception as e:
        print(f"YouTube API Error: {e}")
        flash('Could not connect to YouTube. Please try again later.', 'error')
        
    return render_template(
        'career_videos.html', 
        videos=videos_list,
        search_query=query_term,
        user_skills=[] 
    )

from flask import redirect, url_for, flash
from flask_login import login_required, current_user
# Ensure all other necessary imports (get_db, render_template, etc.) are present at the top of your app.py

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user
    
    skills_str = getattr(user, "skills", "") or ""
    user_skills_list = [s.strip().lower() for s in skills_str.split(",") if s.strip()]

    relevant_jobs = [] 
    db = get_db()
    
    # --- Logic for Career Suggestions (No Change) ---
    all_jobs_query = """
        SELECT c.*, ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
    """
    career_options_db = db.execute(all_jobs_query).fetchall()

    if user_skills_list:
        for job in career_options_db:
            job_skills_list = [s.strip().lower() for s in (job["skills_required"] or "").split(",") if s.strip()]
            if any(user_skill in job_skills_list for user_skill in user_skills_list):
                relevant_jobs.append(job)
    # --------------------------------------------------

    # ======================================================================
    # --- UPDATED: Logic for Applied Jobs (for Download Links) ---
    # ======================================================================
    # This query now fetches each individual application to get its unique ID.
    # It also uses user_id for a more reliable query.
    applied_jobs = db.execute(
        """
        SELECT
            a.id as application_id,
            c.name as job_name
        FROM applications a
        JOIN career_options c ON a.job_id = c.id
        WHERE a.user_id = ?
        ORDER BY a.id DESC
        """,
        (user.id,)  # Use user.id (same as current_user.id)
    ).fetchall()
    # ======================================================================
    # --- END OF UPDATE ---
    # ======================================================================

    return render_template(
        "dashboard.html", 
        user=user, 
        jobs=relevant_jobs, 
        applied_jobs=applied_jobs
    )
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    db = get_db()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sender_email = request.form.get('email', '').strip()
        message_body = request.form.get('message', '').strip()

        if not name or not sender_email or not message_body:
            flash("All fields are required. Please fill out the form completely.", "error")
            return redirect(url_for('contact'))

        try:
            db.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)", 
                       (name, sender_email, message_body))
            
            db.commit()
            
            flash("Your message has been saved. We'll get back to you soon!", "success")
            return redirect(url_for('contact'))
            
        except Exception as e:
            flash(f"Failed to save message to DB. Error: {e}", "error")
            db.rollback() 

    return render_template('contact.html')

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
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
            
            updated_user = User.get(current_user.id)
            login_user(updated_user, remember=True) 
            
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
    today = date.today().isoformat()
    
    todays_jobs_query = """
        SELECT c.*, ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
        WHERE c.is_vacant = 1 AND DATE(c.posted_date) = ?
        ORDER BY c.name ASC
    """
    todays_jobs = db.execute(todays_jobs_query, (today,)).fetchall()
    
    all_jobs_query = """
        SELECT c.*, ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
        WHERE c.is_vacant = 1
    """
    params = []
    if search_query:
        all_jobs_query += " AND (LOWER(c.name) LIKE ? OR LOWER(c.skills_required) LIKE ? OR LOWER(c.description) LIKE ?)"
        like_pattern = f"%{search_query}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    all_jobs_query += " ORDER BY c.name ASC"
    jobs_raw = db.execute(all_jobs_query, params).fetchall()
    
    todays_job_ids = {job['id'] for job in todays_jobs}
    jobs = [job for job in jobs_raw if job['id'] not in todays_job_ids]
    
    available_skills = {}
    
    return render_template(
        'career_options.html',
        todays_jobs=todays_jobs,
        jobs=jobs,
        available_skills=available_skills,
        search_query=search_query
    )


@app.route('/career_interests', methods=['GET', 'POST'])
@login_required
def career_interests():
    if not current_user.is_authenticated:
        flash("Please log in to select your career interests.", "error")
        return redirect(url_for("login"))

    db = get_db()

    rows = db.execute(
        "SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''"
    ).fetchall()
    skills_set = set()
    for row in rows:
        skills_in_row = [skill.strip() for skill in row['skills_required'].split(',')]
        skills_set.update(skills_in_row)
    available_skills = sorted(skills_set)

    if request.method == 'POST':
        selected_skills = request.form.getlist("skills")
        skills_str = ",".join(selected_skills).strip()

        try:
            db.execute(
                "UPDATE users SET skills = ? WHERE username = ? AND role = ?",
                (skills_str, current_user.username, current_user.role),
            )
            db.commit()
            
            updated_user = User.get(current_user.id)
            login_user(updated_user, remember=True) 
            
            flash("Career interests updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Failed to update career interests: {e}", "error")
            db.rollback() 
            return redirect(url_for("career_interests"))

    user_row = db.execute(
        "SELECT skills FROM users WHERE username = ? AND role = ?",
        (current_user.username, current_user.role),
    ).fetchone()

    if user_row and user_row["skills"]:
        user_skills = [s.strip() for s in user_row["skills"].split(",") if s.strip()]
    else:
        user_skills = []

    return render_template(
        "career_interests.html",
        available_skills=available_skills,
        user_skills=user_skills,
    )

@app.route('/terms/<int:job_id>')
def terms(job_id):
    return render_template('terms.html', job_id=job_id)


@app.route('/admin_dashboard/applications')
@admin_required
def view_all_applications():
    db = get_db()
    username = current_user.username
    query = """
        SELECT a.id, a.applicant_name, a.contact_info, a.resume_filename, c.id AS job_id, c.name AS job_name
        FROM applications a
        JOIN career_options c ON a.job_id = c.id
        WHERE c.posted_by = ?
        ORDER BY c.name, a.applicant_name
    """
    applications = db.execute(query, (username,)).fetchall()
    return render_template('all_applications.html', applications=applications)


@app.route('/todays_jobs')
def todays_jobs_page():
    db = get_db()
    today = date.today().isoformat()
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


@app.route('/career_guidance/<string:job_name>')
def career_guidance(job_name):
    db = get_db()
    
    job = db.execute("SELECT * FROM career_options WHERE name = ?", (job_name,)).fetchone()
    
    if job:
        return render_template('career_guidance.html', job=job)
    else:
        flash(f"No guidance found for the career: {job_name}", "error")
        return redirect(url_for('career_options'))

def check_jobs():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    print("--- All Job Postings in the Database ---")
    
    try:
        cursor.execute("SELECT id, name, posted_by FROM career_options")
        rows = cursor.fetchall()

        if not rows:
            print("No jobs found.")
        else:
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, Posted By: {row[2]}")

    except sqlite3.OperationalError as e:
        print(f"Database error: {e}. The 'career_options' table might be missing or columns are incorrect.")
    
    conn.close()

@app.route('/youtube_search_api')
@admin_required
def youtube_search_api():
    query = request.args.get('q')
    
    if not query:
        return jsonify([])

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        
        search_response = youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=5,
            type="video"
        ).execute()
        
        results = []
        
        for search_result in search_response.get("items", []):
            video_id = search_result["id"]["videoId"]
            embed_link = f"https://www.youtube.com/embed/{video_id}" 
            
            results.append({
                'title': search_result["snippet"]["title"],
                'link': embed_link,
                'description': search_result["snippet"]["description"],
                'duration': "N/A" 
            })
            
        return jsonify(results)
    
    except Exception as e:
        print(f"YouTube API Error: {e}")
        return jsonify({'error': 'Search failed. Check key and network.'}), 500
    

@app.route('/admin/upload_video', methods=['GET', 'POST'])
@admin_required
def upload_video():
    db = get_db()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        tags = request.form.get('tags', '').strip()
        description = request.form.get('description', '').strip()
        filename_to_save = request.form.get('filename_to_save', '').strip() 
        
        if not title or not tags or not filename_to_save:
            flash("Video Title, Tags, and Selection are required.", "error")
            return render_template('upload_video.html')

        try:
            db.execute(
                '''INSERT INTO career_videos (title, description, filename, video_tags, upload_date)
                   VALUES (?, ?, ?, ?, ?)''',
                (title, description, filename_to_save, tags, datetime.now().isoformat())
            )
            db.commit()
            flash("Video posted successfully!", "success")
            return redirect(url_for('view_videos')) 
            
        except Exception as e:
            db.rollback()
            flash(f"Database error: {e}", "error")
            
    return render_template('upload_video.html')


def generate_ai_response(prompt):
    """
    Returns a dynamic response: either a local answer or a live search link.
    """
    prompt_lower = prompt.lower()
    
    if "python" in prompt_lower or "data science" in prompt_lower:
        return {"action": "message", "response": "Python is essential for data science and backend web development. To excel, focus on data structures and algorithms."}
        
    elif "waiter" in prompt_lower or "service" in prompt_lower:
        return {"action": "message", "response": "Working in hospitality requires excellent communication and teamwork. Focus on multitasking and maintaining a positive attitude."}
    
    elif "interview" in prompt_lower or "crack job" in prompt_lower:
        return {"action": "message", "response": "To crack the interview, focus on explaining your thought process clearly and demonstrate excellent communication skills."}

    else:
        search_url = f"https://www.google.com/search?q=career+guidance+{prompt}"
        return {
            "action": "link", 
            "url": search_url,
            "message": f"I don't have stored information for '{prompt.capitalize()}'. Would you like me to perform a live web search?"
        }

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'action': 'message', 'response': "Please enter a message."}), 400
    
    ai_response_data = generate_ai_response(user_message)
    
    return jsonify(ai_response_data)


@app.route('/admin/delete_job/<int:job_id>')
@admin_required
def delete_job(job_id):
    db = get_db()
    username = current_user.username
    
    try:
        job_check = db.execute(
            "SELECT id FROM career_options WHERE id = ? AND posted_by = ?", 
            (job_id, username)
        ).fetchone()
        
        if not job_check:
            flash("Error: Job not found or you do not have permission to delete it.", "error")
            return redirect(url_for('admin_dashboard'))

        # This is the ONLY place where jobs and applications are deleted
        db.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
        db.execute("DELETE FROM career_options WHERE id = ?", (job_id,))
        db.commit()
        
        flash("Job and all associated applications successfully deleted.", "success")
        
    except Exception as e:
        db.rollback()
        flash(f"An error occurred during deletion: {e}", "error")
        
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit_job/<int:job_id>', methods=['GET', 'POST'])
@admin_required
def edit_job_post(job_id):
    db = get_db()
    username = current_user.username
    
    rows = db.execute("SELECT DISTINCT skills_required FROM career_options WHERE skills_required IS NOT NULL AND skills_required != ''").fetchall()
    skills_set = set()
    for row in rows:
        for skill in row['skills_required'].split(','):
            skill = skill.strip()
            if skill:
                skills_set.add(skill)
    available_skills = sorted(skills_set)

    job = db.execute(
        "SELECT * FROM career_options WHERE id = ? AND posted_by = ?", 
        (job_id, username)
    ).fetchone()
    
    if not job:
        flash("Error: Job not found or you do not have permission to edit it.", "error")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        learn_more = request.form.get("learn_more", "").strip()
        skills_required = request.form.get("skills_required", "").strip()
        application_form_url = request.form.get("application_form_url", "").strip()
        total_labour_vacancy = request.form.get("total_labour_vacancy", 0, type=int)
        
        is_vacant = 1 if total_labour_vacancy > 0 else 0
        
        vacancy_status = get_vacancy_status(username)
        admin_vacancy_limit = vacancy_status['limit']
        
        current_vacancies_sum_row = db.execute(
            "SELECT SUM(total_labour_vacancy) FROM career_options WHERE posted_by = ? AND id != ?", 
            (username, job_id)
        ).fetchone()
        current_vacancies_sum = current_vacancies_sum_row[0] if current_vacancies_sum_row[0] else 0
        
        if (current_vacancies_sum + total_labour_vacancy) > admin_vacancy_limit:
            flash(
                f"Update failed: New total vacancies ({current_vacancies_sum + total_labour_vacancy}) exceed your limit of {admin_vacancy_limit}.", 
                "error"
            )
            return render_template('edit_job_post.html', job=request.form, job_id=job_id, available_skills=available_skills)

        try:
            db.execute('''UPDATE career_options SET 
                name = ?, description = ?, learn_more = ?, skills_required = ?, 
                application_form_url = ?, total_labour_vacancy = ?, is_vacant = ?
                WHERE id = ?''',
                (name, description, learn_more, skills_required, 
                 application_form_url, total_labour_vacancy, is_vacant, job_id)
            )
            db.commit()
            
            update_vacancy_status(job_id) 
            
            flash(f"Job '{name}' updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.rollback()
            flash(f"Failed to update job: {e}", "error")

    job_skills_list = [s.strip() for s in (job["skills_required"] or "").split(",") if s.strip()]
    
    return render_template('edit_job_post.html', 
                           job=job, 
                           job_id=job_id, 
                           available_skills=available_skills,
                           current_skills=job_skills_list
                           )


@app.route('/career_videos')
def view_videos():
    db = get_db()
    videos = db.execute("SELECT * FROM career_videos ORDER BY upload_date DESC").fetchall()
    
    return render_template('career_videos_list.html', videos=videos)

# app.py (Add this route definition)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    db = get_db()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        answer = request.form.get('answer', '').strip()
        new_password = request.form.get('new_password', '')
        
        user_row = db.execute(
            "SELECT password, security_answer FROM users WHERE username = ?", 
            (username,)
        ).fetchone()

        if not user_row:
            flash("User not found.", "error")
            return redirect(url_for('forgot_password'))

        if user_row['security_answer'].lower() != answer.lower():
            flash("Incorrect security answer.", "error")
            return redirect(url_for('forgot_password'))

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "error")
            return redirect(url_for('forgot_password'))

        hashed_password = generate_password_hash(new_password)
        
        try:
            db.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))
            db.commit()
            flash("Your password has been successfully reset. Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            flash(f"An error occurred during password reset: {e}", "error")
            
    return render_template('forgot_password.html')


# --- Add these new imports at the top of your app.py ---
from flask import Response
from weasyprint import HTML

# ... (your other routes) ...

@app.route('/download/application/<int:application_id>')
@login_required
def download_application(application_id):
    db = get_db()
    
    # Security: Fetch the application and ensure it belongs to the current user
    application = db.execute(
        """
        SELECT a.*, c.name as job_name
        FROM applications a
        JOIN career_options c ON a.job_id = c.id
        WHERE a.id = ? AND a.user_id = ?
        """,
        (application_id, current_user.id)
    ).fetchone()

    # If no application is found (or it doesn't belong to the user), show an error
    if not application:
        flash("Application not found.", "error")
        return redirect(url_for('dashboard'))

    # 1. Render the HTML template from Step 2 into a string
    html_string = render_template("application_receipt.html", application=application)
    
    # 2. Use WeasyPrint to generate a PDF in memory from the HTML string
    pdf = HTML(string=html_string).write_pdf()

    # 3. Create a Flask Response to send the PDF to the browser
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment;filename=application_{application_id}.pdf"
        }
    )

@app.route('/terms-and-conditions')
def terms_and_conditions():
    """
    This route displays the separate Terms and Conditions page.
    """
    return render_template('terms.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['VIDEO_UPLOAD_FOLDER']):
        os.makedirs(app.config['VIDEO_UPLOAD_FOLDER'])
    with app.app_context():
        init_db()
        
        # --- Migration 1: Role Column ---
        try:
            migrate_add_role_column()
        except NameError:
            print("Migration warning: migrate_add_role_column not found. If this is a fresh run, ignore this.")
            
        # --- Migration 2: Career Columns ---
        try:
            migrate_add_career_columns()
        except NameError:
            # Note: This print is now correct.
            print("Migration warning: migrate_add_career_columns not found. If this is a fresh run, ignore this.")
            
        # --- Migration 3: Security Columns (NEW, Independent Call) ---
        # This call must be outside the 'try/except' of the previous migration.
        try:
            migrate_add_security_columns()
        except NameError:
            # Add this safety net since you are importing it from a new file
            print("Migration warning: migrate_add_security_columns not found. Check your security_migrations import.")

        # --- Old trailing syntax corrected/removed ---
        
    app.run(host='0.0.0.0', port=5000, debug=True)