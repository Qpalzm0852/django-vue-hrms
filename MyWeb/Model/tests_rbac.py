import secrets

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from Model.models import Department, JobPosition, EmployeeProfile, Payroll

User = get_user_model()


class RBACPermissionTest(TestCase):
    def setUp(self):
        # Setup Department and Position
        self.dept = Department.objects.create(name="IT Dept")
        self.position = JobPosition.objects.create(name="Developer", department=self.dept)

        # Setup Users
        self.password = secrets.token_urlsafe(24)
        self.admin = User.objects.create_user(user_id='admin', name='Admin User', password=self.password, role='ADMIN')
        self.hr = User.objects.create_user(user_id='hr', name='HR User', password=self.password, role='HR')
        self.staff_a = User.objects.create_user(user_id='staff_a', name='Staff A', password=self.password, role='STAFF')
        self.staff_b = User.objects.create_user(user_id='staff_b', name='Staff B', password=self.password, role='STAFF')

        # Setup Profiles
        EmployeeProfile.objects.create(user=self.admin, department=self.dept, position=self.position)
        EmployeeProfile.objects.create(user=self.hr, department=self.dept, position=self.position)
        EmployeeProfile.objects.create(user=self.staff_a, department=self.dept, position=self.position, base_salary=10000)
        EmployeeProfile.objects.create(user=self.staff_b, department=self.dept, position=self.position, base_salary=12000)

        # Setup Payrolls
        self.payroll_a = Payroll.objects.create(
            employee=self.staff_a, period='2024-01',
            base_pay=10000, net_pay=9000
        )
        self.payroll_b = Payroll.objects.create(
            employee=self.staff_b, period='2024-01',
            base_pay=12000, net_pay=11000
        )

        self.client = Client()

    def login_as(self, user):
        response = self.client.post("/login/", {"user_id": user.user_id, "password": self.password})
        self.assertEqual(response.status_code, 200)
        token = response.json()["data"]["token"]
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    @staticmethod
    def extract_items(response):
        if isinstance(response.data, dict):
            if 'results' in response.data:
                return response.data['results']
            if 'data' in response.data and isinstance(response.data['data'], list):
                return response.data['data']
        return response.data

    def test_payroll_access_admin(self):
        """Admin should see all payrolls"""
        self.login_as(self.admin)
        response = self.client.get('/api/payroll/')
        self.assertEqual(response.status_code, 200)
        items = self.extract_items(response)
        self.assertEqual(len(items), 2)  # Should see both A and B

    def test_payroll_access_staff_a(self):
        """Staff A should only see their own payroll"""
        self.login_as(self.staff_a)
        response = self.client.get('/api/payroll/')
        self.assertEqual(response.status_code, 200)
        items = self.extract_items(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['employee_id'], 'staff_a')

        # Verify sensitive fields are visible to owner
        self.assertIn('base_pay', items[0])
        self.assertEqual(float(items[0]['base_pay']), 10000.0)

    def test_payroll_access_staff_a_viewing_b(self):
        """Staff A trying to view Staff B's payroll directly should fail"""
        self.login_as(self.staff_a)
        response = self.client.get(f'/api/payroll/{self.payroll_b.id}/')
        # Should be 404 because it's filtered out of queryset
        self.assertEqual(response.status_code, 404)

    def test_profile_access_staff_a(self):
        """Staff A should only see their own profile in list"""
        self.login_as(self.staff_a)
        response = self.client.get('/api/employees/')
        self.assertEqual(response.status_code, 200)
        results = self.extract_items(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['user_id'], 'staff_a')

    def test_profile_access_admin(self):
        """Admin should see all profiles"""
        self.login_as(self.admin)
        response = self.client.get('/api/employees/')
        self.assertEqual(response.status_code, 200)
        results = self.extract_items(response)
        self.assertTrue(len(results) >= 4)

    def test_recruitment_access_staff_forbidden(self):
        """Staff should not access recruitment management endpoints"""
        self.login_as(self.staff_a)
        response = self.client.get('/api/recruitment-requirements/')
        self.assertEqual(response.status_code, 403)

    def test_training_write_staff_forbidden(self):
        """Staff should not create training records"""
        self.login_as(self.staff_a)
        response = self.client.post('/api/training/', {'title': 'security test'})
        self.assertEqual(response.status_code, 403)

