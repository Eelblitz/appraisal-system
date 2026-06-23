from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import LoginForm, UserRegistrationForm, UserProfileForm
from .models import UserProfile


def login_view(request):
    """
    Handles employee login.
    GET  → show the login form
    POST → validate credentials and log in
    """
    # If user is already logged in, send them to dashboard
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')

            # If there was a 'next' URL (e.g. user tried to access a page
            # before logging in), redirect there. Otherwise go to dashboard.
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Logs the user out and redirects to login page.
    We only allow POST logout for security
    (prevents logout via a malicious link).
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Shows and updates the logged-in user's profile.
    @login_required means: if not logged in, redirect to LOGIN_URL
    """
    # get_or_create returns (object, created_boolean)
    # This safely handles users who don't have a profile yet
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    form = UserProfileForm(
        request.POST or None,
        request.FILES or None,  # request.FILES handles photo uploads
        instance=profile
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


@login_required
def create_user_view(request):
    """
    HR Admin creates new user accounts.
    Regular employees cannot access this view —
    we check the role before showing the page.
    """
    # Check that the logged-in user is HR admin or super admin
    try:
        user_profile = request.user.profile
        if user_profile.role not in ['hr_admin', 'super_admin']:
            messages.error(request, 'You do not have permission to create users.')
            return redirect('core:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    user_form = UserRegistrationForm(request.POST or None)
    profile_form = UserProfileForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user first
            new_user = user_form.save()

            # Then save the profile, linking it to the new user
            profile = profile_form.save(commit=False)
            profile.user = new_user
            profile.save()

            messages.success(
                request,
                f'Account created for {new_user.get_full_name()} successfully.'
            )
            return redirect('accounts:user_list')

    return render(request, 'accounts/create_user.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def user_list_view(request):
    """
    HR Admin sees a list of all users in the system.
    """
    try:
        user_profile = request.user.profile
        if user_profile.role not in ['hr_admin', 'super_admin']:
            messages.error(request, 'Access denied.')
            return redirect('core:dashboard')
    except UserProfile.DoesNotExist:
        return redirect('core:dashboard')

    users = UserProfile.objects.select_related('user').all().order_by(
        'user__last_name'
    )

    return render(request, 'accounts/user_list.html', {'users': users})