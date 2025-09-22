import sqlite3

DATABASE = 'career_guidance.db'

def migrate_create_skills_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            reference TEXT
        );
    """)
    conn.commit()
    conn.close()
    print("Created skills table if it did not exist.")

if __name__ == '__main__':
    migrate_create_skills_table()
