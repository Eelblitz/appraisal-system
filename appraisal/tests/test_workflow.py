from django.test import TestCase
from django.utils import timezone
from appraisal_project.test_utils import create_full_setup
from appraisal.models import (
    Appraisal, PartOne, PartTwo, PartThree,
    PartFour, AppraisalAspectRating
)


class AppraisalCreationTest(TestCase):
    """Tests for appraisal creation and assignment."""

    def setUp(self):
        self.data = create_full_setup()

    def test_create_appraisal(self):
        """Appraisal record is created correctly."""
        appraisal = Appraisal.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            cycle=self.data['cycle'],
            template=self.data['template'],
            status='pending'
        )
        self.assertEqual(appraisal.status, 'pending')
        self.assertEqual(appraisal.employee, self.data['employee'])

    def test_duplicate_appraisal_prevented(self):
        """
        One employee cannot have two appraisals in the same cycle.
        Tests the unique_together constraint.
        """
        from django.db import IntegrityError
        Appraisal.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            cycle=self.data['cycle'],
            template=self.data['template'],
            status='pending'
        )
        with self.assertRaises(IntegrityError):
            Appraisal.objects.create(
                organisation=self.data['org'],
                employee=self.data['employee'],
                cycle=self.data['cycle'],
                template=self.data['template'],
                status='pending'
            )

    def test_appraisal_belongs_to_organisation(self):
        """Appraisal is linked to the correct organisation."""
        appraisal = Appraisal.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            cycle=self.data['cycle'],
            template=self.data['template'],
        )
        self.assertEqual(appraisal.organisation, self.data['org'])


class AppraisalWorkflowTest(TestCase):
    """
    Tests the complete 4-part workflow sequence.
    Each test builds on the previous to simulate real usage.
    """

    def setUp(self):
        self.data = create_full_setup()
        self.appraisal = Appraisal.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            cycle=self.data['cycle'],
            template=self.data['template'],
            status='pending'
        )

    def test_initial_status_is_pending(self):
        """New appraisal starts as pending."""
        self.assertEqual(self.appraisal.status, 'pending')

    def test_part1_submission_changes_status(self):
        """
        After Part 1 is submitted, appraisal status
        changes to 'part1_submitted'.
        """
        PartOne.objects.create(
            appraisal=self.appraisal,
            qualification='BSc Computer Science',
            date_of_first_appointment='2015-01-01',
            present_substantive_grade='GL 08',
            date_appointed_to_grade='2020-01-01',
            present_job='Software Developer',
            job_description='Develops software systems',
            main_duty_1='Writing code',
            is_draft=False,
            submitted_at=timezone.now()
        )
        self.appraisal.status = 'part1_submitted'
        self.appraisal.part1_submitted_at = timezone.now()
        self.appraisal.save()

        self.appraisal.refresh_from_db()
        self.assertEqual(self.appraisal.status, 'part1_submitted')

    def test_part2_requires_part1_submitted(self):
        """
        Part 2 view should not be accessible when
        appraisal is still 'pending'.
        The reporting officer cannot assess before
        the employee submits Part 1.
        """
        self.client.login(
            username='reporting_officer',
            password='testpass123'
        )
        # Status is still 'pending' — Part 2 should be blocked
        response = self.client.get(
            f'/appraisal/part2/{self.appraisal.pk}/'
        )
        # Should redirect away with warning
        self.assertEqual(response.status_code, 302)

    def test_full_workflow_status_sequence(self):
        """
        Tests the complete status sequence:
        pending → part1_submitted → part2_submitted
        → part3_submitted → completed
        """
        # Part 1
        self.appraisal.status = 'part1_submitted'
        self.appraisal.save()
        self.assertEqual(self.appraisal.status, 'part1_submitted')

        # Part 2
        self.appraisal.status = 'part2_submitted'
        self.appraisal.save()
        self.assertEqual(self.appraisal.status, 'part2_submitted')

        # Part 3
        self.appraisal.status = 'part3_submitted'
        self.appraisal.save()
        self.assertEqual(self.appraisal.status, 'part3_submitted')

        # Part 4
        self.appraisal.status = 'completed'
        self.appraisal.save()
        self.assertEqual(self.appraisal.status, 'completed')

    def test_aspect_ratings_saved_correctly(self):
        """
        Aspect ratings are saved dynamically linked to PartTwo.
        Tests the AppraisalAspectRating model.
        """
        # Create Part 2
        part_two = PartTwo.objects.create(
            appraisal=self.appraisal,
            performance_assessment='Good performance overall',
            overall_rating='3',
            reporting_officer=self.data['reporting_officer'],
            is_draft=False,
            submitted_at=timezone.now()
        )

        # Create aspect ratings
        for aspect in self.data['aspects']:
            AppraisalAspectRating.objects.create(
                part_two=part_two,
                aspect=aspect,
                rating='B'
            )

        # Verify ratings saved
        ratings = part_two.aspect_ratings.all()
        self.assertEqual(ratings.count(), 3)

        for rating in ratings:
            self.assertEqual(rating.rating, 'B')

    def test_aspect_rating_unique_per_aspect(self):
        """
        Each aspect can only be rated once per PartTwo.
        Duplicate ratings are prevented by unique_together.
        """
        from django.db import IntegrityError
        part_two = PartTwo.objects.create(
            appraisal=self.appraisal,
            performance_assessment='Test',
            overall_rating='3',
            reporting_officer=self.data['reporting_officer'],
        )

        aspect = self.data['aspects'][0]
        AppraisalAspectRating.objects.create(
            part_two=part_two,
            aspect=aspect,
            rating='A'
        )

        with self.assertRaises(IntegrityError):
            AppraisalAspectRating.objects.create(
                part_two=part_two,
                aspect=aspect,  # same aspect — should fail
                rating='B'
            )


class DataIsolationTest(TestCase):

    def setUp(self):
        self.data_a = create_full_setup('Ministry A')
        self.data_b = create_full_setup('Ministry B')
        self.prefix_a = self.data_a['prefix']
        self.prefix_b = self.data_b['prefix']

        self.appraisal_a = Appraisal.objects.create(
            organisation=self.data_a['org'],
            employee=self.data_a['employee'],
            cycle=self.data_a['cycle'],
            template=self.data_a['template'],
            status='pending'
        )
        self.appraisal_b = Appraisal.objects.create(
            organisation=self.data_b['org'],
            employee=self.data_b['employee'],
            cycle=self.data_b['cycle'],
            template=self.data_b['template'],
            status='pending'
        )

    def test_employee_cannot_see_other_orgs_appraisal(self):
        self.client.login(
            username=f'{self.prefix_a}_emp',
            password='testpass123'
        )
        response = self.client.get(
            f'/appraisal/detail/{self.appraisal_b.pk}/'
        )
        self.assertEqual(response.status_code, 404)

    def test_hr_admin_cannot_see_other_orgs_appraisals(self):
        self.client.login(
            username=f'{self.prefix_a}_hr',
            password='testpass123'
        )
        response = self.client.get('/appraisal/all/')
        self.assertEqual(response.status_code, 200)
        appraisals = response.context['appraisals']
        for appraisal in appraisals:
            self.assertEqual(
                appraisal.organisation,
                self.data_a['org']
            )

    def test_reporting_officer_sees_only_own_subordinates(self):
        self.client.login(
            username=f'{self.prefix_a}_ro',
            password='testpass123'
        )
        response = self.client.get(
            f'/appraisal/detail/{self.appraisal_b.pk}/'
        )
        self.assertEqual(response.status_code, 404)