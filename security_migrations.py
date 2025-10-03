import sqlite3
import os

# --- GLOBAL CONSTANTS (Match those in app.py) ---
DATABASE = 'career_guidance.db'

def migrate_add_security_columns():
    """
    Connects to the database and adds security_question and security_answer 
    columns to the users table if they don't already exist.
    """
    conn = None
    try:
        # Establish a direct connection to the database file
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # List of columns to check for and add
        columns_to_add = [
            ('security_question', 'TEXT'),
            ('security_answer', 'TEXT')
        ]

        # Get the current schema (info about the users table)
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [info[1] for info in cursor.fetchall()]
        
        migrated = False
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                print(f"Migrating: Adding column '{column_name}' to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                migrated = True
            else:
                print(f"Migration check: Column '{column_name}' already exists.")

        if migrated:
            conn.commit()
            print("Migration complete: Security columns added.")
        else:
            print("Migration check: No new security columns were added.")

    except sqlite3.OperationalError as e:
        # This handles cases where the users table itself might not exist yet
        print(f"Migration error (users table likely missing or locked): {e}")
    except Exception as e:
        print(f"An unexpected error occurred during security column migration: {e}")
    finally:
        if conn:
            conn.close() # Always close the connection