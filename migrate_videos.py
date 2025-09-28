import sqlite3
import os

DATABASE = 'career_guidance.db'

def add_video_tags_column():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if the column already exists to prevent errors on multiple runs
        cursor.execute("PRAGMA table_info(career_videos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'video_tags' not in columns:
            conn.execute("ALTER TABLE career_videos ADD COLUMN video_tags TEXT;")
            conn.commit()
            print("Successfully added 'video_tags' column to career_videos table.")
        else:
            print("'video_tags' column already exists.")
            
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    add_video_tags_column()