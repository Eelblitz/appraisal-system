from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import UserProfile
from appraisal.models import Appraisal
from hr.models import AppraisalCycle
from organisations.models import Organisation
from payments.models import Payment


@login_required
def dashboard_view(request):
    """
    Single dashboard view that serves different content
    based on the logged-in user's role.

    Each role sees ONLY what is relevant to them:

    Platform Super Admin → platform-wide stats, all organisations
    HR Admin → their organisation's stats and quick actions
    Reporting Officer → appraisals awaiting their assessment
    Countersigning Officer → appraisals awaiting countersigning
    Employee → their own appraisals only
    """
    # Safety check — if user has no profile, create one
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    context = {'profile': profile}

    # ── PLATFORM SUPER ADMIN ────────────────────────────
    # Django superuser — sees the entire platform
    if request.user.is_superuser:
        organisations = Organisation.objects.all().order_by('name')
        total_organisations = organisations.count()
        active_organisations = organisations.filter(is_active=True).count()
        total_users = User.objects.count()
        total_appraisals = Appraisal.objects.count()

        # Platform revenue — sum of all platform_earning payments
        from django.db.models import Sum
        platform_revenue = Payment.objects.filter(
            status='success'
        ).aggregate(
            total=Sum('platform_earning')
        )['total'] or 0

        context.update({
            'organisations': organisations[:5],  # show latest 5
            'total_organisations': total_organisations,
            'active_organisations': active_organisations,
            'total_users': total_users,
            'total_appraisals': total_appraisals,
            'platform_revenue': platform_revenue,
        })
        return render(request, 'core/dashboard_platform.html', context)

    # ── ORGANISATION HR ADMIN ───────────────────────────
    # Sees their organisation's data only
    elif profile.role in ['hr_admin', 'super_admin']:
        organisation = profile.organisation

        if not organisation:
            return render(
                request,
                'core/dashboard_no_org.html',
                context
            )

        # All stats scoped to THIS organisation
        total_staff = UserProfile.objects.filter(
            organisation=organisation
        ).count()

        total_appraisals = Appraisal.objects.filter(
            organisation=organisation
        ).count()

        pending_appraisals = Appraisal.objects.filter(
            organisation=organisation,
            status='pending'
        ).count()

        completed_appraisals = Appraisal.objects.filter(
            organisation=organisation,
            status='closed'
        ).count()

        in_progress = Appraisal.objects.filter(
            organisation=organisation
        ).exclude(
            status__in=['pending', 'closed']
        ).count()

        active_cycles = AppraisalCycle.objects.filter(
            organisation=organisation,
            status='active'
        )

        # Recent appraisals for the activity feed
        recent_appraisals = Appraisal.objects.filter(
            organisation=organisation
        ).select_related(
            'employee', 'cycle'
        ).order_by('-created_at')[:5]

        context.update({
            'organisation': organisation,
            'total_staff': total_staff,
            'total_appraisals': total_appraisals,
            'pending_appraisals': pending_appraisals,
            'completed_appraisals': completed_appraisals,
            'in_progress': in_progress,
            'active_cycles': active_cycles,
            'recent_appraisals': recent_appraisals,
        })
        return render(request, 'core/dashboard_hr.html', context)

    # ── REPORTING OFFICER ───────────────────────────────
    elif profile.role == 'reporting_officer':
        organisation = profile.organisation

        # Appraisals where Part 1 is done and officer must assess
        pending_assessment = Appraisal.objects.filter(
            organisation=organisation,
            employee__profile__reporting_officer=profile,
            status='part1_submitted'
        ).select_related('employee', 'cycle')

        # Already assessed
        completed_assessment = Appraisal.objects.filter(
            organisation=organisation,
            employee__profile__reporting_officer=profile,
            status__in=['part2_submitted', 'part3_submitted',
                        'completed', 'closed']
        ).count()

        context.update({
            'organisation': organisation,
            'pending_assessment': pending_assessment,
            'pending_count': pending_assessment.count(),
            'completed_assessment': completed_assessment,
        })
        return render(
            request,
            'core/dashboard_reporting_officer.html',
            context
        )

    # ── COUNTERSIGNING OFFICER ──────────────────────────
    elif profile.role == 'countersigning_officer':
        organisation = profile.organisation

        pending_countersign = Appraisal.objects.filter(
            organisation=organisation,
            employee__profile__countersigning_officer=profile,
            status='part3_submitted'
        ).select_related('employee', 'cycle')

        completed_countersign = Appraisal.objects.filter(
            organisation=organisation,
            employee__profile__countersigning_officer=profile,
            status__in=['completed', 'closed']
        ).count()

        context.update({
            'organisation': organisation,
            'pending_countersign': pending_countersign,
            'pending_count': pending_countersign.count(),
            'completed_countersign': completed_countersign,
        })
        return render(
            request,
            'core/dashboard_countersigning.html',
            context
        )

    # ── EMPLOYEE ────────────────────────────────────────
    else:
        organisation = profile.organisation

        my_appraisals = Appraisal.objects.filter(
            employee=request.user,
            organisation=organisation
        ).select_related('cycle').order_by('-created_at')

        # Current active appraisal — the one they need to act on
        active_appraisal = my_appraisals.filter(
            status='pending'
        ).first()

        context.update({
            'organisation': organisation,
            'my_appraisals': my_appraisals,
            'active_appraisal': active_appraisal,
            'total_appraisals': my_appraisals.count(),
            'completed_appraisals': my_appraisals.filter(
                status='closed'
            ).count(),
        })
        return render(
            request,
            'core/dashboard_employee.html',
            context
        )