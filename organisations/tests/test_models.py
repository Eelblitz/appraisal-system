from django.test import TestCase
from organisations.models import Organisation


class OrganisationModelTest(TestCase):
    """Tests for the Organisation (tenant) model."""

    def setUp(self):
        """Create a test organisation before each test."""
        self.org = Organisation.objects.create(
            name='Federal Ministry of Finance',
            acronym='FMF',
            email='info@fmf.gov.ng',
            subscription_percentage=10,
            is_active=True
        )

    def test_organisation_created_correctly(self):
        """Organisation saves all fields correctly."""
        self.assertEqual(self.org.name, 'Federal Ministry of Finance')
        self.assertEqual(self.org.acronym, 'FMF')
        self.assertEqual(self.org.subscription_percentage, 10)
        self.assertTrue(self.org.is_active)

    def test_slug_auto_generated(self):
        """
        Slug is auto-generated from name when not provided.
        'Federal Ministry of Finance' → 'federal-ministry-of-finance'
        """
        self.assertEqual(self.org.slug, 'federal-ministry-of-finance')

    def test_slug_not_overwritten_on_update(self):
        """
        Slug should not change when organisation name is updated.
        This preserves existing URLs.
        """
        original_slug = self.org.slug
        self.org.name = 'Federal Ministry of Finance (Updated)'
        self.org.save()
        self.assertEqual(self.org.slug, original_slug)

    def test_platform_earning_calculation(self):
        """
        10% of ₦2000 = ₦200
        Tests the calculate_platform_earning method.
        """
        earning = self.org.calculate_platform_earning(2000)
        self.assertEqual(earning, 200.00)

    def test_organisation_earning_calculation(self):
        """
        90% of ₦2000 = ₦1800
        Tests the calculate_organisation_earning method.
        """
        earning = self.org.calculate_organisation_earning(2000)
        self.assertEqual(earning, 1800.00)

    def test_platform_earning_different_percentage(self):
        """Test revenue split with a different percentage (15%)."""
        self.org.subscription_percentage = 15
        earning = self.org.calculate_platform_earning(1000)
        self.assertEqual(earning, 150.00)

    def test_earnings_add_up_to_total(self):
        """Platform earning + organisation earning must always equal total."""
        amount = 3500
        platform = self.org.calculate_platform_earning(amount)
        org_share = self.org.calculate_organisation_earning(amount)
        self.assertEqual(platform + org_share, amount)

    def test_string_representation(self):
        """__str__ returns the organisation name."""
        self.assertEqual(str(self.org), 'Federal Ministry of Finance')

    def test_unique_name_constraint(self):
        """Two organisations cannot have the same name."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Organisation.objects.create(
                name='Federal Ministry of Finance',
                subscription_percentage=10
            )


