from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import LoginForm, UserRegistrationForm, UserProfileForm
from .models import UserProfile


# ─────────────────────────────────────────────────────
# HELPER: Get current user's organisation
# ─────────────────────────────────────────────────────

def get_user_organisation(request):
    """
    Returns the organisation of the currently logged-in user.
    Called at the start of every protected view.
    Centralising this means we only change it in one place
    if the logic ever needs to evolve.
    """
    try:
        return request.user.profile.organisation
    except UserProfile.DoesNotExist:
        return None


# ─────────────────────────────────────────────────────
# HELPER: HR role check decorator
# ─────────────────────────────────────────────────────

def hr_required(view_func):
    """
    Protects views that only HR Admin or Super Admin can access.
    Used for user management pages.
    """
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
# AUTHENTICATION VIEWS
# ═══════════════════════════════════════════════════════

def login_view(request):
    """
    Handles login for all user types.

    Extra check we add for SaaS:
    After credentials are verified, we check if the user's
    organisation is still active.

    Why? If a ministry's subscription lapses, you deactivate
    their organisation. Their users should not be able to log in
    even if their personal account is still active.

    Platform superusers bypass this check — they have no
    organisation and must always be able to log in.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            # Organisation active check for non-superusers
            if not user.is_superuser:
                try:
                    profile = user.profile
                    if profile.organisation and not profile.organisation.is_active:
                        messages.error(
                            request,
                            'Your organisation account is inactive. '
                            'Contact the platform administrator.'
                        )
                        return redirect('accounts:login')
                except UserProfile.DoesNotExist:
                    pass

            login(request, user)
            messages.success(
                request,
                f'Welcome back, {user.get_full_name() or user.username}!'
            )
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


# ═══════════════════════════════════════════════════════
# PROFILE VIEW
# ═══════════════════════════════════════════════════════

@login_required
def profile_view(request):
    """
    Every user can view and update their own profile.
    The form filters reporting/countersigning officer dropdowns
    to only show users from the same organisation.
    """
    organisation = get_user_organisation(request)
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'organisation': organisation}
    )

    form = UserProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=profile,
        organisation=organisation
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile
    })


# ═══════════════════════════════════════════════════════
# USER MANAGEMENT VIEWS (HR Admin only)
# ═══════════════════════════════════════════════════════

@hr_required
def user_list_view(request):
    """
    HR Admin sees ALL users in their organisation only.

    select_related('user') fetches the linked Django User
    in the same database query — avoids N+1 query problem.

    What is N+1?
    Without select_related, Django makes one query to get
    all profiles, then ONE MORE query per profile to get
    the linked user. 100 profiles = 101 queries.
    With select_related, it is always just 1 query.
    """
    organisation = get_user_organisation(request)

    users = UserProfile.objects.filter(
        organisation=organisation
    ).select_related('user').order_by('user__last_name', 'user__first_name')

    # Count by role for the summary cards
    total = users.count()
    employees = users.filter(role='employee').count()
    reporting_officers = users.filter(role='reporting_officer').count()
    countersigning_officers = users.filter(role='countersigning_officer').count()
    hr_admins = users.filter(role='hr_admin').count()

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'total': total,
        'employees': employees,
        'reporting_officers': reporting_officers,
        'countersigning_officers': countersigning_officers,
        'hr_admins': hr_admins,
    })


@hr_required
def create_user_view(request):
    """
    HR Admin creates a new user account within their organisation.

    Two forms are used together:
    1. UserRegistrationForm — creates the Django User
       (username, password, name, email)
    2. UserProfileForm — creates the UserProfile
       (role, department, reporting officer, etc.)

    Both must be valid before either is saved.
    This prevents partial saves — either both save or neither does.

    The organisation is set automatically from the HR Admin's
    profile — the HR Admin cannot choose which organisation
    the new user belongs to.
    """
    organisation = get_user_organisation(request)

    user_form = UserRegistrationForm(request.POST or None)
    profile_form = UserProfileForm(
        request.POST or None,
        request.FILES or None,
        organisation=organisation  # filters dropdowns to this org
    )

    if request.method == 'POST':
        # Both forms must be valid before we save either
        if user_form.is_valid() and profile_form.is_valid():

            # Step 1: Save the Django User record
            new_user = user_form.save()

            # Step 2: Save the UserProfile
            # commit=False gives us the object without saving to DB yet
            # so we can attach the organisation and user first
            profile = profile_form.save(commit=False)
            profile.user = new_user
            profile.organisation = organisation  # ← critical SaaS line
            profile.save()

            messages.success(
                request,
                f'Account created for {new_user.get_full_name()} successfully.'
            )
            return redirect('accounts:user_list')
        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )

    return render(request, 'accounts/create_user.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@hr_required
def edit_user_view(request, pk):
    """
    HR Admin edits an existing user's profile.

    Security check:
    get_object_or_404 with organisation= filter ensures
    HR Admin can only edit users in THEIR organisation.

    If someone manually types /accounts/users/99/edit/
    and user 99 belongs to a different organisation,
    Django returns 404 — not found. Correct behaviour.
    """
    organisation = get_user_organisation(request)

    # Get profile — must belong to this organisation
    profile = get_object_or_404(
        UserProfile,
        user__id=pk,
        organisation=organisation
    )

    user_form = UserRegistrationForm(
        request.POST or None,
        instance=profile.user
    )
    profile_form = UserProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=profile,
        organisation=organisation
    )

    if request.method == 'POST':
        # For editing, we don't require password fields
        # so we validate profile_form independently
        if profile_form.is_valid():
            profile_form.save()

            # Only update name and email from user_form
            # not password (handled separately if needed)
            user = profile.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

            messages.success(
                request,
                f'{profile.user.get_full_name()} updated successfully.'
            )
            return redirect('accounts:user_list')

    return render(request, 'accounts/edit_user.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })


@hr_required
def user_detail_view(request, pk):
    """
    HR Admin views a single user's full details.
    Read-only — no editing here.
    """
    organisation = get_user_organisation(request)

    profile = get_object_or_404(
        UserProfile,
        user__id=pk,
        organisation=organisation
    )

    # Get this user's appraisals
    from appraisal.models import Appraisal
    appraisals = Appraisal.objects.filter(
        employee=profile.user,
        organisation=organisation
    ).select_related('cycle').order_by('-created_at')

    return render(request, 'accounts/user_detail.html', {
        'profile': profile,
        'appraisals': appraisals,
    })