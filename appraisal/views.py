from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Appraisal, PartOne, PartTwo, PartThree, PartFour
from hr.models import AppraisalCycle, AppraisalTemplate
from accounts.models import UserProfile


# ─────────────────────────────────────────────────────
# HELPER: Get current user's organisation
# ─────────────────────────────────────────────────────

def get_user_organisation(request):
    """
    Returns the organisation of the logged-in user.
    Called at the start of every view for data isolation.
    """
    try:
        return request.user.profile.organisation
    except UserProfile.DoesNotExist:
        return None


# ─────────────────────────────────────────────────────
# HELPER: HR role check decorator
# ─────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────
# HELPER: Login required decorator
# ─────────────────────────────────────────────────────

def appraisal_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func
    return wrapper


# ═══════════════════════════════════════════════════════
# HR VIEWS — Appraisal Assignment
# ═══════════════════════════════════════════════════════

@hr_required
def assign_appraisals(request):
    """
    HR Admin assigns appraisals in bulk by category.

    The flow:
    Step 1 (GET):
        Show form to select cycle and template
        Show all employees grouped by their category

    Step 2 (POST):
        Read selected employee IDs from form
        Create one Appraisal record per selected employee
        Skip any already assigned to this cycle
        Report results to HR Admin

    Why bulk by category?
    Government ministries have many employees.
    Assigning one at a time would take hours.
    Bulk assignment by category saves time and
    reduces the chance of missing someone.
    """
    organisation = get_user_organisation(request)

    # Only active cycles can receive new appraisal assignments
    # Draft cycles are not ready, closed cycles are finished
    cycles = AppraisalCycle.objects.filter(
        organisation=organisation,
        status='active'
    ).order_by('-year')

    # All templates in this organisation
    templates = AppraisalTemplate.objects.filter(
        organisation=organisation,
        is_active=True
    ).select_related('cycle')

    # Get all employees in this organisation
    # We group them by category in the template
    employees = UserProfile.objects.filter(
        organisation=organisation,
        role='employee'
    ).select_related('user').order_by(
        'department',
        'user__last_name'
    )

    if request.method == 'POST':
        cycle_id = request.POST.get('cycle')
        template_id = request.POST.get('template')

        # getlist gets ALL checked checkbox values
        # When HR ticks multiple employees, each checkbox
        # sends its value — getlist collects them all into a list
        selected_employee_ids = request.POST.getlist('employees')

        # Validate required fields
        if not cycle_id or not template_id:
            messages.error(
                request,
                'Please select both a cycle and a template.'
            )
            return redirect('appraisal:assign_appraisals')

        if not selected_employee_ids:
            messages.error(
                request,
                'Please select at least one employee.'
            )
            return redirect('appraisal:assign_appraisals')

        # Fetch selected cycle and template
        # Both must belong to THIS organisation — security filter
        cycle = get_object_or_404(
            AppraisalCycle,
            pk=cycle_id,
            organisation=organisation
        )
        template = get_object_or_404(
            AppraisalTemplate,
            pk=template_id,
            organisation=organisation
        )

        # Validate template belongs to selected cycle
        if template.cycle != cycle:
            messages.error(
                request,
                'The selected template does not belong to '
                'the selected cycle.'
            )
            return redirect('appraisal:assign_appraisals')

        # Process each selected employee
        created_count = 0
        skipped_count = 0

        for employee_id in selected_employee_ids:
            try:
                # Get the User object for this employee
                employee_user = User.objects.get(
                    pk=employee_id,
                    profile__organisation=organisation  # security check
                )

                # get_or_create is the safe way to do this:
                # If appraisal already exists for this employee+cycle,
                # it returns the existing one with created=False
                # If it does not exist, it creates a new one
                # with created=True
                # This prevents duplicate appraisals
                appraisal, created = Appraisal.objects.get_or_create(
                    employee=employee_user,
                    cycle=cycle,
                    defaults={
                        'organisation': organisation,
                        'template': template,
                        'status': 'pending',
                    }
                )

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            except User.DoesNotExist:
                # If employee ID is invalid or from another org, skip
                continue

        # Build a clear result message for HR Admin
        if created_count > 0:
            msg = f'{created_count} appraisal(s) assigned successfully.'
            if skipped_count > 0:
                msg += (
                    f' {skipped_count} skipped '
                    f'(already assigned to this cycle).'
                )
            messages.success(request, msg)
        else:
            messages.warning(
                request,
                f'No new appraisals created. '
                f'{skipped_count} employee(s) were already '
                f'assigned to this cycle.'
            )

        return redirect('appraisal:assign_appraisals')

    return render(request, 'appraisal/assign_appraisals.html', {
        'cycles': cycles,
        'templates': templates,
        'employees': employees,
    })


@hr_required
def appraisal_list_hr(request):
    """
    HR Admin sees ALL appraisals in their organisation.
    Can filter by cycle and status.
    """
    organisation = get_user_organisation(request)

    appraisals = Appraisal.objects.filter(
        organisation=organisation
    ).select_related(
        'employee', 'cycle', 'template'
    ).order_by('-created_at')

    # Filter by cycle if HR selects one
    cycle_filter = request.GET.get('cycle')
    if cycle_filter:
        appraisals = appraisals.filter(cycle__id=cycle_filter)

    # Filter by status if HR selects one
    status_filter = request.GET.get('status')
    if status_filter:
        appraisals = appraisals.filter(status=status_filter)

    # Available cycles for the filter dropdown
    cycles = AppraisalCycle.objects.filter(
        organisation=organisation
    ).order_by('-year')

    return render(request, 'appraisal/appraisal_list_hr.html', {
        'appraisals': appraisals,
        'cycles': cycles,
        'cycle_filter': cycle_filter,
        'status_filter': status_filter,
        'status_choices': Appraisal.STATUS_CHOICES,
    })


# ═══════════════════════════════════════════════════════
# EMPLOYEE VIEWS — My Appraisals
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def my_appraisals(request):
    """
    Employee sees ONLY their own appraisals.

    The filter employee=request.user ensures an employee
    can never see another employee's appraisals.
    Combined with organisation filter for extra security.
    """
    organisation = get_user_organisation(request)

    appraisals = Appraisal.objects.filter(
        employee=request.user,
        organisation=organisation
    ).select_related('cycle', 'template').order_by('-created_at')

    return render(request, 'appraisal/my_appraisals.html', {
        'appraisals': appraisals,
    })


@appraisal_login_required
def appraisal_detail(request, pk):
    """
    Shows full details of one appraisal.
    Different roles see different information:

    Employee → sees Part 1 status, overall progress
    Reporting Officer → sees Part 1, can access Part 2/3
    Countersigning Officer → sees Parts 1-3, can access Part 4
    HR Admin → sees everything
    """
    organisation = get_user_organisation(request)
    user_role = request.user.profile.role

    # Build the base query — who can see this appraisal?
    if user_role == 'employee':
        # Employees can only see their own appraisal
        appraisal = get_object_or_404(
            Appraisal,
            pk=pk,
            employee=request.user,
            organisation=organisation
        )
    elif user_role == 'reporting_officer':
        # Reporting officer sees appraisals of their subordinates
        appraisal = get_object_or_404(
            Appraisal,
            pk=pk,
            organisation=organisation,
            employee__profile__reporting_officer=request.user.profile
        )
    elif user_role == 'countersigning_officer':
        appraisal = get_object_or_404(
            Appraisal,
            pk=pk,
            organisation=organisation,
            employee__profile__countersigning_officer=request.user.profile
        )
    else:
        # HR Admin and Super Admin see all appraisals
        appraisal = get_object_or_404(
            Appraisal,
            pk=pk,
            organisation=organisation
        )

    # Check which parts exist already
    has_part1 = hasattr(appraisal, 'part_one')
    has_part2 = hasattr(appraisal, 'part_two')
    has_part3 = hasattr(appraisal, 'part_three')
    has_part4 = hasattr(appraisal, 'part_four')

    return render(request, 'appraisal/appraisal_detail.html', {
        'appraisal': appraisal,
        'has_part1': has_part1,
        'has_part2': has_part2,
        'has_part3': has_part3,
        'has_part4': has_part4,
        'user_role': user_role,
    })


@appraisal_login_required
def team_appraisals(request):
    """
    Reporting Officers and Countersigning Officers see
    appraisals of their team members.

    Reporting Officer sees:
        Employees where reporting_officer = their profile

    Countersigning Officer sees:
        Employees where countersigning_officer = their profile
    """
    organisation = get_user_organisation(request)
    user_role = request.user.profile.role

    if user_role == 'reporting_officer':
        appraisals = Appraisal.objects.filter(
            organisation=organisation,
            employee__profile__reporting_officer=request.user.profile
        ).select_related('employee', 'cycle').order_by('-created_at')

    elif user_role == 'countersigning_officer':
        appraisals = Appraisal.objects.filter(
            organisation=organisation,
            employee__profile__countersigning_officer=request.user.profile
        ).select_related('employee', 'cycle').order_by('-created_at')

    elif user_role in ['hr_admin', 'super_admin']:
        appraisals = Appraisal.objects.filter(
            organisation=organisation
        ).select_related('employee', 'cycle').order_by('-created_at')

    else:
        # Regular employees should not access team appraisals
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    return render(request, 'appraisal/team_appraisals.html', {
        'appraisals': appraisals,
        'user_role': user_role,
    })