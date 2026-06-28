from io import BytesIO
from .pdf_generator import generate_appraisal_pdf
import uuid
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from .models import Payment, PaymentAccessLog
from appraisal.models import Appraisal
from accounts.models import UserProfile


def get_user_organisation(request):
    try:
        return request.user.profile.organisation
    except UserProfile.DoesNotExist:
        return None


def appraisal_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func
    return wrapper


def hr_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        try:
            role = request.user.profile.role
            if role not in ['hr_admin', 'super_admin']:
                messages.error(request, 'Access denied.')
                return redirect('core:dashboard')
        except UserProfile.DoesNotExist:
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func
    return wrapper


# ═══════════════════════════════════════════════════════
# INITIATE PAYMENT
# ═══════════════════════════════════════════════════════

@appraisal_login_required
@appraisal_login_required
def initiate_payment(request, pk):
    organisation = get_user_organisation(request)

    appraisal = get_object_or_404(
        Appraisal,
        pk=pk,
        employee=request.user,
        organisation=organisation
    )

    if appraisal.status not in ['completed', 'closed']:
        messages.warning(request, 'This appraisal is not yet complete.')
        return redirect('core:dashboard')

    # Already paid — go straight to download
    existing_payment = Payment.objects.filter(
        appraisal=appraisal,
        employee=request.user,
        status='success'
    ).first()

    if existing_payment:
        return redirect('payments:download_pdf', pk=appraisal.pk)

    # Handle free download
    download_fee = appraisal.cycle.download_fee
    if download_fee == 0:
        Payment.objects.create(
            organisation=organisation,
            employee=request.user,
            appraisal=appraisal,
            amount=0,
            platform_earning=0,
            organisation_earning=0,
            platform_percentage_used=organisation.subscription_percentage,
            status='success',
            paystack_reference=f'FREE-{appraisal.pk}-{uuid.uuid4().hex[:8]}',
            paid_at=timezone.now()
        )
        appraisal.status = 'closed'
        appraisal.save()
        return redirect('payments:download_pdf', pk=appraisal.pk)

    # Check employee has email
    if not request.user.email:
        messages.error(
            request,
            'Your account has no email address. '
            'Contact HR to update your email.'
        )
        return redirect('core:dashboard')

    reference = f'APPR-{appraisal.pk}-{uuid.uuid4().hex[:8].upper()}'

    callback_url = request.build_absolute_uri(
        f'/payments/callback/?reference={reference}'
    )

    paystack_data = {
        'email': request.user.email,
        'amount': int(download_fee * 100),
        'reference': reference,
        'callback_url': callback_url,
        'metadata': {
            'appraisal_id': appraisal.pk,
            'employee_name': request.user.get_full_name(),
            'cycle_name': appraisal.cycle.name,
        }
    }

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(
            f'{settings.PAYSTACK_BASE_URL}/transaction/initialize',
            json=paystack_data,
            headers=headers,
            timeout=30
        )
        response_data = response.json()

        if response_data.get('status'):
            # Save payment record only after confirmed by Paystack
            Payment.objects.create(
                organisation=organisation,
                employee=request.user,
                appraisal=appraisal,
                amount=download_fee,
                platform_percentage_used=organisation.subscription_percentage,
                status='pending',
                paystack_reference=reference,
            )
            # Redirect to Paystack payment page
            return redirect(response_data['data']['authorization_url'])
        else:
            messages.error(
                request,
                f"Payment error: {response_data.get('message', 'Unknown error')}"
            )
            return redirect('core:dashboard')

    except Exception as e:
        messages.error(request, f'Payment failed: {str(e)}')
        return redirect('core:dashboard')

# ═══════════════════════════════════════════════════════
# PAYMENT CALLBACK
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def payment_callback(request):
    """
    Paystack redirects the employee here after payment.

    CRITICAL: We do NOT trust the redirect alone.
    We always verify with Paystack API before unlocking PDF.

    Why? Someone could manually visit this URL with a fake
    reference and get free PDFs without paying.
    The verification call to Paystack confirms real payment.
    """
    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('core:dashboard')

    # Find our payment record using the reference
    payment = get_object_or_404(
        Payment,
        paystack_reference=reference,
        employee=request.user
    )

    # If already verified (user hit back button), go to download
    if payment.status == 'success':
        return redirect(
            'payments:download_pdf',
            pk=payment.appraisal.pk
        )

    # Verify payment with Paystack API
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }

    try:
        response = requests.get(
            f'{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}',
            headers=headers,
            timeout=30
        )
        response_data = response.json()

        # Store full Paystack response for audit purposes
        payment.paystack_response = response_data

        if (response_data.get('status') and
                response_data['data']['status'] == 'success'):

            # Payment confirmed by Paystack
            organisation = payment.organisation

            # Calculate the revenue split
            platform_earning = organisation.calculate_platform_earning(
                payment.amount
            )
            organisation_earning = organisation.calculate_organisation_earning(
                payment.amount
            )

            # Update payment record with full details
            payment.status = 'success'
            payment.platform_earning = platform_earning
            payment.organisation_earning = organisation_earning
            payment.paystack_transaction_id = str(
                response_data['data']['id']
            )
            payment.paid_at = timezone.now()
            payment.save()

            # Close the appraisal — PDF now available
            appraisal = payment.appraisal
            appraisal.status = 'closed'
            appraisal.save()

            messages.success(
                request,
                f'Payment of ₦{payment.amount} confirmed. '
                f'Your PDF is ready to download.'
            )
            return redirect(
                'payments:download_pdf',
                pk=appraisal.pk
            )

        else:
            # Payment failed or was cancelled
            payment.status = 'failed'
            payment.save()
            messages.error(
                request,
                'Payment was not successful. Please try again.'
            )
            return redirect('core:dashboard')

    except requests.exceptions.RequestException:
        messages.error(
            request,
            'Could not verify payment. Please contact support '
            'with your reference: ' + reference
        )
        return redirect('core:dashboard')


# ═══════════════════════════════════════════════════════
# MY PAYMENTS VIEW
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def my_payments(request):
    """
    Employee sees their own payment history.
    Shows all payment attempts and their status.
    """
    organisation = get_user_organisation(request)

    payments = Payment.objects.filter(
        employee=request.user,
        organisation=organisation
    ).select_related('appraisal__cycle').order_by('-created_at')

    return render(request, 'payments/my_payments.html', {
        'payments': payments,
    })


# ═══════════════════════════════════════════════════════
# ALL PAYMENTS VIEW (HR Admin)
# ═══════════════════════════════════════════════════════

@hr_required
def all_payments(request):
    """
    HR Admin sees all payments in their organisation.
    Shows revenue split between platform and organisation.
    """
    from django.db.models import Sum
    organisation = get_user_organisation(request)

    payments = Payment.objects.filter(
        organisation=organisation
    ).select_related(
        'employee', 'appraisal__cycle'
    ).order_by('-created_at')

    # Revenue summary
    successful = payments.filter(status='success')
    total_collected = successful.aggregate(
        total=Sum('amount')
    )['total'] or 0
    platform_total = successful.aggregate(
        total=Sum('platform_earning')
    )['total'] or 0
    org_total = successful.aggregate(
        total=Sum('organisation_earning')
    )['total'] or 0

    return render(request, 'payments/all_payments.html', {
        'payments': payments,
        'total_collected': total_collected,
        'platform_total': platform_total,
        'org_total': org_total,
    })
    
# ═══════════════════════════════════════════════════════
# DOWNLOAD PDF VIEW
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def download_pdf(request, pk):
    """
    Generates and serves the appraisal PDF.

    Security checks:
    1. User must be logged in
    2. Appraisal must belong to this employee
    3. A successful payment must exist

    Why generate on the fly?
    We never store the PDF on disk.
    Every download generates a fresh PDF from
    the current database data.
    This saves disk space and ensures the PDF
    always reflects the actual data.

    HttpResponse with content_type='application/pdf'
    tells the browser this is a PDF file.
    Content-Disposition attachment means the browser
    downloads it rather than trying to display it inline.
    """
    organisation = get_user_organisation(request)

    appraisal = get_object_or_404(
        Appraisal,
        pk=pk,
        employee=request.user,
        organisation=organisation
    )

    # Verify payment exists and was successful
    payment = Payment.objects.filter(
        appraisal=appraisal,
        employee=request.user,
        status='success'
    ).first()

    if not payment:
        messages.error(
            request,
            'Please complete payment before downloading.'
        )
        return redirect('payments:initiate', pk=appraisal.pk)

    # Log this download for audit trail
    PaymentAccessLog.objects.create(
        payment=payment,
        employee=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    # Generate PDF in memory
    buffer = BytesIO()
    generate_appraisal_pdf(appraisal, buffer)
    buffer.seek(0)

    # Build a clean filename
    # e.g. "Performance_Evaluation_Musa_Abdullahi_2024.pdf"
    employee_name = request.user.get_full_name().replace(' ', '_')
    year = appraisal.cycle.year
    filename = f'Performance_Evaluation_{employee_name}_{year}.pdf'

    # Serve the PDF as a download
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )
    return response