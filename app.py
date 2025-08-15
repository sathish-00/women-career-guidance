import sqlite3
import os
from flask import Flask, request, redirect, session, url_for, render_template, g, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import base64

# --- Configuration for file uploads and database ---
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'career_guidance.db'

app = Flask(__name__, static_folder="static")

# Configure built-in session management with a SECRET_KEY
app.config['SECRET_KEY'] = 'ab8ff1c3a4662502b0c67289d6317703c493208dfc78ab1d'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            age INTEGER,
            profile_pic TEXT,
            skills TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS career_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            learn_more TEXT NOT NULL,
            skills_required TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(career_options);")
        columns = [col[1] for col in cursor.fetchall()]
        if 'skills_required' not in columns:
            print("Adding 'skills_required' column to career_options table...")
            db.execute("ALTER TABLE career_options ADD COLUMN skills_required TEXT;")
        db.commit()

# --- Global Data ---
available_skills = [
    "Python Programming", "Web Development (Frontend)", "Web Development (Backend)",
    "Database Management (SQL)", "Machine Learning", "Data Analysis",
    "Cloud Computing (AWS/Azure/GCP)", "Network Administration", "Cybersecurity",
    "Project Management", "Communication", "Problem Solving", "Teamwork",
    "Graphic Design", "Content Writing", "Digital Marketing", "Sales",
    "Customer Service", "Financial Analysis", "Nursing", "Teaching",
    "Agriculture", "Tailoring", "Poultry Farming"
]

example_career_options = [
    {"name": "Python Developer", "description": "Develops software applications, web backends, and automation scripts using Python.", "learn_more": "https://www.freecodecamp.org/news/what-does-a-python-developer-do/", "skills_required": "Python Programming,Web Development (Backend),Database Management (SQL),Problem Solving"},
    {"name": "Web Designer", "description": "Focuses on the visual and interactive elements of websites, ensuring a good user experience.", "learn_more": "https://www.coursera.org/articles/what-does-a-web-designer-do", "skills_required": "Web Development (Frontend),Graphic Design"},
    {"name": "Data Scientist", "description": "Applies statistical methods, machine learning, and programming skills to extract insights from data.", "learn_more": "https://www.ibm.com/topics/data-scientist", "skills_required": "Python Programming,Data Analysis,Machine Learning"},
    {"name": "Nurse", "description": "Provides direct patient care, administers medication, and educates patients and their families.", "learn_more": "https://www.nursingworld.org/careers-and-images-in-nursing/what-do-nurses-do/", "skills_required": "Nursing,Communication,Teamwork"},
    {"name": "Teacher", "description": "Educates students of various ages and subjects, developing curricula and assessing progress.", "learn_more": "https://www.teachforamerica.org/about-us/what-we-do/what-is-a-teacher", "skills_required": "Teaching,Communication,Problem Solving"},
    {"name": "Farmer", "description": "Manages agricultural production, including crops or livestock, for food or raw materials.", "learn_more": "https://www.nationalgeographic.org/encyclopedia/farmer/", "skills_required": "Agriculture"},
    {"name": "Tailor", "description": "Designs, repairs, and alters garments, working with fabrics and sewing techniques.", "learn_more": "https://www.fashiondesigncollege.com/blog/what-is-a-tailor", "skills_required": "Tailoring"},
    {"name": "Poultry Farmer", "description": "Raises domesticated birds like chickens, ducks, or turkeys for meat, eggs, or feathers.", "learn_more": "https://www.nal.usda.gov/farms-and-agriculture/poultry-farming-information-and-resources", "skills_required": "Poultry Farming,Agriculture"}
]

# --- Flask Routes ---

@app.route("/")
def home():
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid username or password", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        age = int(request.form["age"])
        profile_pic_filename = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                profile_pic_filename = filename
            elif file.filename != '':
                flash("Only image (png, jpg, jpeg, gif) files are allowed for profile pictures.", "error")
                return redirect(request.url)
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password, age, profile_pic) VALUES (?, ?, ?, ?)",
                       (username, password, age, profile_pic_filename))
            db.commit()
            session["username"] = username
            flash("Registration successful! Please add your skills to personalize your experience.", "success")
            return redirect(url_for("career_interests"))
        except sqlite3.IntegrityError:
            flash("Username already exists! Please try a different one.", "error")
        except Exception as e:
            db.rollback()
            flash(f"An error occurred during registration: {e}", "error")
    return render_template("register.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route("/career_interests", methods=["GET", "POST"])
def career_interests():
    if "username" not in session:
        flash("You need to log in first!", "error")
        return redirect(url_for("login"))
    db = get_db()
    if request.method == "POST":
        skills = request.form.getlist("skills")
        db.execute("UPDATE users SET skills = ? WHERE username = ?", (",".join(skills), session["username"]))
        db.commit()
        flash("Skills updated successfully!", "success")
        return redirect(url_for("dashboard"))
    user = db.execute("SELECT skills FROM users WHERE username = ?", (session["username"],)).fetchone()
    current_skills = user["skills"].split(",") if user and user["skills"] else []
    return render_template(
        "career_interests.html",
        username=session["username"],
        current_skills=current_skills,
        available_skills=available_skills
    )

@app.route("/dashboard")
def dashboard():
    if "username" in session:
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (session["username"],)).fetchone()
        user_skills_list = user["skills"].split(',') if user and user["skills"] else []
        user_skills_list = [s.strip() for s in user_skills_list if s.strip()]
        relevant_jobs = []
        career_options_db = db.execute("SELECT * FROM career_options").fetchall()
        for job_option in career_options_db:
            job_skills_raw = job_option['skills_required']
            if job_skills_raw:
                job_skills_list = [s.strip() for s in job_skills_raw.split(',') if s.strip()]
                if any(user_skill in job_skills_list for user_skill in user_skills_list):
                    relevant_jobs.append(job_option)
        if not relevant_jobs:
            fallback_jobs = db.execute("SELECT * FROM career_options LIMIT 5").fetchall()
            relevant_jobs = fallback_jobs
        return render_template("dashboard.html", user=user, jobs=relevant_jobs)
    flash("You need to log in first!", "error")
    return redirect(url_for("login"))

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "username" not in session:
        flash("You need to log in first!", "error")
        return redirect(url_for("login"))
    db = get_db()
    user = db.execute("SELECT username, age, skills, profile_pic FROM users WHERE username = ?", (session["username"],)).fetchone()
    if not user:
        flash("User profile not found. Please log in again.", "error")
        session.pop('username', None)
        return redirect(url_for("login"))
    if request.method == "POST":
        new_age = request.form.get("age", type=int)
        new_skills_list = request.form.getlist("skills")
        new_skills_str = ",".join(new_skills_list)
        if new_age is None or new_age < 0:
            flash("Age must be a non-negative number.", "error")
            current_skills_for_template = user["skills"].split(",") if user and user["skills"] else []
            return render_template("edit_profile.html", user=user, current_skills=current_skills_for_template, available_skills=available_skills)
        current_profile_pic_filename = user['profile_pic']
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
                flash("Profile picture updated!", "success")
            elif file.filename != '':
                flash("Only image (png, jpg, jpeg, gif) files are allowed for profile picture.", "error")
                current_skills_for_template = user["skills"].split(",") if user and user["skills"] else []
                return render_template("edit_profile.html", user=user, current_skills=current_skills_for_template, available_skills=available_skills)
        try:
            db.execute("UPDATE users SET age = ?, skills = ?, profile_pic = ? WHERE username = ?",
                       (new_age, new_skills_str, profile_pic_filename_to_save, session["username"]))
            db.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while updating profile: {e}", "error")
    current_skills_for_template = user["skills"].split(",") if user and user["skills"] else []
    return render_template(
        "edit_profile.html",
        user=user,
        current_skills=current_skills_for_template,
        available_skills=available_skills
    )

@app.route('/career_options')
def career_options():
    query = request.args.get('query', '').strip()
    db = get_db()
    if query:
        # Search the database for careers matching the query
        search_term = f"%{query}%"
        jobs = db.execute("SELECT * FROM career_options WHERE name LIKE ? OR description LIKE ?", 
                          (search_term, search_term)).fetchall()
    else:
        # If no query, show all careers
        jobs = db.execute("SELECT * FROM career_options").fetchall()
    
    return render_template("career_options.html", jobs=jobs)

@app.route('/career_videos')
def career_videos():
    videos = [
        {"title": "Nursing Career Path", "link": "https://www.youtube.com/embed/QYjCs0HuCmM"},
        {"title": "Sewing & Tailoring Career Guidance", "link": "https://www.youtube.com/embed/HNg9kd2yHog"},
        {"title": "Farming Techniques for Beginners", "link": "https://www.youtube.com/embed/6Wv-AXtEnfM"}
    ]
    return render_template("career_videos.html", videos=videos)

@app.route('/search_videos')
def search_videos():
    query = request.args.get('query', '').lower()
    suggestions = [
        "Data Science Career Guide", "Software Engineering Path",
        "AI Engineer Roadmap", "Digital Marketing Explained"
    ]
    relevant_videos = [
        {"title": "Intro to Data Science Jobs", "url": "https://www.youtube.com/watch?v=abc123"},
        {"title": "Software Engineer Career", "url": "https://www.youtube.com/watch?v=def456"},
        {"title": "AI Career Paths & Opportunities", "url": "https://www.youtube.com/watch?v=ghi789"},
        {"title": "Marketing Strategies for 2025", "url": "http://googleusercontent.com/youtube/6"}
    ]
    matching_suggestions = [s for s in suggestions if query in s.lower()]
    matching_videos = [v for v in relevant_videos if query in v["title"].lower()]
    return {
        "suggestions": "<ul>" + "".join([f'<li onclick="document.getElementById(\'searchBar\').value=\'{s}\'; searchVideos();">{s}</li>' for s in matching_suggestions]) + "</ul>",
        "results": "<ul>" + "".join([f'<li><a href="{v["url"]}" target="_blank">{v["title"]}</a></li>' for v in matching_videos]) + "</ul>"
    }

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
            db.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                (name, sender_email, message_body)
            )
            db.commit()
            flash("Your message has been saved. We'll get back to you soon!", "success")
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f"Failed to save message. Error: {e}", "error")
            return render_template('contact.html')

    return render_template('contact.html')

@app.route('/admin/contact_messages')
def view_contact_messages():
    db = get_db()
    messages = db.execute("SELECT * FROM contact_messages ORDER BY timestamp DESC").fetchall()
    return render_template('admin_contact.html', messages=messages)

# --- Application Initialization ---
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    with app.app_context():
        init_db()
        db = get_db()
        if db.execute("SELECT COUNT(*) FROM career_options").fetchone()[0] == 0:
            print("Populating example career options...")
            for job in example_career_options:
                db.execute("INSERT INTO career_options (name, description, learn_more, skills_required) VALUES (?, ?, ?, ?)",
                           (job['name'], job['description'], job['learn_more'], job['skills_required']))
            db.commit()
            print("Example career options populated.")
        else:
            print("Career options table already populated.")
    app.run(host='0.0.0.0', port=5000, debug=True)