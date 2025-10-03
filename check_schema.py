import sqlite3

DATABASE_NAME = 'career_guidance.db'
TABLE_NAME = 'users'

try:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    print(f"--- Columns in '{TABLE_NAME}' table ---")
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    for column in cursor.fetchall():
        print(f"Column Name: {column[1]}, Type: {column[2]}, Is Primary Key: {'YES' if column[5] else 'NO'}")
    print("---------------------------------")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()