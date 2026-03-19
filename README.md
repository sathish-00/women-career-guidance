# 🌾 Rural Women's Career Guidance Platform

> 🚀 A full-stack AI-powered web application that provides career guidance, job opportunities, and skill-based learning for rural women.

---

## 📌 Overview
This project is designed to empower rural women by connecting them with job opportunities, career guidance, and skill development resources. The platform uses AI assistance, job filtering, and admin-based job postings to create a complete career ecosystem.

---

## 🎯 Features

### 👩‍💼 User Features
- Secure Registration & Login system  
- Personalized job recommendations based on skills  
- Apply for jobs with resume upload  
- Dashboard showing relevant opportunities  
- Skill-based job filtering system  
- AI Career Assistant for guidance  
- Career videos using YouTube API  
- Download application receipts (PDF)  

---

### 🏢 Admin Features
- Admin registration with verification system  
- Job posting and vacancy management  
- Admin dashboard with:
  - Vacancy tracking  
  - Applications received  
- Edit/Delete job postings  
- View applicants and resumes  

---

### 🤖 AI Features
- AI chatbot for career guidance (Gemini API)  
- Suggests skills, interview tips, and career paths  
- Smart responses with fallback search  

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)  
- **Database:** SQLite  
- **Frontend:** HTML, CSS, JavaScript  
- **Authentication:** Flask-Login  
- **AI Integration:** Google Gemini API  
- **Video Integration:** YouTube Data API  
- **Security:** reCAPTCHA, password hashing  
- **PDF Generation:** WeasyPrint  

---

## 🧠 How It Works

1. Users register and select their skills  
2. System matches jobs based on skills  
3. Admins post jobs and manage vacancies  
4. Users apply for jobs and upload resumes  
5. AI chatbot helps users with career guidance  
6. Users can learn skills through video recommendations  

---

## 📂 Project Structure
project/
│── app.py
│── templates/
│── static/
│── uploads/
│── database/


---

## 🚀 How to Run the Project

1. Clone the repository
```bash
git clone https://github.com/yourusername/project-name.git
cd carrer_guide
pip install -r requirements.txt
python app.py
http://127.0.0.1:5000
