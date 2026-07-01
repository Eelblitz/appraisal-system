from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import UserProfile
from appraisal_project.test_utils import create_organisation, create_user, create_full_setup


class UserProfileModelTest(TestCase):

    def setUp(self):
        self.org = create_organisation()
        self.user = create_user('testuser', 'employee', self.org)

    def test_profile_created_with_correct_role(self):
        self.assertEqual(self.user.profile.role, 'employee')

    def test_profile_linked_to_organisation(self):
        self.assertEqual(self.user.profile.organisation, self.org)

    def test_reporting_officer_assignment(self):
        officer = create_user('officer1', 'reporting_officer', self.org)
        self.user.profile.reporting_officer = officer.profile
        self.user.profile.save()
        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.reporting_officer,
            officer.profile
        )

    def test_string_representation(self):
        result = str(self.user.profile)
        self.assertIn('employee', result.lower())


class UserProfileViewTest(TestCase):

    def setUp(self):
        """
        Create test users using create_full_setup.
        We use the returned prefix to build login credentials.
        """
        self.data = create_full_setup('View Test Org')
        self.prefix = self.data['prefix']

    def test_login_page_loads(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects_to_dashboard(self):
        """
        Login with the prefixed employee username.
        prefix='view_test_org' → username='view_test_org_emp'
        """
        response = self.client.post('/accounts/login/', {
            'username': f'{self.prefix}_emp',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/core/dashboard/')

    def test_invalid_login_stays_on_login_page(self):
        response = self.client.post('/accounts/login/', {
            'username': f'{self.prefix}_emp',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_dashboard_redirects_to_login(self):
        response = self.client.get('/core/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_employee_cannot_access_user_list(self):
        self.client.login(
            username=f'{self.prefix}_emp',
            password='testpass123'
        )
        response = self.client.get('/accounts/users/')
        self.assertEqual(response.status_code, 302)

    def test_hr_admin_can_access_user_list(self):
        self.client.login(
            username=f'{self.prefix}_hr',
            password='testpass123'
        )
        response = self.client.get('/accounts/users/')
        self.assertEqual(response.status_code, 200)