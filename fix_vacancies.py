import sqlite3

def fix_database_vacancies():
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    
    try:
        # Update all jobs where total_labour_vacancy is 0
        cursor.execute("UPDATE career_options SET is_vacant = 0 WHERE total_labour_vacancy = 0")
        
        # Update all jobs where total_labour_vacancy is greater than 0
        cursor.execute("UPDATE career_options SET is_vacant = 1 WHERE total_labour_vacancy > 0")
        
        conn.commit()
        print(f"Database update successful. Fixed {cursor.rowcount} rows.")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_vacancies()