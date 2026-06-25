from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Appraisal, PartOne, PartTwo, PartThree, PartFour
from hr.models import AppraisalCycle, AppraisalTemplate
from accounts.models import UserProfile
from .forms import PartOneForm


# ─────────────────────────────────────────────────────
# HELPER: Get current user's organisation
# ─────────────────────────────────────────────────────

def get_user_organisation(request):
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
    organisation = get_user_organisation(request)

    cycles = AppraisalCycle.objects.filter(
        organisation=organisation,
        status='active'
    ).order_by('-year')

    templates = AppraisalTemplate.objects.filter(
        organisation=organisation,
        is_active=True
    ).select_related('cycle')

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
        selected_employee_ids = request.POST.getlist('employees')

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

        if template.cycle != cycle:
            messages.error(
                request,
                'The selected template does not belong to '
                'the selected cycle.'
            )
            return redirect('appraisal:assign_appraisals')

        created_count = 0
        skipped_count = 0

        for employee_id in selected_employee_ids:
            try:
                employee_user = User.objects.get(
                    pk=employee_id,
                    profile__organisation=organisation
                )
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
                continue

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
    organisation = get_user_organisation(request)

    appraisals = Appraisal.objects.filter(
        organisation=organisation
    ).select_related(
        'employee', 'cycle', 'template'
    ).order_by('-created_at')

    cycle_filter = request.GET.get('cycle')
    if cycle_filter:
        appraisals = appraisals.filter(cycle__id=cycle_filter)

    status_filter = request.GET.get('status')
    if status_filter:
        appraisals = appraisals.filter(status=status_filter)

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
    organisation = get_user_organisation(request)
    user_role = request.user.profile.role

    if user_role == 'employee':
        appraisal = get_object_or_404(
            Appraisal,
            pk=pk,
            employee=request.user,
            organisation=organisation
        )
    elif user_role == 'reporting_officer':
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
        appraisal = get_object_or_404(
            Appraisal,
            pk=pk,
            organisation=organisation
        )

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
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    return render(request, 'appraisal/team_appraisals.html', {
        'appraisals': appraisals,
        'user_role': user_role,
    })


# ═══════════════════════════════════════════════════════
# PART 1 VIEW — Employee fills personal records
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def part1_form(request, pk):
    """
    The employee fills Part 1 of the GEN 79 form.

    Three behaviours:
    1. PRE-FILL fields 1-3 from UserProfile (read-only)
    2. DRAFT SAVING — employee can save and return later
    3. FINAL SUBMISSION — locks form, notifies reporting officer
    """
    organisation = get_user_organisation(request)

    # Security: employee can only access their OWN appraisal
    appraisal = get_object_or_404(
        Appraisal,
        pk=pk,
        employee=request.user,
        organisation=organisation
    )

    # If already submitted, redirect to detail view
    if appraisal.status != 'pending':
        messages.info(
            request,
            'Part 1 has already been submitted and cannot be edited.'
        )
        return redirect('appraisal:detail', pk=appraisal.pk)

    # Try to get existing draft — do NOT save anything on GET
    # Creating in the database only happens when employee saves
    try:
        part_one = PartOne.objects.get(appraisal=appraisal)
    except PartOne.DoesNotExist:
        # Create Python object in memory only — not saved to DB yet
        part_one = PartOne(appraisal=appraisal)

    # Get profile for pre-filling fields 1-3
    profile = request.user.profile

    # Which button did the employee click?
    action = request.POST.get('action', 'draft')
    is_submitting = (action == 'submit')

    form = PartOneForm(
        request.POST or None,
        instance=part_one
    )

    # Tell the form whether this is final submission
    # so it knows whether to enforce required field validation
    form.is_submitting = is_submitting

    if request.method == 'POST':
        if form.is_valid():
            part_one = form.save(commit=False)
            part_one.appraisal = appraisal

            if is_submitting:
                # Final submission — lock the form
                part_one.is_draft = False
                part_one.submitted_at = timezone.now()
                part_one.save()

                # Advance appraisal status to unlock Part 2
                appraisal.status = 'part1_submitted'
                appraisal.part1_submitted_at = timezone.now()
                appraisal.save()

                messages.success(
                    request,
                    'Part 1 submitted successfully. '
                    'Your Reporting Officer has been notified.'
                )
                return redirect('appraisal:detail', pk=appraisal.pk)

            else:
                # Draft save — keep editable
                part_one.is_draft = True
                part_one.save()

                messages.success(
                    request,
                    'Draft saved. You can continue later.'
                )
                return redirect('appraisal:part1_form', pk=appraisal.pk)

        else:
            messages.error(
                request,
                'Please correct the errors below before submitting.'
            )

    return render(request, 'appraisal/part1_form.html', {
        'form': form,
        'appraisal': appraisal,
        'profile': profile,
        'part_one': part_one,
        'is_draft': part_one.is_draft,
    })