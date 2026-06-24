from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Organisation
from .forms import OrganisationForm, OrganisationSettingsForm, OrgAdminCreationForm
from accounts.models import UserProfile


# ─────────────────────────────────────────────────────
# HELPER: Platform superuser check
# ─────────────────────────────────────────────────────

def platform_admin_required(view_func):
    """
    Custom decorator that checks two things:
    1. User is logged in
    2. User is a Django superuser (is_superuser=True)

    Why Django superuser and not our custom role?
    Platform admin is at a different level from organisation roles.
    Django's built-in is_superuser flag is the right tool here.
    Our custom roles (hr_admin, super_admin) are organisation-level.
    Platform admin transcends all organisations.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if not request.user.is_superuser:
            messages.error(
                request,
                'You do not have permission to access the platform admin area.'
            )
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)

    wrapper.__wrapped__ = view_func
    return wrapper


def org_super_admin_required(view_func):
    """
    Checks the user has super_admin role within their organisation.
    Used for organisation-level admin pages.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        try:
            role = request.user.profile.role
            if role not in ['super_admin', 'hr_admin']:
                messages.error(request, 'Access denied.')
                return redirect('core:dashboard')
        except UserProfile.DoesNotExist:
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)

    wrapper.__wrapped__ = view_func
    return wrapper


# ═══════════════════════════════════════════════════════
# PLATFORM LEVEL VIEWS
# Only Django superusers (you) can access these
# ═══════════════════════════════════════════════════════

@platform_admin_required
def organisation_list(request):
    """
    Platform admin sees ALL organisations across the system.
    This is the only view where .all() without an
    organisation filter is intentional and correct.
    """
    organisations = Organisation.objects.all().order_by('name')

    # Platform-wide statistics for the admin dashboard
    total_orgs = organisations.count()
    active_orgs = organisations.filter(is_active=True).count()

    return render(request, 'organisations/organisation_list.html', {
        'organisations': organisations,
        'total_orgs': total_orgs,
        'active_orgs': active_orgs,
    })


@platform_admin_required
def organisation_create(request):
    """
    Platform admin creates a new organisation account.
    After creation, they are redirected to create
    the first HR Admin for that organisation.
    """
    form = OrganisationForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            organisation = form.save(commit=False)
            organisation.created_by = request.user
            organisation.save()

            messages.success(
                request,
                f'Organisation "{organisation.name}" created. '
                f'Now create their first HR Admin account.'
            )
            # Redirect to create the first admin for this org
            return redirect('organisations:create_org_admin', pk=organisation.pk)

    return render(request, 'organisations/organisation_form.html', {
        'form': form,
        'title': 'Onboard New Organisation',
        'button_label': 'Create Organisation',
    })


@platform_admin_required
def organisation_edit(request, pk):
    """
    Platform admin edits an organisation's details.
    Including the subscription percentage.
    """
    organisation = get_object_or_404(Organisation, pk=pk)
    form = OrganisationForm(
        request.POST or None,
        request.FILES or None,
        instance=organisation
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Organisation "{organisation.name}" updated.'
            )
            return redirect('organisations:organisation_list')

    return render(request, 'organisations/organisation_form.html', {
        'form': form,
        'title': f'Edit — {organisation.name}',
        'button_label': 'Save Changes',
        'organisation': organisation,
    })


@platform_admin_required
def organisation_toggle(request, pk):
    """
    Activate or deactivate an organisation.

    When deactivated:
    - The organisation's users cannot log in
    - Their data is preserved
    - They can be reactivated at any time

    We check this during login in the accounts app.
    """
    organisation = get_object_or_404(Organisation, pk=pk)
    organisation.is_active = not organisation.is_active
    organisation.save()

    status = 'activated' if organisation.is_active else 'deactivated'
    messages.success(
        request,
        f'"{organisation.name}" has been {status}.'
    )
    return redirect('organisations:organisation_list')


@platform_admin_required
def create_org_admin(request, pk):
    """
    Creates the first HR Admin account for an organisation.

    Why is this at platform level?
    The first HR Admin cannot be created by the organisation
    because the organisation has no users yet.
    The platform admin bootstraps the first account,
    then the HR Admin can create all other staff accounts.

    This is called the "bootstrapping problem" —
    you need at least one admin to create other admins.
    """
    organisation = get_object_or_404(Organisation, pk=pk)
    form = OrgAdminCreationForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # Create the Django User
            new_user = form.save()

            # Create their UserProfile with hr_admin role
            # automatically linked to the correct organisation
            UserProfile.objects.create(
                user=new_user,
                organisation=organisation,
                role='hr_admin',
            )

            messages.success(
                request,
                f'HR Admin account created for {new_user.get_full_name()} '
                f'at {organisation.name}.'
            )
            return redirect('organisations:organisation_list')

    return render(request, 'organisations/create_org_admin.html', {
        'form': form,
        'organisation': organisation,
        'title': f'Create HR Admin — {organisation.name}',
        'button_label': 'Create HR Admin Account',
    })


# ═══════════════════════════════════════════════════════
# ORGANISATION LEVEL VIEWS
# Organisation super_admin manages their own org settings
# ═══════════════════════════════════════════════════════

@org_super_admin_required
def organisation_settings(request):
    """
    Organisation super_admin updates their own organisation's details.
    They can update contact info and logo.
    They CANNOT change the subscription percentage —
    that field is not in OrganisationSettingsForm.
    """
    organisation = request.user.profile.organisation

    if not organisation:
        messages.error(request, 'No organisation found for your account.')
        return redirect('core:dashboard')

    form = OrganisationSettingsForm(
        request.POST or None,
        request.FILES or None,
        instance=organisation
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Organisation settings updated.')
            return redirect('organisations:settings')

    return render(request, 'organisations/organisation_settings.html', {
        'form': form,
        'organisation': organisation,
    })