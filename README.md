# Smart Job Portal & Recruitment Management System

A web-based career and recruitment management portal built with **Flask**, **Python 3**, and **Bootstrap 5**, featuring role-based dashboards for Job Seekers, Recruiters, and Administrators.

---

## 🌟 Key Features

- **Profile Picture & Professional Identity**:
  - Upload, update, and preview custom avatar photos (JPG, PNG, WEBP, GIF).
  - Manage headline, contact phone, and professional bio at `/profile`.
  - Avatar display in navigation bar, dashboards, and recruiter applicant reviews.

- **Classic Luxury Animated Login Experience**:
  - Ambient floating glowing orbs with fluid CSS keyframe animations.
  - Classic glassmorphic luxury card with animated gradient top accent.
  - Interactive show/hide password toggle.
  - **1-Click Quick Demo Sign-In** pills for instant testing (Job Seeker, Recruiter, Admin).
  - Error shake animation on failed attempts.

- **Complete Job Application Lifecycle**:
  - Multi-format resume upload (PDF, DOCX, DOC, TXT), contact phone, and optional cover note.
  - Real-time application tracking with color-coded status badges (`Applied`, `Shortlisted`, `Selected`, `Rejected`).
  - Duplicate application prevention and status preview on job details page.
  - Candidates can withdraw pending applications.
  - Recruiters can review resumes, read cover letters, and update candidate statuses with 1 click.

- **Job Search & Management**:
  - Live keyword (title, company, skills) and location search filtering on home page.
  - Recruiters can publish, edit, and delete job postings.

- **Dual Database Support**:
  - Connects to **MySQL** if available on `localhost:3306`.
  - Seamlessly falls back to an embedded **SQLite** database (`smart_job_portal.db`) with automatic schema migration and zero setup.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- Dependencies in `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Run Automated Tests
```bash
python test_app.py
```

---

## 🔑 Default Demo Accounts

| Role | Email | Password | Quick Action |
| :--- | :--- | :--- | :--- |
| **Job Seeker** | `seeker@example.com` | `seeker123` | Click "Job Seeker" pill on login page |
| **Recruiter** | `recruiter@example.com` | `recruiter123` | Click "Recruiter" pill on login page |
| **Admin** | `admin@gmail.com` | `admin123` | Click "Admin" pill on login page |

*New Job Seekers and Recruiters can also be registered at `/register`.*

---

## 📁 Project Structure

```
.
├── app.py                 # Core Flask backend, database adapter & routes
├── requirements.txt       # Python dependencies
├── database.sql           # MySQL database schema & seed data
├── test_app.py            # Automated test suite
├── README.md              # Project documentation
├── templates/             # Jinja2 HTML templates
│   ├── index.html         # Job portal home & keyword search
│   ├── login.html         # Classic animated luxury login
│   ├── register.html      # Registration page
│   ├── profile.html       # Profile picture upload & bio management
│   ├── dashboard.html     # Role-based dashboard (Jobseeker/Recruiter/Admin)
│   ├── job_details.html   # Job view, status banner & application form
│   └── post_job.html      # Recruiter job posting & editing form
├── static/
│   ├── css/style.css      # Custom styling & keyframe animations
│   └── uploads/           # Uploaded resumes and profile avatars
└── smart_job_portal.db    # SQLite database (auto-generated fallback)
```
