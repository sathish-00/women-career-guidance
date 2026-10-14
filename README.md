<div align="center">

<img src="https://github.com/user-attachments/assets/ffe53909-14ee-4746-a97b-a48d1895870c" alt="Rural Women's Job Discovery & Career Guidance Platform" width="700"/>

# Rural Women's Job Discovery & Career Guidance Platform

**An AI-powered full-stack platform that helps rural women discover the latest jobs matched to their skills, prepare for interviews, and learn new skills through guided career support.**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge)](https://women-career-guidance.onrender.com)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)

[Live Demo](https://women-career-guidance.onrender.com) · [Aim](#aim) · [Features](#features) · [Getting Started](#getting-started) · [Screenshots](#screenshots)

</div>

> **Note:** The demo is hosted on a free tier, so the first load may take 30-60 seconds while the server wakes up.

---

## Overview

Women in rural areas often lack access to job listings, career advice, and skill-building resources. This platform brings them together in one place:

- **Job seekers** register, select their skills, receive matched job recommendations, and apply with a resume.
- **Admins** post vacancies, track applications, and review applicants.
- **A Gemini-powered AI assistant** gives career guidance, interview preparation, skill suggestions, and career-path advice.
- **Curated YouTube videos** help users learn new skills.

---

## Aim

The aim of this project is to **empower rural women with equal access to employment and career growth** by:

- Making relevant, up-to-date job opportunities easy to find, with no long searches through outdated listings.
- Matching women to jobs that fit their skills, so they apply with confidence.
- Keeping the job board accurate: once a vacancy is filled, the post is **automatically removed**, so users never waste time on positions that are no longer open.
- Offering personalized career advice and interview preparation through AI.
- Helping women build new skills through free, guided learning resources.
- Giving admins and employers simple tools to post jobs, manage vacancies, and review applicants.

### The Problem
Limited awareness of suitable jobs, outdated or closed listings, little access to career mentors, and few affordable learning resources keep many rural women out of formal employment.

### The Solution
A single, easy-to-use web platform that shows only the **latest open vacancies**, filters them by skill, guides users with AI, and points them to free learning content, while giving admins simple tools to manage the full hiring flow.

---

## Features

### For Users
- Secure registration and login
- Skill selection during registration
- Personalized job recommendations based on selected skills
- Latest job vacancies shown first, with only open positions displayed
- Smart filtering to narrow jobs by skill and other criteria
- Apply for jobs with resume upload
- Dashboard showing relevant opportunities
- AI Career Assistant for guidance
- Career and skill-learning videos via the YouTube Data API
- Downloadable PDF application receipts

### For Admins
- Admin registration with a verification system
- Post, edit, and delete job listings
- Vacancy management with a set number of openings per post
- **Automatic post removal:** when all vacancies for a job are filled, the post is deleted automatically, keeping the board current
- Dashboard with vacancy tracking and applications received
- View applicants and review their resumes

### AI Assistant
- Career guidance chatbot powered by the **Google Gemini API**
- Suggests skills, career paths, and interview tips
- Fallback search when the AI cannot give a direct answer
- **In progress:** deeper LLM integration to give more personalized, context-aware career advice based on each user's skills, goals, and applications

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Authentication | Flask-Login |
| AI / LLM | Google Gemini API |
| Video | YouTube Data API |
| Security | reCAPTCHA, password hashing |
| PDF generation | WeasyPrint |
| Deployment | Render |

---

## How It Works

1. Users register and select their skills.
2. The system matches jobs to those skills and shows the latest open vacancies first.
3. Users filter the listings to find the best fit.
4. Admins post jobs and set the number of vacancies.
5. Users apply and upload resumes.
6. Admins review applicants and select candidates.
7. Once all vacancies are filled, the job post is automatically removed.
8. The AI chatbot and learning videos support users with career advice and skill-building throughout.

---

## Project Structure

```
rural-women-career-platform/
├── app.py            # Main Flask application
├── templates/        # HTML templates
├── static/           # CSS, JS, images
├── uploads/          # Uploaded resumes
├── database/         # SQLite database
├── requirements.txt  # Python dependencies
└── .env.example      # Environment variable template
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- API keys for Google Gemini, YouTube Data API, and Google reCAPTCHA
- System libraries required by WeasyPrint ([installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/sathish-00/rural-women-career-platform.git
cd rural-women-career-platform

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env            # Then add your API keys

# 5. Run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Screenshots

| Home | Register |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/493d3837-7eed-48ef-b829-8be666082d1f" width="400"/> | <img src="https://github.com/user-attachments/assets/ade09f74-c809-4d24-ac6c-fe3ccfadebf4" width="400"/> |

| Career Options | AI Assistant |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/e1d76742-bdbd-42d8-a224-574694479e83" width="400"/> | <img src="https://github.com/user-attachments/assets/5d5f0716-9c24-4c00-8551-69d4abb4685b" width="400"/> |

| Admin Dashboard | Applications |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/0b8323ca-2d3e-4600-8237-1b895498b3f8" width="400"/> | <img src="https://github.com/user-attachments/assets/420ba6c8-7fba-44c3-8370-0e0e3dd9f8d5" width="400"/> |

<details>
<summary><b>View more screenshots</b></summary>

<br>

| Admin Registration | Admin Dashboard (Vacancies) |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/ac198b3c-47b7-4ad6-8952-8c773a080052" width="400"/> | <img src="https://github.com/user-attachments/assets/617f37e4-ab7a-4c10-99c9-e0184e1544a1" width="400"/> |

| AI Chatbot | Register (Skills) |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/34f4b789-032a-4127-a291-6e7c644ee324" width="400"/> | <img src="https://github.com/user-attachments/assets/7144fe70-ee7c-4783-b40d-6b7e43599e5b" width="400"/> |

| Admin Registration (Verification) | Contact Us |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/ed912983-650d-4226-8176-69ecb15242c6" width="400"/> | <img src="https://github.com/user-attachments/assets/c4a85a39-dd7a-4943-b01f-0589f2b379c2" width="400"/> |

</details>

---

## Security

- Password hashing
- reCAPTCHA protection on forms
- Role-based access control (user vs. admin)
- Admin accounts require verification

---

## Future Improvements

- [ ] Complete the advanced LLM integration for personalized career advice (in progress)
- [ ] Multi-language support (Telugu, Hindi, and more)
- [ ] Voice input for the AI chatbot
- [ ] Real-time job notifications
- [ ] Advanced AI-based job recommendations
- [ ] Mobile application
- [ ] PostgreSQL and persistent cloud storage for production use

---

## Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Sathish Kodari**
Computer Science student, Vardhaman College of Engineering

[![GitHub](https://img.shields.io/badge/GitHub-sathish--00-181717?style=flat&logo=github)](https://github.com/sathish-00)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-sathish--kodari00-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/sathish-kodari00)

<div align="center">

If you found this project useful, consider giving it a star.

</div>
