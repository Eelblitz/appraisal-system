from django.db import models
from django.contrib.auth.models import User
from appraisal.models import Appraisal


class Payment(models.Model):
    """
    Records every payment attempt an employee makes
    to download their completed appraisal PDF.

    Flow:
    1. Employee clicks 'Download PDF'
    2. We create a Payment record with status='pending'
    3. We redirect to Paystack
    4. Paystack calls our webhook with success/failure
    5. We update the Payment status accordingly
    6. If 'success', we unlock the PDF download
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),       # Payment initiated but not confirmed
        ('success', 'Success'),       # Paystack confirmed payment
        ('failed', 'Failed'),         # Payment failed
        ('refunded', 'Refunded'),     # Payment was refunded
    ]

    # Which employee is paying
    employee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    # Which appraisal they are paying to download
    appraisal = models.ForeignKey(
        Appraisal,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    # Amount they paid — copied from cycle.download_fee at time of payment
    # We copy it here so if HR changes the fee later, payment history is preserved
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Paystack gives us a unique reference for every transaction
    # We generate this before redirecting to Paystack
    paystack_reference = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique transaction reference sent to Paystack'
    )

    # Paystack returns this after payment — we use it to verify
    paystack_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Transaction ID returned by Paystack after payment'
    )

    # Full response from Paystack stored as text — useful for debugging
    paystack_response = models.JSONField(
        null=True,
        blank=True,
        help_text='Full JSON response from Paystack verification'
    )

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.appraisal.cycle.name} - {self.status}"

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']


class PaymentAccessLog(models.Model):
    """
    Every time an employee successfully downloads their PDF,
    we log it here. This gives HR a full audit trail.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name='access_logs'
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='download_logs'
    )
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} downloaded at {self.downloaded_at}"

    class Meta:
        verbose_name = 'Payment Access Log'
        verbose_name_plural = 'Payment Access Logs'
        ordering = ['-downloaded_at']