import sqlite3
from datetime import date

def check_jobs_posted_today():
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    
    today = date.today().isoformat()
    
    print(f"--- Checking for jobs posted on {today} ---")
    
    try:
        query = "SELECT id, name, posted_by, is_vacant, posted_date FROM career_options WHERE DATE(posted_date) = ?"
        cursor.execute(query, (today,))
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found in the database with today's date.")
        else:
            print(f"Found {len(jobs)} jobs posted today:")
            for job in jobs:
                print(f"ID: {job[0]}, Name: {job[1]}, Posted By: {job[2]}, Vacant: {job[3]}, Posted Date: {job[4]}")
                
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}. The 'career_options' table or 'posted_date' column might be missing.")
    
    finally:
        conn.close()

if __name__ == '__main__':
    check_jobs_posted_today()