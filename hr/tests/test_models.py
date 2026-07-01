from django.test import TestCase
from appraisal_project.test_utils import (
    create_full_setup, create_organisation, create_user
)
from hr.models import AppraisalCycle, AppraisalCategory, AppraisalTemplate


class AppraisalCycleTest(TestCase):

    def setUp(self):
        self.data = create_full_setup('HR Test Org')

    def test_cycle_created_correctly(self):
        cycle = self.data['cycle']
        self.assertEqual(cycle.name, '2024 Annual Appraisal')
        self.assertEqual(cycle.year, 2024)
        self.assertEqual(cycle.download_fee, 1000)
        self.assertEqual(cycle.status, 'active')

    def test_cycle_belongs_to_organisation(self):
        self.assertEqual(self.data['cycle'].organisation, self.data['org'])

    def test_template_linked_to_cycle(self):
        self.assertEqual(
            self.data['template'].cycle,
            self.data['cycle']
        )

    def test_template_has_correct_aspects(self):
        self.assertEqual(self.data['template'].aspects.count(), 3)

    def test_category_unique_per_organisation(self):
        from django.db import IntegrityError
        org = self.data['org']
        hr = self.data['hr_admin']
        with self.assertRaises(IntegrityError):
            AppraisalCategory.objects.create(
                organisation=org,
                name='Admin Staff',
                created_by=hr
            )

    def test_same_category_name_in_different_orgs(self):
        org2 = create_organisation('Another Ministry')
        hr2 = create_user('another_hr', 'hr_admin', org2)
        category2 = AppraisalCategory.objects.create(
            organisation=org2,
            name='Admin Staff',
            created_by=hr2
        )
        self.assertIsNotNone(category2.pk)


class HRViewTest(TestCase):

    def setUp(self):
        """
        Two separate organisations with unique prefixed usernames.
        Ministry A prefix: 'ministry_a'
        Ministry B prefix: 'ministry_b'
        No username collisions.
        """
        self.data = create_full_setup('Ministry A')
        self.data2 = create_full_setup('Ministry B')
        self.prefix = self.data['prefix']
        self.prefix2 = self.data2['prefix']

    def test_hr_admin_sees_only_own_cycles(self):
        self.client.login(
            username=f'{self.prefix}_hr',
            password='testpass123'
        )
        response = self.client.get('/hr/cycles/')
        self.assertEqual(response.status_code, 200)
        cycles_in_response = response.context['cycles']
        for cycle in cycles_in_response:
            self.assertEqual(cycle.organisation, self.data['org'])

    def test_hr_admin_cannot_edit_other_orgs_cycle(self):
        self.client.login(
            username=f'{self.prefix}_hr',
            password='testpass123'
        )
        org_b_cycle = self.data2['cycle']
        response = self.client.get(f'/hr/cycles/{org_b_cycle.pk}/edit/')
        self.assertEqual(response.status_code, 404)

    def test_employee_cannot_access_hr_cycles(self):
        self.client.login(
            username=f'{self.prefix}_emp',
            password='testpass123'
        )
        response = self.client.get('/hr/cycles/')
        self.assertEqual(response.status_code, 302)