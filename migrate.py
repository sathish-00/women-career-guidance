import sqlite3

# Make sure this is the correct name of your database file
DATABASE_NAME = 'career_guidance.db'

def add_user_id_column():
    """
    Connects to the database and safely adds the 'user_id' column
    to the 'applications' table if it doesn't already exist.
    """
    conn = None
    try:
        # 1. Connect to the database
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # 2. Check if the column already exists
        cursor.execute("PRAGMA table_info(applications)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("Column 'user_id' already exists in 'applications' table. No changes made.")
        else:
            # 3. If it doesn't exist, add the column
            print("Column 'user_id' not found. Adding it now...")
            cursor.execute("ALTER TABLE applications ADD COLUMN user_id INTEGER")
            conn.commit()
            print("Successfully added 'user_id' column to 'applications' table.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        # 4. Close the connection
        if conn:
            conn.close()
            print("Database connection closed.")

# --- This makes the script runnable from the command line ---
if __name__ == '__main__':
    add_user_id_column()