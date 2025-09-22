import sqlite3

DATABASE = 'career_guidance.db'

def migrate_add_role_column():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'role' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'job_seeker'")
        print("Added 'role' column to users table.")
    else:
        print("'role' column already exists in users table.")
    conn.commit()
    conn.close()

def migrate_add_career_columns():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(career_options)")
    columns = [row[1] for row in cursor.fetchall()]

    altered = False
    if 'shop_name' not in columns:
        cursor.execute("ALTER TABLE career_options ADD COLUMN shop_name TEXT")
        altered = True
        print("Added 'shop_name' column to career_options table.")
    if 'location' not in columns:
        cursor.execute("ALTER TABLE career_options ADD COLUMN location TEXT")
        altered = True
        print("Added 'location' column to career_options table.")
    if 'contact_info' not in columns:
        cursor.execute("ALTER TABLE career_options ADD COLUMN contact_info TEXT")
        altered = True
        print("Added 'contact_info' column to career_options table.")
    if 'posted_by' not in columns:
        cursor.execute("ALTER TABLE career_options ADD COLUMN posted_by TEXT")
        altered = True
        print("Added 'posted_by' column to career_options table.")
    if 'total_labour_vacancy' not in columns:
        cursor.execute("ALTER TABLE career_options ADD COLUMN total_labour_vacancy INTEGER DEFAULT 0")
        altered = True
        print("Added 'total_labour_vacancy' column to career_options table.")

    if altered:
        conn.commit()
    else:
        print("Career options table already has the required columns.")
    conn.close()

    

if __name__ == '__main__':
    migrate_add_role_column()
    migrate_add_career_columns()
