# app.py (These lines MUST be at the very top)

import os 
# Ensure python-dotenv is installed: pip install python-dotenv


import time
import sqlite3
from urllib.parse import urlparse, urljoin
from flask import Flask, request, redirect, url_for, render_template, g, flash, abort, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date, datetime
from functools import wraps

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from googleapiclient.discovery import build # For YouTube API

from add_row_column import migrate_add_role_column, migrate_add_career_columns


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

# Load API Key variables securely from .env file
YOUTUBE_API_KEY = os.environ.get('AIzaSyC8hIIBnhqDhjIBZHoKGfLZP6_V0cDAefQ')




# --- 3. FLASK-LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ... (The rest of your functions and routes follow below this block) ...


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ... (The rest of your code follows) ...


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
        # app.py (Inside def init_db():)
# ...
        db.execute('''CREATE TABLE IF NOT EXISTS career_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            video_tags TEXT  -- THIS LINE MUST BE PRESENT
        )''')
        # Function to add the columns
        
# ...
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
            # --- This line has been corrected ---
            # Pass the username, age, skills, profile pic, AND role from the database
            login_user(User(
                username=user['username'], 
                age=user['age'], 
                skills=user['skills'], 
                profile_pic=user['profile_pic'], 
                role=user['role']
            ))
            # --- End of correction ---

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
#@admin_required
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
#@admin_required # This is a critical security decorator
def admin_profile():
    db = get_db()
    
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

        try:
            # Use INSERT OR REPLACE to handle both creation and updates in one query
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
        # Fetch the profile for the current logged-in user
        profile = db.execute('SELECT * FROM admin_profiles WHERE username = ?', (current_user.username,)).fetchone()
        return render_template("admin_profile.html", profile=profile)


@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    username = current_user.username
    
    # This query now joins the career_options and applications tables
    # to get a count of applications for each job.
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
    
    return render_template("admin_dashboard.html", profile=profile, jobs=jobs)

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
    
from datetime import datetime # Make sure you have this import at the top

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
        
        is_vacant = 1 if total_labour_vacancy > 0 else 0

        posted_by = username

        if not name or not description:
            flash("Job name and description are required.", "error")
            return render_template("post_job.html", available_skills=available_skills)

        admin_profile = db.execute("SELECT total_labour_vacancy FROM admin_profiles WHERE username = ?", (username,)).fetchone()
        if admin_profile and admin_profile['total_labour_vacancy'] is not None:
            admin_vacancy_limit = admin_profile['total_labour_vacancy']
            
            current_vacancies_sum_row = db.execute(
                "SELECT SUM(total_labour_vacancy) FROM career_options WHERE posted_by = ?", 
                (username,)
            ).fetchone()
            current_vacancies_sum = current_vacancies_sum_row[0] if current_vacancies_sum_row[0] else 0
            
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
            # Corrected query to use a placeholder for the date
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
            
            if new_job_id:
                update_vacancy_status(new_job_id)

            flash("Job posted successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"Failed to post job: {e}", "error")

    return render_template("post_job.html", available_skills=available_skills)


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
    

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM career_options WHERE id = ? AND is_vacant = 1", (job_id,)).fetchone()
    if not job:
        flash("Job not found or not vacant.", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        applicant_name = current_user.username
        
        # 🚀 REMOVED: contact_info = request.form.get("contact_info", "").strip() 
        
        # 🚀 ADDED: Retrieve specific contact fields from the application form
        applicant_email = request.form.get("applicant_email", "").strip()
        applicant_phone = request.form.get("applicant_phone", "").strip() # Name used in the HTML form
        
        # 💡 Suggestion: Retrieve other application-specific data (First Name, Last Name, etc.)
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        dob = request.form.get("dob", "").strip()
        address = request.form.get("address", "").strip()
        pincode = request.form.get("pincode", "").strip()
        experience = request.form.get("experience", "").strip()
        skills_applied = request.form.get("skills", "").strip()
        preferred_location = request.form.get("preferred_location", "").strip()

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
                    flash(f"Failed to save resume file: {e}", "error")
                    return redirect(request.url)
            else:
                flash("Only image (png, jpg, jpeg, gif) and pdf files are allowed for resume.", "error")
                return redirect(request.url)

        try:
            # 🚀 UPDATED: INSERT query now saves email and phone, and includes other application data
            db.execute(
                '''INSERT INTO applications (
                    job_id, applicant_name, 
                    applicant_email, applicant_phone, 
                    resume_filename, 
                    first_name, last_name, dob, address, pincode, experience, skills_applied, preferred_location
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    job_id, applicant_name, 
                    applicant_email, applicant_phone, 
                    resume_filename, 
                    first_name, last_name, dob, address, pincode, experience, skills_applied, preferred_location
                )
            )

            # --- User Skill Update Logic (Kept Original) ---
            user_skills = set(current_user.skills.split(',')) if current_user.skills else set()
            job_skills = set([skill.strip() for skill in job['skills_required'].split(',')])
            updated_skills = ','.join(sorted(user_skills.union(job_skills)))

            db.execute(
                "UPDATE users SET skills = ? WHERE username = ?",
                (updated_skills, current_user.username)
            )
            # --- End Skill Update Logic ---

            db.commit()

            # The function definition for update_vacancy_status is provided below
            update_vacancy_status(job_id) 

            flash("Application submitted successfully.", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.rollback()
            flash(f"Failed to submit application: {e}", "error")
            return redirect(request.url)

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
            
            -- 🚀 UPDATED: Fetch specific contact and age fields
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







 # Required for display_filtered_videos



# NOTE: Make sure YOUTUBE_API_KEY is defined in your global variables
# YOUTUBE_API_KEY = "AIzaSyC8hIIBnhqDhjIBZHoKGfLZP6_V0cDAefQ" 


# --- ROUTE 1: THE INITIAL FILTER FORM PAGE ---
@app.route('/career_videos/select', methods=['GET'])
def select_video_skills():
    db = get_db()
    
    # 1. Fetch all unique skills required by current vacant jobs
    posted_skills_rows = db.execute(
        """
        SELECT DISTINCT skills_required FROM career_options 
        WHERE is_vacant = 1 AND skills_required IS NOT NULL AND skills_required != ''
        """
    ).fetchall()

    # 2. Aggregate all skills into a single, clean list
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
    # 1. Get selected skills from the form submission
    selected_skills = request.form.getlist('skill')
    
    if not selected_skills:
        flash("Please select at least one skill to search for videos.", "error")
        return redirect(url_for('select_video_skills'))
        
    # 2. Format the query for YouTube (e.g., "Python OR Excel OR Communication")
    query_term = " OR ".join(selected_skills)
    
    videos_list = []
    
    # NOTE: YOUTUBE_API_KEY must be defined globally in your app.py
    YOUTUBE_API_KEY = "AIzaSyC8hIIBnhqDhjIBZHoKGfLZP6_V0cDAefQ" 

    try:
        # Initialize the YouTube service client
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        search_response = youtube.search().list(
            q=query_term,
            part="id,snippet",
            maxResults=10, 
            type="video"
        ).execute()
        
        # 3. Process the response and format for the frontend
        for search_result in search_response.get("items", []):
            video_id = search_result["id"]["videoId"]
            embed_link = f"https://www.youtube.com/embed/{video_id}" 

            videos_list.append({
                'title': search_result["snippet"]["title"],
                'filename': embed_link,
                'description': search_result["snippet"]["description"],
                'is_relevant': True, # All results are relevant to the selected query
            })

    except Exception as e:
        print(f"YouTube API Error: {e}")
        flash('Could not connect to YouTube. Please try again later.', 'error')
        
    # 4. Render the final video gallery page, ensuring all template variables are defined
    return render_template(
        'career_videos.html', 
        videos=videos_list,
        search_query=query_term,
        user_skills=[] # Prevents the UndefinedError/TypeError in JavaScript/Jinja2
    )

@app.route("/dashboard")
def dashboard():
    user = current_user if hasattr(current_user, "is_authenticated") and current_user.is_authenticated else None

    user_skills_list = []
    username = None
    if user and hasattr(user, "skills"):
        skills_str = getattr(user, "skills", "") or ""
        user_skills_list = [s.strip().lower() for s in skills_str.split(",") if s.strip()]
        username = getattr(user, "username", None)

    db = get_db()

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


# app.py (Ensure these imports are at the top of your file)
# from flask_mail import Mail, Message  <-- UNCOMMENT/ADD THESE
# import os                          <-- Ensure os is imported
# ... (Your MAIL_ configuration must be set up)

# Ensure this is at the very top of app.py

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
            
            # 1. SAVE MESSAGE TO DATABASE 
            db.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)", 
                       (name, sender_email, message_body))
            
            # 2. SEND EMAIL TO ADMIN
            from flask_mail import Message
            
            recipient = os.environ.get('EMAIL_USER')
            
            email_subject = f"New Contact Message from {name}"
            email_body = f"""
            A new message has been submitted through the contact form:
            
            Name: {name}
            Sender Email: {sender_email}
            
            Message:
            {message_body}
            """
            
            msg = Message(email_subject,
                          recipients=[recipient],
                          body=email_body)
            
            # --- CRITICAL FIX FOR SCOPE ---
            global mail # Declares mail as a global object accessible in this function
            mail.send(msg) 
            # --- End of Fix ---
            
            db.commit()
            
            flash("Your message has been saved and sent. We'll get back to you soon!", "success")
            return redirect(url_for('contact'))
            
        except Exception as e:
            flash(f"Failed to send message or save to DB. Error: {e}", "error")
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
    today = date.today().isoformat()
    
    # Query for Today's Jobs
    todays_jobs_query = """
        SELECT c.*, ap.shop_name, ap.location, ap.contact_info
        FROM career_options c
        LEFT JOIN admin_profiles ap ON c.posted_by = ap.username
        WHERE c.is_vacant = 1 AND DATE(c.posted_date) = ?
        ORDER BY c.name ASC
    """
    todays_jobs = db.execute(todays_jobs_query, (today,)).fetchall()
    
    # Query for All Available Jobs (with optional search)
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
    jobs = db.execute(all_jobs_query, params).fetchall()
    
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
            flash("Career interests updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Failed to update career interests: {e}", "error")
            return redirect(url_for("career_interests"))

    user_row = db.execute(
        "SELECT skills FROM users WHERE username = ? AND role = ?",
        (current_user.username, current_user.role),
    ).fetchone()

    if user_row and user_row["skills"]:
        user_skills = user_row["skills"].split(",")
    else:
        user_skills = available_skills

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
def todays_jobs():
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


# app.py

# ... (other routes) ...

@app.route('/career_guidance/<string:job_name>')
def career_guidance(job_name):
    db = get_db()
    
    # Fetches the entire job row from the database using the job's name
    job = db.execute("SELECT * FROM career_options WHERE name = ?", (job_name,)).fetchone()
    
    if job:
        # We will now use the search tool to get a summary and tips
        
        # --- (Here is where the AI/Advanced Search Logic would go) ---
        # For example, searching Google for structured tips based on job.name:
        
        # This function would return a dictionary of structured advice.
        # For simplicity, we pass the job object and let the template render it.
        # -----------------------------------------------------------------

        return render_template('career_guidance.html', job=job)
    else:
        flash(f"No guidance found for the career: {job_name}", "error")
        return redirect(url_for('career_options'))

import sqlite3

def check_jobs():
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    print("--- All Job Postings in the Database ---")
    
    try:
        # Fetch all columns to see if 'posted_by' is being saved correctly
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

# app.py

# ... (rest of your imports) ...

@app.route('/youtube_search_api')
@admin_required
def youtube_search_api():
    query = request.args.get('q')
    
    if not query:
        return jsonify([])

    try:
        # 1. Initialize the YouTube service client using your key
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        
        # 2. Execute the search request
        search_response = youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=5,
            type="video"
        ).execute()
        
        results = []
        
        # 3. Process the response and format the results for the frontend
        for search_result in search_response.get("items", []):
            video_id = search_result["id"]["videoId"]
            # We use the embed URL for iframe src
            embed_link = f"https://www.youtube.com/embed/{video_id}" 
            
            results.append({
                'title': search_result["snippet"]["title"],
                'link': embed_link,
                'duration': "N/A" 
            })
            
        return jsonify(results)
    
    except Exception as e:
        # Handle API key errors or connection failures
        print(f"YouTube API Error: {e}")
        return jsonify({'error': 'Search failed. Check key and network.'}), 500
    


@app.route('/admin/upload_video', methods=['GET', 'POST'])
@admin_required
def upload_video():
    db = get_db()
    
    if request.method == 'POST':
        # Data comes from the hidden form fields after YouTube search/selection
        title = request.form.get('title', '').strip()
        tags = request.form.get('tags', '').strip()
        description = request.form.get('description', '').strip()
        # This is the final embed URL selected from the search results
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


 # Ensure this is imported

 # Ensure this is imported at the top

# --- Placeholder function for AI integration ---
# NOTE: This function needs your actual LLM API call logic (e.g., Gemini API)
 # Ensure this is imported

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
        # Default action: Generate a dynamic search link for non-stored information
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
    
    # Return the structured data directly
    return jsonify(ai_response_data)

# Make sure you have 'import openai' and your API key configured globally in app.py

# add_columns.py
# In your main app.py file, define this function:
# (You might need to import os, if it's not already)


# Do NOT call this function here. We will call it from the shell.


@app.route('/admin/delete_job/<int:job_id>')
@admin_required
def delete_job(job_id):
    db = get_db()
    username = current_user.username
    
    try:
        # 1. Verify the job exists AND belongs to the current admin for security
        job_check = db.execute(
            "SELECT id FROM career_options WHERE id = ? AND posted_by = ?", 
            (job_id, username)
        ).fetchone()
        
        if not job_check:
            flash("Error: Job not found or you do not have permission to delete it.", "error")
            return redirect(url_for('admin_dashboard'))

        # 2. Delete related applications first (CRUCIAL for data integrity)
        db.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
        
        # 3. Delete the job post itself
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
    
    # Fetch the job to ensure it exists and belongs to the admin
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
        
        # --- Recalculate Vacancy Limit (Same logic as post_job) ---
        admin_profile = db.execute("SELECT total_labour_vacancy FROM admin_profiles WHERE username = ?", (username,)).fetchone()
        admin_vacancy_limit = admin_profile['total_labour_vacancy'] if admin_profile else 0
        
        # Sum current vacancies, EXCLUDING the current job's old vacancy count
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
            return render_template('edit_job_post.html', job=job, job_id=job_id)
        # --- End of Limit Check ---

        try:
            db.execute('''UPDATE career_options SET 
                name = ?, description = ?, learn_more = ?, skills_required = ?, 
                application_form_url = ?, total_labour_vacancy = ?, is_vacant = ?
                WHERE id = ?''',
                (name, description, learn_more, skills_required, 
                 application_form_url, total_labour_vacancy, is_vacant, job_id)
            )
            db.commit()
            
            # Update the vacancy status (to check against applications)
            update_vacancy_status(job_id) 
            
            flash(f"Job '{name}' updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.rollback()
            flash(f"Failed to update job: {e}", "error")

    # GET request: Render the edit form
    return render_template('edit_job_post.html', job=job, job_id=job_id)


# app.py (New route to get recommendations)


# This route should be protected

 

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['VIDEO_UPLOAD_FOLDER']):
        os.makedirs(app.config['VIDEO_UPLOAD_FOLDER'])
    with app.app_context():
        init_db()
        migrate_add_role_column()
        migrate_add_career_columns()
    
        
    app.run(host='0.0.0.0', port=5000, debug=True)
    