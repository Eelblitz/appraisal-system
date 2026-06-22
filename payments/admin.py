from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Payment, PaymentAccessLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'appraisal', 'amount',
        'status', 'paystack_reference', 'paid_at'
    ]
    list_filter = ['status']
    search_fields = [
        'employee__first_name',
        'employee__last_name',
        'paystack_reference'
    ]
    readonly_fields = [
        'paystack_reference', 'paystack_transaction_id',
        'paystack_response', 'paid_at', 'created_at'
    ]


@admin.register(PaymentAccessLog)
class PaymentAccessLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payment', 'downloaded_at', 'ip_address']
    readonly_fields = ['downloaded_at', 'ip_address']