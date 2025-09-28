import sqlite3

def check_all_users():
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    
    try:
        print("--- All Users in the Database ---")
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()

        if not users:
            print("No users found in the database.")
        else:
            for user in users:
                print(f"Username: {user[0]}, Role: {user[1]}")

    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
    
    finally:
        conn.close()

if __name__ == '__main__':
    check_all_users()