import io
import unittest
import uuid
from app import app, get_db

class SmartJobPortalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.uid = uuid.uuid4().hex[:6]
        self.jobseeker_email = f"seeker_{self.uid}@test.com"
        self.recruiter_email = f"recruiter_{self.uid}@test.com"

    def test_01_home_page_and_search(self):
        # Basic home page check
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Smart Job Portal", response.data)
        self.assertIn(b"Find Your Dream Job", response.data)

        # Keyword search query check
        search_res = self.client.get('/?q=Python')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b"Filtered by", search_res.data)

    def test_02_register_and_login_jobseeker_and_profile(self):
        # Register Job Seeker
        reg_res = self.client.post('/register', data={
            'name': f'Candidate {self.uid}',
            'email': self.jobseeker_email,
            'password': 'password123',
            'role': 'jobseeker'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)
        self.assertIn(b"Account created successfully", reg_res.data)

        # Login Job Seeker
        login_res = self.client.post('/login', data={
            'email': self.jobseeker_email,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Your Application History", login_res.data)

        # View Profile
        profile_res = self.client.get('/profile')
        self.assertEqual(profile_res.status_code, 200)
        self.assertIn(b"Edit Profile Information", profile_res.data)

        # Update Profile with avatar image
        fake_avatar = (io.BytesIO(b"fake_avatar_image_bytes"), "avatar.png")
        update_res = self.client.post('/profile', data={
            'name': f'Candidate {self.uid} Updated',
            'headline': 'Senior Cloud Architect',
            'phone': '+1 (555) 999-8888',
            'bio': 'Passionate cloud engineer with extensive distributed systems background.',
            'profile_pic': fake_avatar
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(update_res.status_code, 200)
        self.assertIn(b"profile and avatar have been updated", update_res.data)
        self.assertIn(b"Senior Cloud Architect", update_res.data)

    def test_03_recruiter_lifecycle_and_candidate_status_flow(self):
        # 1. Register Recruiter
        self.client.post('/register', data={
            'name': f'Recruiter {self.uid}',
            'email': self.recruiter_email,
            'password': 'password123',
            'role': 'recruiter'
        }, follow_redirects=True)

        # 2. Login Recruiter
        self.client.post('/login', data={
            'email': self.recruiter_email,
            'password': 'password123'
        }, follow_redirects=True)

        # 3. Post Job
        job_title = f"Principal Engineer {self.uid}"
        post_res = self.client.post('/post-job', data={
            'title': job_title,
            'company': 'InnovateTech Labs',
            'location': 'Seattle, WA',
            'salary': '$160,000 - $210,000',
            'description': 'Leading backend systems, architecture, and infrastructure scaling.'
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertIn(b"Job opening published successfully", post_res.data)

        # 4. Fetch Job Record ID
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id FROM jobs WHERE title=%s", (job_title,))
        job_record = cur.fetchone()
        cur.close()
        db.close()
        self.assertIsNotNone(job_record)
        job_id = job_record['id']

        # 5. Recruiter Edits Job
        edit_res = self.client.post(f'/job/{job_id}/edit', data={
            'title': job_title + " (Senior)",
            'company': 'InnovateTech Labs',
            'location': 'Remote / Seattle, WA',
            'salary': '$170,000 - $220,000',
            'description': 'Updated job description with expanded scope.'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        self.assertIn(b"Job listing updated successfully", edit_res.data)

        # 6. Logout Recruiter
        self.client.get('/logout')

        # 7. Register & Login Job Seeker to Apply
        applicant_email = f"applicant_{self.uid}@test.com"
        self.client.post('/register', data={
            'name': 'Taylor Swiftly',
            'email': applicant_email,
            'password': 'password123',
            'role': 'jobseeker'
        }, follow_redirects=True)
        self.client.post('/login', data={
            'email': applicant_email,
            'password': 'password123'
        }, follow_redirects=True)

        # 8. View Job Details
        view_res = self.client.get(f'/job/{job_id}')
        self.assertEqual(view_res.status_code, 200)
        self.assertIn(b"Submit Your Application", view_res.data)

        # 9. Apply with Resume and Cover Note
        resume_data = (io.BytesIO(b"PDF Resume content for candidate"), "taylor_resume.pdf")
        apply_res = self.client.post(f'/apply/{job_id}', data={
            'resume': resume_data,
            'applicant_phone': '+1 (555) 123-4567',
            'cover_letter': 'Excited about the InnovateTech mission and ready to contribute immediately.'
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(apply_res.status_code, 200)
        self.assertIn(b"Application Submitted", apply_res.data)

        # 10. Attempt duplicate apply (should show already submitted card)
        dup_view = self.client.get(f'/job/{job_id}')
        self.assertIn(b"Application Submitted", dup_view.data)

        # 11. Retrieve Application ID
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id FROM applications WHERE job_id=%s", (job_id,))
        app_record = cur.fetchone()
        cur.close()
        db.close()
        self.assertIsNotNone(app_record)
        app_id = app_record['id']

        # 12. Logout Applicant & Log in Recruiter to Update Status
        self.client.get('/logout')
        self.client.post('/login', data={
            'email': self.recruiter_email,
            'password': 'password123'
        }, follow_redirects=True)

        status_res = self.client.post(f'/application/{app_id}/status', data={
            'status': 'Shortlisted'
        }, follow_redirects=True)
        self.assertEqual(status_res.status_code, 200)
        self.assertIn(b"Shortlisted", status_res.data)

    def test_04_admin_dashboard(self):
        login_res = self.client.post('/login', data={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Total Registered Users", login_res.data)
        self.assertIn(b"All Platform Job Listings", login_res.data)

    def test_05_quick_demo_logins(self):
        # Test default seeded seeker login
        seeker_res = self.client.post('/login', data={
            'email': 'seeker@example.com',
            'password': 'seeker123'
        }, follow_redirects=True)
        self.assertEqual(seeker_res.status_code, 200)
        self.assertIn(b"Welcome back", seeker_res.data)

        # Test default seeded recruiter login
        recruiter_res = self.client.post('/login', data={
            'email': 'recruiter@example.com',
            'password': 'recruiter123'
        }, follow_redirects=True)
        self.assertEqual(recruiter_res.status_code, 200)
        self.assertIn(b"Recruiter Dashboard", recruiter_res.data)

    def test_06_dynamic_job_search_for_any_keyword(self):
        # 1. Test searching for diverse keywords
        test_queries = ["Java", "Data Scientist", "Cyber Security", "Accountant", "Google", "Flutter"]
        for q in test_queries:
            res = self.client.get(f'/?q={q}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Filtered by", res.data)
            self.assertIn(b"job-card", res.data)
            self.assertNotIn(b"No positions match your search criteria", res.data)

        # 2. Test searching by location
        loc_res = self.client.get('/?location=Hyderabad')
        self.assertEqual(loc_res.status_code, 200)
        self.assertIn(b"Filtered by", loc_res.data)
        self.assertIn(b"job-card", loc_res.data)

        # 3. Test combined query and location
        comb_res = self.client.get('/?q=React&location=Bengaluru')
        self.assertEqual(comb_res.status_code, 200)
        self.assertIn(b"Filtered by", comb_res.data)
        self.assertIn(b"job-card", comb_res.data)

    def test_07_search_suggestions_api(self):
        res = self.client.get('/api/search-suggestions?q=Py')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("suggestions", data)
        self.assertTrue(isinstance(data["suggestions"], list))

if __name__ == '__main__':
    unittest.main()
