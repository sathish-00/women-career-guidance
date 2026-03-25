import sqlite3

def find_and_update():
    db_name = 'career_guidance.db' # Make sure this matches your get_db()
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # This finds all tables in your database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print(f"❌ The file '{db_name}' is empty or has no tables.")
        return

    print(f"Found these tables: {tables}")
    
    # We will try to update 'users' or 'user' - whichever one exists
    target_table = None
    for t in tables:
        if t[0].lower() in ['users', 'user']:
            target_table = t[0]
            break

    if target_table:
        print(f"Targeting table: {target_table}")
        new_columns = [
            f"ALTER TABLE {target_table} ADD COLUMN is_verified INTEGER DEFAULT 0",
            f"ALTER TABLE {target_table} ADD COLUMN shop_name TEXT",
            f"ALTER TABLE {target_table} ADD COLUMN business_license TEXT"
        ]
        for cmd in new_columns:
            try:
                cursor.execute(cmd)
                conn.commit()
                print(f"✅ Executed: {cmd}")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Skipped: {e}")
    else:
        print("❌ Could not find a table named 'users' or 'user'.")

    conn.close()


def update_db():
    db = get_db()
    # List of new columns to add for Admin Verification
    new_columns = [
        "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'pending'",
        "ALTER TABLE users ADD COLUMN shop_name TEXT",
        "ALTER TABLE users ADD COLUMN voter_id TEXT",
        "ALTER TABLE users ADD COLUMN verification_doc TEXT"
    ]

    for sql in new_columns:
        try:
            db.execute(sql)
            print(f"Success: {sql}")
        except sqlite3.OperationalError:
            # This happens if the column is already there, which is fine!
            print(f"Skipped (already exists): {sql}")
    
    db.commit()

if __name__ == '__main__':
    find_and_update()