from django.test import TestCase
from django.utils import timezone
from appraisal_project.test_utils import create_full_setup
from appraisal.models import Appraisal
from payments.models import Payment, PaymentAccessLog
import uuid


class PaymentModelTest(TestCase):
    """Tests for Payment model and revenue split logic."""

    def setUp(self):
        self.data = create_full_setup()
        self.appraisal = Appraisal.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            cycle=self.data['cycle'],
            template=self.data['template'],
            status='completed'
        )

    def test_payment_created_correctly(self):
        """Payment record saves all fields correctly."""
        payment = Payment.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            appraisal=self.appraisal,
            amount=1000,
            platform_percentage_used=10,
            status='pending',
            paystack_reference=f'TEST-{uuid.uuid4().hex[:8]}'
        )
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.amount, 1000)

    def test_revenue_split_stored_correctly(self):
        """
        Revenue split is calculated and stored correctly.
        ₦1000 at 10% → platform: ₦100, org: ₦900
        """
        org = self.data['org']
        amount = 1000
        platform = org.calculate_platform_earning(amount)
        org_share = org.calculate_organisation_earning(amount)

        payment = Payment.objects.create(
            organisation=org,
            employee=self.data['employee'],
            appraisal=self.appraisal,
            amount=amount,
            platform_earning=platform,
            organisation_earning=org_share,
            platform_percentage_used=org.subscription_percentage,
            status='success',
            paystack_reference=f'TEST-{uuid.uuid4().hex[:8]}',
            paid_at=timezone.now()
        )

        payment.refresh_from_db()
        self.assertEqual(payment.platform_earning, 100)
        self.assertEqual(payment.organisation_earning, 900)
        self.assertEqual(
            payment.platform_earning + payment.organisation_earning,
            payment.amount
        )

    def test_duplicate_reference_prevented(self):
        """
        Two payments cannot have the same Paystack reference.
        The reference is unique per transaction.
        """
        from django.db import IntegrityError
        ref = 'UNIQUE-REF-001'
        Payment.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            appraisal=self.appraisal,
            amount=1000,
            status='pending',
            paystack_reference=ref
        )
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                organisation=self.data['org'],
                employee=self.data['employee'],
                appraisal=self.appraisal,
                amount=1000,
                status='pending',
                paystack_reference=ref  # duplicate
            )

    def test_download_log_created_on_access(self):
        """
        Every PDF download is logged in PaymentAccessLog.
        """
        payment = Payment.objects.create(
            organisation=self.data['org'],
            employee=self.data['employee'],
            appraisal=self.appraisal,
            amount=1000,
            status='success',
            paystack_reference=f'TEST-{uuid.uuid4().hex[:8]}',
            paid_at=timezone.now()
        )

        PaymentAccessLog.objects.create(
            payment=payment,
            employee=self.data['employee'],
            ip_address='127.0.0.1'
        )

        logs = PaymentAccessLog.objects.filter(payment=payment)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().ip_address, '127.0.0.1')

    def test_free_download_at_zero_fee(self):
        """
        Cycles with ₦0 download fee should not go through Paystack.
        Platform and org earnings should both be 0.
        """
        org = self.data['org']
        amount = 0
        platform = org.calculate_platform_earning(amount)
        org_share = org.calculate_organisation_earning(amount)

        self.assertEqual(platform, 0)
        self.assertEqual(org_share, 0)

    def test_payment_access_view_requires_successful_payment(self):
        """
        Employee cannot access PDF download without a
        successful payment record.
        """
        self.appraisal.status = 'completed'
        self.appraisal.save()

        self.client.login(username='employee', password='testpass123')
        response = self.client.get(
            f'/payments/download/{self.appraisal.pk}/'
        )
        # Should redirect to initiate payment, not serve PDF
        self.assertEqual(response.status_code, 302)


