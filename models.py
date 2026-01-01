from flask_sqlalchemy import SQLAlchemy
# Initialize SQLAlchemy outside of this snippet (e.g., in __init__.py or app.py)
# For this example, assume 'db' is initialized elsewhere.
db = SQLAlchemy() 

class Job(db.Model):
    """Stores individual job postings."""
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # The crucial column to track how many slots this post occupies
    vacancies_posted = db.Column(db.Integer, default=1, nullable=False) 
    is_active = db.Column(db.Boolean, default=True) 
    
    def __repr__(self):
        return f"<Job {self.id}: {self.title} ({self.vacancies_posted} slots)>"

class SystemSettings(db.Model):
    """Stores system-wide configuration, like the total vacancy limit."""
    __tablename__ = 'system_settings'

    # Use a fixed ID (e.g., 1) as this table will only ever have one row
    id = db.Column(db.Integer, primary_key=True)
    # The absolute maximum number of jobs/vacancies allowed
    total_allowed_vacancies = db.Column(db.Integer, default=50, nullable=False) 

    def __repr__(self):
        return f"<Settings: Total Limit={self.total_allowed_vacancies}>"