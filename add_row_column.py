import sqlite3

DATABASE = 'career_guidance.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def migrate_add_role_column():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'job_seeker'")
            print("Successfully added 'role' column to users table.")
        else:
            print("'role' column already exists in users table.")
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Migration for 'role' column failed: {e}")
    finally:
        conn.close()

def migrate_add_career_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(career_options)")
        columns = [row[1] for row in cursor.fetchall()]

        # These columns are specific to the career_options table
        if 'application_form_url' not in columns:
            cursor.execute("ALTER TABLE career_options ADD COLUMN application_form_url TEXT;")
        if 'is_vacant' not in columns:
            cursor.execute("ALTER TABLE career_options ADD COLUMN is_vacant INTEGER DEFAULT 1;")
        if 'posted_by' not in columns:
            cursor.execute("ALTER TABLE career_options ADD COLUMN posted_by TEXT;")
        if 'total_labour_vacancy' not in columns:
            cursor.execute("ALTER TABLE career_options ADD COLUMN total_labour_vacancy INTEGER DEFAULT 0;")

        conn.commit()
        print("Successfully added new columns to career_options table.")
    except sqlite3.OperationalError as e:
        print(f"Migration for career_options columns failed: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_add_role_column()
    migrate_add_career_columns()