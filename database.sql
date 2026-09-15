CREATE DATABASE IF NOT EXISTS smart_job_portal;

USE smart_job_portal;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','recruiter','jobseeker') DEFAULT 'jobseeker',
    profile_pic VARCHAR(255) DEFAULT '',
    headline VARCHAR(150) DEFAULT '',
    phone VARCHAR(50) DEFAULT '',
    bio TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recruiter_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    company VARCHAR(150) NOT NULL,
    location VARCHAR(100),
    salary VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recruiter_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    applicant_id INT NOT NULL,
    resume VARCHAR(255),
    cover_letter TEXT DEFAULT NULL,
    applicant_phone VARCHAR(50) DEFAULT '',
    status ENUM('Applied','Shortlisted','Rejected','Selected') DEFAULT 'Applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (applicant_id) REFERENCES users(id)
);

INSERT INTO users (name, email, password, role, headline, bio)
VALUES
('System Admin', 'admin@gmail.com', 'admin123', 'admin', 'Portal Chief Administrator', 'Platform moderation and system settings.'),
('Sarah Jenkins', 'recruiter@example.com', 'recruiter123', 'recruiter', 'Senior Technical Talent Partner', 'Connecting stellar talent with top-tier companies.'),
('Alex Rivera', 'seeker@example.com', 'seeker123', 'jobseeker', 'Full-Stack Python & React Engineer', 'Experienced web engineer seeking high-impact roles.')
ON DUPLICATE KEY UPDATE name=VALUES(name);
