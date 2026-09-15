import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash, send_from_directory, url_for
from werkzeug.utils import secure_filename
import mysql.connector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "smart_job_portal.db")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "smart_job_portal_secret_key_classic_2026")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx", "doc", "txt"}


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


# ---------------------------------------------------------
# Database Adapters (MySQL with transparent SQLite fallback)
# ---------------------------------------------------------
DB_ENGINE = None  # Will be 'mysql' or 'sqlite'


class SQLiteCursorAdapter:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, query, params=None):
        query = query.replace("%s", "?")
        if params is None:
            return self._cursor.execute(query)
        return self._cursor.execute(query, tuple(params))

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._dictionary:
            return [dict(row) for row in rows]
        return rows

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is not None and self._dictionary:
            return dict(row)
        return row

    def close(self):
        self._cursor.close()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount


class SQLiteConnectionAdapter:
    def __init__(self, conn):
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        return SQLiteCursorAdapter(self._conn.cursor(), dictionary=dictionary)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


DEFAULT_SEED_JOBS = [
    {
        "title": "Python Full Stack Developer",
        "company": "Acme Tech Solutions",
        "location": "Remote / Hybrid",
        "salary": "$90,000 - $125,000",
        "description": "We are seeking an enthusiastic Python developer proficient with Flask, FastAPI, modern JavaScript, and relational databases. Responsibilities include building RESTful services, integrating database models, and designing intuitive user experiences."
    },
    {
        "title": "Senior Java & Spring Boot Developer",
        "company": "Infosys Technologies",
        "location": "Hyderabad, India",
        "salary": "₹14,00,000 - ₹22,00,000",
        "description": "Architect enterprise microservices using Java 17, Spring Boot, Hibernate, Kafka, and PostgreSQL. Design high-throughput transactional backends and mentor junior engineers."
    },
    {
        "title": "Senior Frontend UI/UX Engineer",
        "company": "PixelCraft Studios",
        "location": "New York, NY",
        "salary": "$85,000 - $115,000",
        "description": "Looking for a creative frontend specialist with strong HTML5, CSS3, JavaScript, and modern responsive design experience to craft intuitive, accessible web interfaces."
    },
    {
        "title": "React & Next.js Web Developer",
        "company": "Cognizant Solutions",
        "location": "Bengaluru, India",
        "salary": "₹12,00,000 - ₹18,00,000",
        "description": "Develop high-performance Single Page Applications with React 18, Next.js, Redux Toolkit, and Tailwind CSS. Implement reusable UI component libraries and smooth client-side interactions."
    },
    {
        "title": "DevOps & Cloud Specialist",
        "company": "CloudSphere Inc.",
        "location": "Austin, TX",
        "salary": "$110,000 - $145,000",
        "description": "Lead our CI/CD pipelines, container orchestration with Docker and Kubernetes, and server performance monitoring. Expertise in Linux, Docker, Python scripting, and AWS/GCP security."
    },
    {
        "title": "Senior AI & Deep Learning Engineer",
        "company": "Google Partner Labs",
        "location": "Bengaluru, India",
        "salary": "₹22,00,000 - ₹38,00,000",
        "description": "Build cutting-edge generative AI models, LLM fine-tuning pipelines, RAG systems, and transformer architectures using PyTorch and Hugging Face. Optimize models for high-concurrency production deployments."
    },
    {
        "title": "Lead Data Scientist (Machine Learning)",
        "company": "Tata Consultancy Services (TCS)",
        "location": "Hyderabad, India",
        "salary": "₹18,00,000 - ₹28,00,000",
        "description": "Drive end-to-end predictive modeling, customer segmentation, and statistical data analysis using Python, Scikit-learn, XGBoost, and SQL. Present strategic insights to C-level stakeholders."
    },
    {
        "title": "Senior Data Analyst (PowerBI & SQL)",
        "company": "Deloitte Digital",
        "location": "Hyderabad, India",
        "salary": "₹10,00,000 - ₹16,00,000",
        "description": "Translate complex multi-source data into actionable business intelligence dashboards using advanced SQL, PowerBI, Tableau, and Excel analytics to drive strategic decision-making."
    },
    {
        "title": "AWS Cloud Solutions Architect",
        "company": "Amazon Web Services Partner",
        "location": "Hyderabad, India",
        "salary": "₹20,00,000 - ₹34,00,000",
        "description": "Design secure, resilient, and cost-optimized cloud architectures on AWS. Expertise in ECS, EKS, Lambda, Terraform, and cloud networking with high availability guarantees."
    },
    {
        "title": "Cyber Security Operations Analyst",
        "company": "Wipro Cybersecurity Hub",
        "location": "Pune, India",
        "salary": "₹11,00,000 - ₹17,00,000",
        "description": "Monitor and analyze security alerts, investigate vulnerabilities, conduct incident triage, and implement threat detection using SIEM and EDR tools to protect enterprise infrastructure."
    },
    {
        "title": "Senior Android App Developer (Kotlin)",
        "company": "Zoho Corporation",
        "location": "Chennai, India",
        "salary": "₹13,00,000 - ₹21,00,000",
        "description": "Build modern native Android mobile applications with Kotlin, Jetpack Compose, Coroutines, MVVM architecture, and offline SQLite caching with fluid animations."
    },
    {
        "title": "iOS Application Developer (Swift)",
        "company": "Apex Digital Labs",
        "location": "Bengaluru, India",
        "salary": "₹14,00,000 - ₹22,00,000",
        "description": "Design and engineer intuitive iOS apps using Swift, SwiftUI, Combine, and RESTful APIs, maintaining high standards of Apple Human Interface Guidelines."
    },
    {
        "title": "QA Automation Lead (Selenium / Cypress)",
        "company": "Accenture Interactive",
        "location": "Hyderabad, India",
        "salary": "₹12,00,000 - ₹19,00,000",
        "description": "Establish automated test frameworks for web and mobile apps using Selenium, Cypress, Playwright, Python/Java, and integrate continuous testing into CI/CD pipelines."
    },
    {
        "title": "Senior Product Manager (B2B SaaS)",
        "company": "InnovateTech Labs",
        "location": "Bengaluru, India",
        "salary": "₹24,00,000 - ₹38,00,000",
        "description": "Define product vision, roadmaps, and execution for enterprise SaaS platforms. Partner with engineering, UX design, and go-to-market teams to drive user retention."
    },
    {
        "title": "Lead UI/UX Product Designer",
        "company": "DesignMatrix Studio",
        "location": "Remote / Hybrid",
        "salary": "$80,000 - $110,000",
        "description": "Create engaging user journeys, wireframes, high-fidelity prototypes, and comprehensive design systems using Figma, Adobe XD, and user research methodologies."
    },
    {
        "title": "Senior Technical Recruiter & HR Partner",
        "company": "Global Talent Partners",
        "location": "Hyderabad, India",
        "salary": "₹8,00,000 - ₹14,00,000",
        "description": "Lead end-to-end recruitment for high-caliber engineering, AI, and leadership roles. Source top talent, manage recruitment funnels, and build strong talent pipelines."
    },
    {
        "title": "Corporate Financial Analyst & Accountant",
        "company": "Zenith Financial Services",
        "location": "Mumbai, India",
        "salary": "₹10,00,000 - ₹15,00,000",
        "description": "Manage financial planning, budgeting, variance analysis, monthly closing, and tax compliance. Advanced financial modeling and ERP experience required."
    },
    {
        "title": "Digital Marketing & Growth Manager",
        "company": "NextGen Media",
        "location": "Remote",
        "salary": "$70,000 - $95,000",
        "description": "Execute omni-channel growth marketing strategies across SEO, Google Ads, LinkedIn Ads, social media marketing, and conversion rate optimization to scale customer acquisition."
    },
    {
        "title": "Node.js & Microservices Backend Engineer",
        "company": "TechCorp Global Solutions",
        "location": "Pune, India",
        "salary": "₹13,00,000 - ₹19,00,000",
        "description": "Develop scalable event-driven backend services with Node.js, Express, NestJS, Redis, and MongoDB. Implement robust authentication and real-time WebSocket messaging."
    },
    {
        "title": "Site Reliability Engineer (SRE)",
        "company": "Microsoft Cloud Hub",
        "location": "Hyderabad, India",
        "salary": "₹18,00,000 - ₹26,00,000",
        "description": "Ensure ultra-high availability, automated monitoring, Prometheus/Grafana alerting, and zero-downtime deployments for global multi-tenant cloud platforms."
    },
    {
        "title": "Flutter Cross-Platform Developer",
        "company": "AppVantage Studios",
        "location": "Remote / Hyderabad",
        "salary": "₹11,00,000 - ₹17,00,000",
        "description": "Craft beautiful native-compiled iOS and Android apps using Dart and Flutter framework. Integrate REST APIs, state management via Bloc/Provider, and native device plugins."
    },
    {
        "title": "Senior Golang Distributed Systems Engineer",
        "company": "CloudSphere Systems",
        "location": "Bengaluru, India",
        "salary": "₹20,00,000 - ₹32,00,000",
        "description": "Build high-throughput, low-latency concurrent services in Go. Implement gRPC endpoints, distributed locking, Raft consensus, and Kafka event streaming."
    }
]


def init_sqlite_db():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'jobseeker',
            profile_pic TEXT DEFAULT '',
            headline TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            bio TEXT DEFAULT ''
        )
    """)

    # Schema migration for existing users table
    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = {col[1] for col in cursor.fetchall()}
    if "profile_pic" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT ''")
    if "headline" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN headline TEXT DEFAULT ''")
    if "phone" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''")
    if "bio" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recruiter_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            applicant_id INTEGER NOT NULL,
            resume TEXT,
            cover_letter TEXT DEFAULT '',
            applicant_phone TEXT DEFAULT '',
            status TEXT DEFAULT 'Applied',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (applicant_id) REFERENCES users(id)
        )
    """)

    # Schema migration for existing applications table
    cursor.execute("PRAGMA table_info(applications)")
    existing_app_cols = {col[1] for col in cursor.fetchall()}
    if "cover_letter" not in existing_app_cols:
        cursor.execute("ALTER TABLE applications ADD COLUMN cover_letter TEXT DEFAULT ''")
    if "applicant_phone" not in existing_app_cols:
        cursor.execute("ALTER TABLE applications ADD COLUMN applicant_phone TEXT DEFAULT ''")

    # Seed default Admin
    cursor.execute("SELECT id FROM users WHERE email='admin@gmail.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, email, password, role, headline, bio) VALUES (?, ?, ?, ?, ?, ?)",
            ("System Admin", "admin@gmail.com", "admin123", "admin", "Portal Chief Administrator", "Platform management and moderation.")
        )

    # Seed default Recruiter
    cursor.execute("SELECT id FROM users WHERE email='recruiter@example.com'")
    recruiter = cursor.fetchone()
    if not recruiter:
        cursor.execute(
            "INSERT INTO users (name, email, password, role, headline, bio) VALUES (?, ?, ?, ?, ?, ?)",
            ("Sarah Jenkins", "recruiter@example.com", "recruiter123", "recruiter", "Senior Technical Talent Partner", "Connecting stellar engineers with high-growth technology companies.")
        )
        recruiter_id = cursor.lastrowid
    else:
        recruiter_id = recruiter[0]

    # Seed default Job Seeker
    cursor.execute("SELECT id FROM users WHERE email='seeker@example.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, email, password, role, headline, bio) VALUES (?, ?, ?, ?, ?, ?)",
            ("Alex Rivera", "seeker@example.com", "seeker123", "jobseeker", "Full-Stack Python & React Engineer", "3+ years specializing in Flask, PostgreSQL, and high-performance frontend interfaces.")
        )

    # Sample jobs if empty or sparse
    cursor.execute("SELECT COUNT(*) FROM jobs")
    if cursor.fetchone()[0] < 15:
        for job in DEFAULT_SEED_JOBS:
            cursor.execute("SELECT id FROM jobs WHERE title = ? AND company = ?", (job["title"], job["company"]))
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO jobs (recruiter_id, title, company, location, salary, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        recruiter_id,
                        job["title"],
                        job["company"],
                        job["location"],
                        job["salary"],
                        job["description"]
                    )
                )

    conn.commit()
    conn.close()


def detect_and_init_db():
    global DB_ENGINE
    if os.environ.get("USE_SQLITE", "").lower() in ("1", "true", "yes"):
        DB_ENGINE = "sqlite"
        init_sqlite_db()
        return

    # Try connecting to MySQL
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_user = os.environ.get("MYSQL_USER", "root")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "")
    mysql_port = int(os.environ.get("MYSQL_PORT", 3306))
    mysql_database = os.environ.get("MYSQL_DATABASE", "smart_job_portal")

    try:
        test_conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            port=mysql_port,
            connection_timeout=2
        )
        cur = test_conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_database}`")
        cur.close()
        test_conn.close()

        db_conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            port=mysql_port,
            database=mysql_database
        )
        cur = db_conn.cursor()
        cur.execute("""
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
            )
        """)
        for col_name, col_def in [
            ("profile_pic", "VARCHAR(255) DEFAULT ''"),
            ("headline", "VARCHAR(150) DEFAULT ''"),
            ("phone", "VARCHAR(50) DEFAULT ''"),
            ("bio", "TEXT DEFAULT NULL")
        ]:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

        cur.execute("""
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
            )
        """)

        cur.execute("""
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
            )
        """)
        for col_name, col_def in [
            ("cover_letter", "TEXT DEFAULT NULL"),
            ("applicant_phone", "VARCHAR(50) DEFAULT ''")
        ]:
            try:
                cur.execute(f"ALTER TABLE applications ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

        # Seed default users
        cur.execute("SELECT id FROM users WHERE email='admin@gmail.com'")
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (name, email, password, role, headline, bio) VALUES (%s, %s, %s, %s, %s, %s)",
                ("System Admin", "admin@gmail.com", "admin123", "admin", "Portal Chief Administrator", "Platform management.")
            )
        cur.execute("SELECT id FROM users WHERE email='recruiter@example.com'")
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (name, email, password, role, headline, bio) VALUES (%s, %s, %s, %s, %s, %s)",
                ("Sarah Jenkins", "recruiter@example.com", "recruiter123", "recruiter", "Senior Technical Talent Partner", "Hiring top engineering talent.")
            )
        cur.execute("SELECT id FROM users WHERE email='seeker@example.com'")
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (name, email, password, role, headline, bio) VALUES (%s, %s, %s, %s, %s, %s)",
                ("Alex Rivera", "seeker@example.com", "seeker123", "jobseeker", "Full-Stack Python & React Engineer", "Passionate developer.")
            )

        # Seed default sample jobs for MySQL if empty or sparse
        cur.execute("SELECT COUNT(*) FROM jobs")
        if cur.fetchone()[0] < 15:
            cur.execute("SELECT id FROM users WHERE email='recruiter@example.com'")
            rec_row = cur.fetchone()
            mysql_rec_id = rec_row[0] if rec_row else 2
            for job in DEFAULT_SEED_JOBS:
                cur.execute("SELECT id FROM jobs WHERE title = %s AND company = %s", (job["title"], job["company"]))
                if not cur.fetchone():
                    cur.execute(
                        """
                        INSERT INTO jobs (recruiter_id, title, company, location, salary, description)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            mysql_rec_id,
                            job["title"],
                            job["company"],
                            job["location"],
                            job["salary"],
                            job["description"]
                        )
                    )

        db_conn.commit()
        cur.close()
        db_conn.close()

        DB_ENGINE = "mysql"
        print("[Database] Successfully connected to MySQL server.")
    except Exception as err:
        print(f"[Database] MySQL not available ({err}). Falling back to local SQLite database.")
        DB_ENGINE = "sqlite"
        init_sqlite_db()


def get_db():
    global DB_ENGINE
    if DB_ENGINE is None:
        detect_and_init_db()

    if DB_ENGINE == "mysql":
        return mysql.connector.connect(
            host=os.environ.get("MYSQL_HOST", "localhost"),
            user=os.environ.get("MYSQL_USER", "root"),
            password=os.environ.get("MYSQL_PASSWORD", ""),
            database=os.environ.get("MYSQL_DATABASE", "smart_job_portal"),
            port=int(os.environ.get("MYSQL_PORT", 3306))
        )
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        return SQLiteConnectionAdapter(conn)


# Initialize DB on load
detect_and_init_db()


@app.context_processor
def inject_globals():
    return {
        "current_user_pic": session.get("profile_pic", ""),
        "current_user_name": session.get("name", ""),
        "current_user_role": session.get("role", "")
    }


# ---------------------------------------------------------
# Dynamic Job Search & Generation Helpers
# ---------------------------------------------------------

KNOWN_COMPANIES = {
    "google": "Google India Technologies",
    "amazon": "Amazon Web Services (AWS)",
    "microsoft": "Microsoft Corporation",
    "tcs": "Tata Consultancy Services (TCS)",
    "tata": "Tata Consultancy Services (TCS)",
    "infosys": "Infosys Technologies",
    "wipro": "Wipro Digital",
    "accenture": "Accenture Global Services",
    "cognizant": "Cognizant Technology Solutions",
    "zoho": "Zoho Corporation",
    "deloitte": "Deloitte Digital",
    "oracle": "Oracle Cloud Systems",
    "ibm": "IBM India Technologies",
    "apple": "Apple Inc.",
    "meta": "Meta Platforms Inc.",
    "netflix": "Netflix Technology Labs",
    "flipkart": "Flipkart Internet Pvt Ltd",
    "swiggy": "Swiggy Technologies",
    "zomato": "Zomato Media Pvt Ltd",
    "hcl": "HCL Technologies",
    "capgemini": "Capgemini Solutions"
}

GENERAL_COMPANIES = [
    "Tata Consultancy Services (TCS)", "Infosys Technologies", "Accenture Global",
    "Cognizant Solutions", "Amazon Web Services", "Microsoft Tech Hub",
    "Google Cloud Partner", "Wipro Digital", "Zoho Corporation",
    "Deloitte Digital", "CloudSphere Inc.", "TechCorp Global Solutions"
]


def build_dynamic_titles(query_str, count=4):
    q_clean = (query_str or "").strip()
    if not q_clean:
        return [
            "Senior Full-Stack Software Engineer",
            "Cloud Solutions & DevOps Architect",
            "Lead Data Scientist & AI Specialist",
            "Technical Product & UI/UX Specialist"
        ][:count]

    lower_q = q_clean.lower()
    title_q = q_clean.title()

    seniority_prefixes = ["senior ", "sr ", "lead ", "principal ", "chief ", "head ", "junior ", "associate ", "staff "]
    has_prefix = any(lower_q.startswith(p) for p in seniority_prefixes)

    base_role = title_q
    if has_prefix:
        for p in seniority_prefixes:
            if lower_q.startswith(p):
                base_role = title_q[len(p):].strip()
                break

    profession_nouns = [
        "engineer", "developer", "specialist", "architect", "analyst",
        "manager", "consultant", "designer", "officer", "associate",
        "lead", "doctor", "physician", "nurse", "accountant", "auditor",
        "scientist", "administrator", "executive", "director", "writer",
        "recruiter", "tester", "technician", "operator", "lawyer"
    ]
    has_noun = any(noun in lower_q for noun in profession_nouns)

    if has_noun:
        titles = [
            f"Senior {base_role}",
            f"Lead {base_role}",
            f"Principal {base_role} Specialist",
            f"{base_role} (Immediate Hire)"
        ]
    else:
        if lower_q in ["ai", "ml", "nlp", "llm", "generative ai"]:
            titles = [
                f"Senior {title_q} Engineer",
                f"Lead {title_q} Research Scientist",
                f"{title_q} Solutions Architect",
                f"Principal {title_q} Platform Specialist"
            ]
        elif lower_q in ["marketing", "sales", "finance", "accounting", "hr", "operations", "legal"]:
            titles = [
                f"Senior {title_q} Manager",
                f"Lead {title_q} Specialist",
                f"{title_q} Strategy Director",
                f"Associate {title_q} Executive"
            ]
        else:
            titles = [
                f"Senior {title_q} Developer",
                f"Lead {title_q} Software Engineer",
                f"{title_q} Solutions Architect",
                f"Full-Stack {title_q} Specialist"
            ]

    return titles[:count]


def generate_dynamic_jobs_for_query(query="", location="", db=None, recruiter_id=None, count=4):
    """
    Dynamically generates realistic, high-quality job postings matching any search query and location,
    and inserts them into the database so they can be viewed, applied for, and managed.
    """
    if db is None:
        db = get_db()

    if recruiter_id is None:
        c = db.cursor(dictionary=True)
        c.execute("SELECT id FROM users WHERE role='recruiter' ORDER BY id ASC LIMIT 1")
        rec_row = c.fetchone()
        recruiter_id = rec_row["id"] if rec_row else 2
        c.close()

    q_clean = (query or "").strip()
    loc_clean = (location or "").strip()

    # Check if query matches a known company
    matched_company = None
    q_words = [w.lower() for w in q_clean.split()]
    for key, cname in KNOWN_COMPANIES.items():
        if key in q_words or key == q_clean.lower():
            matched_company = cname
            break

    if matched_company:
        titles = [
            "Senior Cloud Software Engineer",
            "Technical Solutions Architect",
            "Data & AI Systems Specialist",
            "Full-Stack DevOps Engineer"
        ][:count]
        companies = [matched_company] * count
    else:
        titles = build_dynamic_titles(q_clean, count=count)
        companies = [GENERAL_COMPANIES[i % len(GENERAL_COMPANIES)] for i in range(count)]

    if loc_clean:
        locations = [
            loc_clean,
            f"{loc_clean} (Hybrid)",
            f"{loc_clean} / Remote",
            loc_clean
        ]
    else:
        locations = [
            "Hyderabad, India",
            "Bengaluru, India",
            "Remote / Hybrid",
            "Pune, India"
        ]

    salaries = [
        "₹14,00,000 - ₹24,00,000 / yr",
        "₹12,00,000 - ₹20,00,000 / yr",
        "₹18,00,000 - ₹30,00,000 / yr",
        "₹10,00,000 - ₹16,00,000 / yr"
    ]

    cur = db.cursor()
    new_jobs = []
    for i in range(count):
        t = titles[i]
        c = companies[i]
        l = locations[i % len(locations)]
        s = salaries[i % len(salaries)]
        topic = q_clean if q_clean else "core software and distributed systems"
        d = (
            f"We are actively seeking a talented and driven {t} to join our high-impact team at {c} in {l}. "
            f"In this role, you will take ownership of critical features, build scalable solutions around {topic}, "
            f"collaborate with agile stakeholders, and drive technical excellence. "
            f"Qualifications: Proven hands-on experience with {topic}, strong analytical problem-solving skills, and a passion for engineering quality. "
            f"Benefits: Competitive salary package, health insurance, flexible working hours, and career advancement."
        )
        cur.execute("SELECT id FROM jobs WHERE title = %s AND company = %s", (t, c))
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO jobs (recruiter_id, title, company, location, salary, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (recruiter_id, t, c, l, s, d)
            )
            new_jobs.append({"title": t, "company": c, "location": l, "salary": s, "description": d})

    db.commit()
    cur.close()
    return new_jobs


def search_jobs_in_db(cursor, query="", location=""):
    q_clean = (query or "").strip()
    loc_clean = (location or "").strip()

    sql = "SELECT * FROM jobs"
    conditions = []
    params = []

    if q_clean:
        conditions.append("(LOWER(title) LIKE %s OR LOWER(company) LIKE %s OR LOWER(description) LIKE %s)")
        q_like = f"%{q_clean.lower()}%"
        params.extend([q_like, q_like, q_like])

    if loc_clean:
        conditions.append("LOWER(location) LIKE %s")
        params.append(f"%{loc_clean.lower()}%")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY created_at DESC"
    cursor.execute(sql, tuple(params) if params else None)
    results = cursor.fetchall()

    # Multi-term token matching if fewer than 3 results
    if len(results) < 3 and q_clean:
        words = [w.lower() for w in q_clean.split() if len(w) > 2 and w.lower() not in {"and", "for", "the", "with", "in", "at", "to", "or", "of"}]
        if len(words) > 1:
            token_conditions = []
            token_params = []
            for word in words:
                token_conditions.append("(LOWER(title) LIKE %s OR LOWER(company) LIKE %s OR LOWER(description) LIKE %s)")
                w_like = f"%{word}%"
                token_params.extend([w_like, w_like, w_like])

            token_sql = "SELECT * FROM jobs WHERE (" + " OR ".join(token_conditions) + ")"
            if loc_clean:
                token_sql += " AND LOWER(location) LIKE %s"
                token_params.append(f"%{loc_clean.lower()}%")
            token_sql += " ORDER BY created_at DESC"

            cursor.execute(token_sql, tuple(token_params))
            token_results = cursor.fetchall()
            seen_ids = {r["id"] for r in results}
            for r in token_results:
                if r["id"] not in seen_ids:
                    results.append(r)
                    seen_ids.add(r["id"])

    return results


# ---------------------------------------------------------
# Application Routes
# ---------------------------------------------------------

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id FROM users WHERE role='recruiter' ORDER BY id ASC LIMIT 1")
    rec_row = cursor.fetchone()
    recruiter_id = rec_row["id"] if rec_row else 2

    if query or location:
        jobs = search_jobs_in_db(cursor, query, location)

        # If fewer than 3 matching jobs found, dynamically generate matching jobs!
        if len(jobs) < 3:
            needed = max(4 - len(jobs), 3)
            generate_dynamic_jobs_for_query(
                query=query,
                location=location,
                db=db,
                recruiter_id=recruiter_id,
                count=needed
            )
            # Re-fetch matching jobs from DB so newly generated jobs are included
            jobs = search_jobs_in_db(cursor, query, location)
    else:
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50")
        jobs = cursor.fetchall()

    applied_job_ids = set()
    if "user_id" in session and session.get("role") == "jobseeker":
        cursor.execute("SELECT job_id FROM applications WHERE applicant_id = %s", (session["user_id"],))
        applied_job_ids = {row["job_id"] for row in cursor.fetchall()}

    cursor.close()
    db.close()

    return render_template(
        "index.html",
        jobs=jobs,
        query=query,
        location=location,
        applied_job_ids=applied_job_ids
    )


@app.route("/api/search-suggestions")
def search_suggestions():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return {"suggestions": []}
    db = get_db()
    cursor = db.cursor(dictionary=True)
    like_term = f"%{q.lower()}%"
    cursor.execute(
        "SELECT DISTINCT title FROM jobs WHERE LOWER(title) LIKE %s LIMIT 6",
        (like_term,)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    suggestions = [r["title"] for r in rows]
    return {"suggestions": suggestions}


@app.route("/register", methods=["GET", "POST"])
def register():
    next_page = request.args.get("next", "").strip()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "jobseeker").strip()
        next_param = request.form.get("next", "").strip()

        if not name or not email or not password:
            flash("All required fields must be filled.")
            return render_template("register.html", next=next_page)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users(name, email, password, role)
                VALUES(%s, %s, %s, %s)
                """,
                (name, email, password, role)
            )
            db.commit()
            cursor.close()
            db.close()

            flash("Account created successfully! Please sign in.")
            if next_param and next_param.startswith("/"):
                return redirect(url_for("login", next=next_param))
            return redirect("/login")

        except Exception:
            cursor.close()
            db.close()
            flash("That email address is already registered. Please sign in or use another email.")

    return render_template("register.html", next=next_page)


@app.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next", "").strip()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        next_param = request.form.get("next", "").strip()

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE LOWER(email)=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            session["profile_pic"] = user.get("profile_pic") or ""

            flash(f"Welcome back, {user['name']}!")
            if next_param and next_param.startswith("/"):
                return redirect(next_param)
            return redirect("/dashboard")

        flash("Invalid email address or password. Please verify and try again.")

    return render_template("login.html", next=next_page)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in to manage your profile.")
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()
        flash("User profile not found.")
        return redirect("/login")

    # Gather user statistics for profile display
    stats = {"applications_count": 0, "jobs_posted_count": 0}
    if user["role"] == "jobseeker":
        cursor.execute("SELECT COUNT(*) AS total FROM applications WHERE applicant_id = %s", (user["id"],))
        res = cursor.fetchone()
        stats["applications_count"] = res["total"] if res else 0
    elif user["role"] == "recruiter":
        cursor.execute("SELECT COUNT(*) AS total FROM jobs WHERE recruiter_id = %s", (user["id"],))
        res = cursor.fetchone()
        stats["jobs_posted_count"] = res["total"] if res else 0

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        headline = request.form.get("headline", "").strip()
        phone = request.form.get("phone", "").strip()
        bio = request.form.get("bio", "").strip()
        remove_pic = request.form.get("remove_pic") == "1"

        if not name:
            flash("Full name cannot be blank.")
            cursor.close()
            db.close()
            return render_template("profile.html", user=user, stats=stats)

        profile_pic_name = user.get("profile_pic") or ""

        if remove_pic:
            profile_pic_name = ""

        # Handle uploaded avatar image
        pic_file = request.files.get("profile_pic")
        if pic_file and pic_file.filename:
            if allowed_file(pic_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                clean_name = secure_filename(pic_file.filename)
                profile_pic_name = f"avatar_{user['id']}_{clean_name}"
                pic_file.save(os.path.join(app.config["UPLOAD_FOLDER"], profile_pic_name))
            else:
                flash("Invalid image type. Please upload JPG, PNG, WEBP, or GIF.")
                cursor.close()
                db.close()
                return render_template("profile.html", user=user, stats=stats)

        update_cursor = db.cursor()
        update_cursor.execute(
            """
            UPDATE users
            SET name = %s, headline = %s, phone = %s, bio = %s, profile_pic = %s
            WHERE id = %s
            """,
            (name, headline, phone, bio, profile_pic_name, user["id"])
        )
        db.commit()
        update_cursor.close()

        # Update session values
        session["name"] = name
        session["profile_pic"] = profile_pic_name

        cursor.close()
        db.close()

        flash("Your profile and avatar have been updated successfully!")
        return redirect("/profile")

    cursor.close()
    db.close()
    return render_template("profile.html", user=user, stats=stats)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access your dashboard.")
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Current user info
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    current_user = cursor.fetchone()

    if session["role"] == "recruiter":
        cursor.execute(
            "SELECT * FROM jobs WHERE recruiter_id=%s ORDER BY created_at DESC",
            (session["user_id"],)
        )
        jobs = cursor.fetchall()

        cursor.execute(
            """
            SELECT applications.id, applications.resume, applications.cover_letter,
                   applications.applicant_phone, applications.status, applications.applied_at,
                   users.name AS applicant_name, users.email AS applicant_email,
                   users.profile_pic AS applicant_pic, users.headline AS applicant_headline,
                   jobs.id AS job_id, jobs.title AS job_title
            FROM applications
            JOIN jobs ON applications.job_id = jobs.id
            JOIN users ON applications.applicant_id = users.id
            WHERE jobs.recruiter_id=%s
            ORDER BY applications.applied_at DESC
            """,
            (session["user_id"],)
        )
        applications = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template(
            "dashboard.html",
            user=current_user,
            jobs=jobs,
            applications=applications
        )

    elif session["role"] == "jobseeker":
        cursor.execute(
            """
            SELECT applications.*, jobs.title, jobs.company, jobs.location, jobs.salary
            FROM applications
            JOIN jobs ON applications.job_id = jobs.id
            WHERE applications.applicant_id=%s
            ORDER BY applications.applied_at DESC
            """,
            (session["user_id"],)
        )
        applications = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template(
            "dashboard.html",
            user=current_user,
            applications=applications
        )

    else:
        # Admin view
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        users_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) AS total FROM jobs")
        jobs_count = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) AS total FROM applications")
        applications_count = cursor.fetchone()

        cursor.execute("SELECT id, name, email, role, profile_pic, headline FROM users ORDER BY id DESC")
        all_users = cursor.fetchall()

        cursor.execute(
            """
            SELECT jobs.*, users.name AS recruiter_name
            FROM jobs
            JOIN users ON jobs.recruiter_id = users.id
            ORDER BY jobs.created_at DESC
            """
        )
        all_jobs = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template(
            "dashboard.html",
            user=current_user,
            users=users_count["total"] if users_count else 0,
            jobs=jobs_count["total"] if jobs_count else 0,
            applications=applications_count["total"] if applications_count else 0,
            all_users=all_users,
            all_jobs=all_jobs
        )


@app.route("/post-job", methods=["GET", "POST"])
def post_job():
    if "user_id" not in session or session.get("role") != "recruiter":
        flash("Only registered recruiters can post job openings.")
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not company or not description:
            flash("Title, company, and description are required.")
            return render_template("post_job.html", is_edit=False)

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO jobs (recruiter_id, title, company, location, salary, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (session["user_id"], title, company, location, salary, description)
        )

        db.commit()
        cursor.close()
        db.close()

        flash("Job opening published successfully!")
        return redirect("/dashboard")

    return render_template("post_job.html", is_edit=False)


@app.route("/job/<int:job_id>/edit", methods=["GET", "POST"])
def edit_job(job_id):
    if "user_id" not in session or session.get("role") != "recruiter":
        flash("Only recruiters can edit job postings.")
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM jobs WHERE id = %s AND recruiter_id = %s",
        (job_id, session["user_id"])
    )
    job = cursor.fetchone()

    if not job:
        cursor.close()
        db.close()
        flash("Job posting not found or you are not authorized to edit it.")
        return redirect("/dashboard")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not company or not description:
            flash("Title, company, and description are required.")
            cursor.close()
            db.close()
            return render_template("post_job.html", job=job, is_edit=True)

        up_cur = db.cursor()
        up_cur.execute(
            """
            UPDATE jobs
            SET title = %s, company = %s, location = %s, salary = %s, description = %s
            WHERE id = %s AND recruiter_id = %s
            """,
            (title, company, location, salary, description, job_id, session["user_id"])
        )
        db.commit()
        up_cur.close()
        cursor.close()
        db.close()

        flash("Job listing updated successfully!")
        return redirect("/dashboard")

    cursor.close()
    db.close()
    return render_template("post_job.html", job=job, is_edit=True)


@app.route("/job/<int:job_id>/delete", methods=["POST"])
def delete_job(job_id):
    if "user_id" not in session or session.get("role") not in ("recruiter", "admin"):
        flash("Unauthorized action.")
        return redirect("/dashboard")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if session.get("role") == "admin":
        cursor.execute("SELECT id, title FROM jobs WHERE id = %s", (job_id,))
    else:
        cursor.execute("SELECT id, title FROM jobs WHERE id = %s AND recruiter_id = %s", (job_id, session["user_id"]))
    job = cursor.fetchone()

    if not job:
        cursor.close()
        db.close()
        flash("Job posting not found or unauthorized.")
        return redirect("/dashboard")

    del_cur = db.cursor()
    del_cur.execute("DELETE FROM applications WHERE job_id = %s", (job_id,))
    del_cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
    db.commit()
    del_cur.close()
    cursor.close()
    db.close()

    flash(f"Job '{job['title']}' and its associated applications have been deleted.")
    return redirect("/dashboard")


@app.route("/job/<int:job_id>")
def job_details(job_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT jobs.*, users.name AS recruiter_name, users.profile_pic AS recruiter_pic
        FROM jobs
        JOIN users ON jobs.recruiter_id = users.id
        WHERE jobs.id = %s
        """,
        (job_id,)
    )
    job = cursor.fetchone()

    has_applied = False
    application_record = None

    if job and "user_id" in session and session.get("role") == "jobseeker":
        cursor.execute(
            "SELECT * FROM applications WHERE job_id = %s AND applicant_id = %s",
            (job_id, session["user_id"])
        )
        application_record = cursor.fetchone()
        if application_record:
            has_applied = True

    cursor.close()
    db.close()

    if not job:
        flash("The requested job listing was not found.")
        return redirect("/")

    return render_template(
        "job_details.html",
        job=job,
        has_applied=has_applied,
        application_record=application_record
    )


@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    if "user_id" not in session:
        flash("Please sign in as a job seeker to submit your application.")
        return redirect(f"/login?next=/job/{job_id}")

    if session.get("role") != "jobseeker":
        flash("Only job seeker accounts can submit applications.")
        return redirect(f"/job/{job_id}")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    if not job:
        cursor.close()
        db.close()
        flash("The job opening you are applying for does not exist.")
        return redirect("/")

    # Duplicate check
    cursor.execute(
        "SELECT id FROM applications WHERE job_id = %s AND applicant_id = %s",
        (job_id, session["user_id"])
    )
    if cursor.fetchone():
        cursor.close()
        db.close()
        flash("You have already submitted an application for this position.")
        return redirect(f"/job/{job_id}")

    resume = request.files.get("resume")
    cover_letter = request.form.get("cover_letter", "").strip()
    applicant_phone = request.form.get("applicant_phone", "").strip()
    filename = ""

    if resume and resume.filename:
        if allowed_file(resume.filename, ALLOWED_RESUME_EXTENSIONS):
            clean_name = secure_filename(resume.filename)
            filename = f"resume_{session['user_id']}_{clean_name}"
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        else:
            cursor.close()
            db.close()
            flash("Invalid resume format. Please upload PDF, DOCX, DOC, or TXT file.")
            return redirect(f"/job/{job_id}")

    write_cursor = db.cursor()
    write_cursor.execute(
        """
        INSERT INTO applications (job_id, applicant_id, resume, cover_letter, applicant_phone, status)
        VALUES (%s, %s, %s, %s, %s, 'Applied')
        """,
        (job_id, session["user_id"], filename, cover_letter, applicant_phone)
    )

    db.commit()
    write_cursor.close()
    cursor.close()
    db.close()

    flash(f"Congratulations! Your application for '{job['title']}' has been successfully submitted.")
    return redirect(f"/job/{job_id}")


@app.route("/application/<int:app_id>/status", methods=["POST"])
def update_application_status(app_id):
    if "user_id" not in session or session.get("role") != "recruiter":
        flash("Unauthorized action.")
        return redirect("/dashboard")

    new_status = request.form.get("status", "").strip()
    if new_status not in ["Applied", "Shortlisted", "Selected", "Rejected"]:
        flash("Invalid status selection.")
        return redirect("/dashboard")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT applications.id, users.name AS applicant_name, jobs.title AS job_title
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN users ON applications.applicant_id = users.id
        WHERE applications.id = %s AND jobs.recruiter_id = %s
        """,
        (app_id, session["user_id"])
    )
    application = cursor.fetchone()

    if not application:
        cursor.close()
        db.close()
        flash("Application not found or unauthorized.")
        return redirect("/dashboard")

    up_cur = db.cursor()
    up_cur.execute(
        "UPDATE applications SET status = %s WHERE id = %s",
        (new_status, app_id)
    )
    db.commit()
    up_cur.close()
    cursor.close()
    db.close()

    flash(f"Candidate {application['applicant_name']} marked as '{new_status}' for {application['job_title']}.")
    return redirect("/dashboard")


@app.route("/application/<int:app_id>/withdraw", methods=["POST"])
def withdraw_application(app_id):
    if "user_id" not in session or session.get("role") != "jobseeker":
        flash("Unauthorized action.")
        return redirect("/dashboard")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT applications.id, jobs.title
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = %s AND applications.applicant_id = %s
        """,
        (app_id, session["user_id"])
    )
    application = cursor.fetchone()

    if not application:
        cursor.close()
        db.close()
        flash("Application not found.")
        return redirect("/dashboard")

    del_cur = db.cursor()
    del_cur.execute("DELETE FROM applications WHERE id = %s", (app_id,))
    db.commit()
    del_cur.close()
    cursor.close()
    db.close()

    flash(f"Your application for '{application['title']}' has been withdrawn.")
    return redirect("/dashboard")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    safe_name = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.")
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f" * Smart Job Portal starting on http://127.0.0.1:{port}")
    app.run(debug=True, host="127.0.0.1", port=port)
