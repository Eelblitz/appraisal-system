from django.db import models
from django.contrib.auth.models import User
from appraisal.models import Appraisal
from organisations.models import Organisation


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='payments'
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    appraisal = models.ForeignKey(
        Appraisal,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Revenue split fields
    # These are calculated and stored at payment time
    # We store them so the record is permanent even if percentage changes later
    platform_earning = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Platform cut from this payment e.g. 10% of amount'
    )
    organisation_earning = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Organisation share from this payment e.g. 90% of amount'
    )
    platform_percentage_used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='The percentage that was applied at time of payment'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    paystack_reference = models.CharField(max_length=100, unique=True)
    paystack_transaction_id = models.CharField(max_length=100, blank=True)
    paystack_response = models.JSONField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.appraisal.cycle.name} — {self.status}"

    class Meta:
        ordering = ['-created_at']


class PaymentAccessLog(models.Model):
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
        ordering = ['-downloaded_at']