import sqlite3
from werkzeug.security import generate_password_hash

def reset_user_password(username, new_password):
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(new_password)
    
    try:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                       (hashed_password, username))
        conn.commit()
        print(f"Password for user '{username}' has been reset to '{new_password}'.")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == '__main__':
    reset_user_password('sathish', '12345678')