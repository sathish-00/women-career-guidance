import sqlite3

def inspect_jobs():
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    
    print("--- Inspecting Job Vacancy Data ---")
    
    try:
        cursor.execute("SELECT id, name, total_labour_vacancy, is_vacant FROM career_options")
        rows = cursor.fetchall()
        
        if not rows:
            print("No jobs found in the database.")
        else:
            for row in rows:
                job_id, name, total_vacancies, is_vacant = row
                print(f"ID: {job_id}, Name: {name}, Total Vacancies: {total_vacancies}, Is Vacant: {is_vacant}")
                print(f"Type of Total Vacancies: {type(total_vacancies)}")
                
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}. The 'career_options' table might be missing or columns are incorrect.")
    
    finally:
        conn.close()

if __name__ == '__main__':
    inspect_jobs()
    