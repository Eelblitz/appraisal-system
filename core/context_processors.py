from appraisal.models import Appraisal


def notifications(request):
    """
    Adds notification counts to every template context.

    This runs on EVERY page load for logged-in users.
    The counts appear in the sidebar as badges.

    Why a context processor?
    Instead of passing notification counts from every
    single view, we compute them once here and they
    are automatically available in every template.
    """
    if not request.user.is_authenticated:
        return {}

    try:
        profile = request.user.profile
    except Exception:
        return {}

    notifications = {
        'nav_notification_count': 0,
        'nav_completed_appraisals': 0,
        'nav_pending_appraisals': 0,
        'nav_pending_assessment': 0,
        'nav_pending_countersign': 0,
    }

    organisation = profile.organisation if hasattr(profile, 'organisation') else None

    if not organisation and not request.user.is_superuser:
        return notifications

    try:
        if profile.role == 'employee':
            # Only count genuinely actionable items:
            # 'pending' = employee needs to fill Part 1
            # 'completed' = employee needs to pay and download
            # Once paid (status='closed'), no longer counts as pending
            pending = Appraisal.objects.filter(
                employee=request.user,
                organisation=organisation,
                status='pending'
            ).count()

            completed = Appraisal.objects.filter(
                employee=request.user,
                organisation=organisation,
                status='completed'  # ready for payment — not yet paid
            ).count()

            notifications['nav_pending_appraisals'] = pending
            notifications['nav_completed_appraisals'] = completed
            # Total badge = items needing employee action
            notifications['nav_notification_count'] = pending + completed
    except Exception:
        pass

    return notifications