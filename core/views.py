from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from appraisal.models import Appraisal


@login_required
def dashboard_view(request):
    """
    The dashboard is the first page every user sees after login.
    What they see depends on their role.

    We pass different context data based on who is logged in:
    - Employee     → their own appraisals
    - Reporting Officer → appraisals awaiting their input
    - HR Admin     → system-wide statistics
    """

    # Safely get the user's profile
    # If somehow they have no profile, create one with default role
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'profile': profile,
    }

    # ── Employee Dashboard ──────────────────────────────
    if profile.role == 'employee':
        # Get all appraisals belonging to this employee
        my_appraisals = Appraisal.objects.filter(
            employee=request.user
        ).select_related('cycle', 'template').order_by('-created_at')

        context['my_appraisals'] = my_appraisals
        context['pending_count'] = my_appraisals.filter(status='pending').count()
        context['completed_count'] = my_appraisals.filter(status='closed').count()

    # ── Reporting Officer Dashboard ─────────────────────
    elif profile.role == 'reporting_officer':
        # Get appraisals where the employee reports to this officer
        # and the employee has submitted Part 1 (so Part 2 is now due)
        pending_review = Appraisal.objects.filter(
            employee__profile__reporting_officer=profile,
            status='part1_submitted'
        ).select_related('employee', 'cycle')

        context['pending_review'] = pending_review
        context['pending_count'] = pending_review.count()

    # ── Countersigning Officer Dashboard ────────────────
    elif profile.role == 'countersigning_officer':
        # Appraisals where Part 3 is done and awaiting countersigning
        pending_countersign = Appraisal.objects.filter(
            employee__profile__countersigning_officer=profile,
            status='part3_submitted'
        ).select_related('employee', 'cycle')

        context['pending_countersign'] = pending_countersign
        context['pending_count'] = pending_countersign.count()

    # ── HR Admin / Super Admin Dashboard ────────────────
    elif profile.role in ['hr_admin', 'super_admin']:
        # HR sees system-wide statistics
        context['total_appraisals'] = Appraisal.objects.count()
        context['pending_appraisals'] = Appraisal.objects.filter(
            status='pending'
        ).count()
        context['completed_appraisals'] = Appraisal.objects.filter(
            status='closed'
        ).count()
        context['total_users'] = UserProfile.objects.count()

    return render(request, 'core/dashboard.html', context)