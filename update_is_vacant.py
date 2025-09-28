import sqlite3
import sys

def update_job_vacancy(job_id, new_status):
    """Updates the is_vacant status for a specific job ID."""
    try:
        conn = sqlite3.connect('career_guidance.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE career_options SET is_vacant = ? WHERE id = ?", (new_status, job_id))
        conn.commit()
        print(f"Updated is_vacant for job id {job_id} to {new_status}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Check if command-line arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python your_script_name.py <job_id> <new_status>")
        sys.exit(1)

    try:
        job_id = int(sys.argv[1])
        new_status = int(sys.argv[2])
        update_job_vacancy(job_id, new_status)
    except ValueError:
        print("Error: Job ID and status must be integers.")
        sys.exit(1)