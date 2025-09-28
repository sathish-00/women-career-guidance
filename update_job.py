import sqlite3

def update_job_vacancies(job_id, new_vacancies):
    conn = sqlite3.connect('career_guidance.db')
    cursor = conn.cursor()
    
    is_vacant_status = 1 if new_vacancies > 0 else 0
    
    try:
        cursor.execute("UPDATE career_options SET total_labour_vacancy = ?, is_vacant = ? WHERE id = ?",
                       (new_vacancies, is_vacant_status, job_id))
        
        conn.commit()
        print(f"Updated job ID {job_id} to have {new_vacancies} vacancies.")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == '__main__':
    # Update job ID 29 (chicken cutter) to have 5 vacancies
    update_job_vacancies(29, 5)