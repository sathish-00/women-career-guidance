import sqlite3

conn = sqlite3.connect('career_guidance.db')
cursor = conn.cursor()
cursor.execute("UPDATE career_options SET is_vacant = 1 WHERE id = 15")
conn.commit()
conn.close()

print("Updated is_vacant for job id 15")
