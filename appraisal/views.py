from .forms import PartOneForm, PartTwoForm, PartThreeForm, PartFourForm
from .models import (
    Appraisal, PartOne, PartTwo, PartThree,
    PartFour, AppraisalAspectRating
)
from hr.models import AppraisalCycle, AppraisalTemplate, PerformanceAspect
from django.db.models import Q
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
    
# ═══════════════════════════════════════════════════════
# PART 2 VIEW — Reporting Officer fills assessment
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def part2_form(request, pk):
    """
    Reporting Officer fills Part 2 of the GEN 79 form.

    Three key behaviours:

    1. REFERENCE — Shows employee's main duties from Part 1
       at the top so the officer has context while rating.

    2. DYNAMIC ASPECTS — Loads aspects from the template
       assigned to this appraisal. Different organisations
       see different aspects depending on their template.

    3. ASPECT RATINGS — Each aspect gets its own A-E radio
       button row. Ratings are stored in AppraisalAspectRating,
       not as hardcoded fields on PartTwo.

    Security:
       Only the assigned Reporting Officer can fill Part 2.
       We verify via employee's profile.reporting_officer.
    """
    organisation = get_user_organisation(request)

    # Security: only the reporting officer of this employee
    # can fill Part 2 — not just any reporting officer
    appraisal = get_object_or_404(
        Appraisal,
        pk=pk,
        organisation=organisation,
        employee__profile__reporting_officer=request.user.profile
    )

    # Part 2 only available after employee submits Part 1
    if appraisal.status not in ['part1_submitted', 'part2_submitted']:
        messages.warning(
            request,
            'Part 2 is not available yet. '
            'The employee must submit Part 1 first.'
        )
        return redirect('appraisal:detail', pk=appraisal.pk)

    # If already submitted, redirect to detail
    if appraisal.status == 'part2_submitted':
        messages.info(
            request,
            'Part 2 has already been submitted.'
        )
        return redirect('appraisal:detail', pk=appraisal.pk)

    # Get Part 1 for reference (main duties display)
    try:
        part_one = appraisal.part_one
    except PartOne.DoesNotExist:
        part_one = None

    # Get or create Part 2 draft
    try:
        part_two = PartTwo.objects.get(appraisal=appraisal)
    except PartTwo.DoesNotExist:
        part_two = PartTwo(
            appraisal=appraisal,
            reporting_officer=request.user
        )

    # Load aspects from the template assigned to this appraisal
    # This is the dynamic aspect loading — organisation specific
    # We show:
    # 1. Platform defaults (organisation=None) that are active
    # 2. Custom aspects belonging to this organisation
    # Both filtered to aspects included in the template
    template_aspect_ids = appraisal.template.aspects.values_list(
        'id', flat=True
    )

    aspects = PerformanceAspect.objects.filter(
        id__in=template_aspect_ids,
        is_applicable=True
    ).order_by('order')

    # Get existing ratings if this is a draft being edited
    # Build a dict: {aspect_id: rating} for easy template access
    existing_ratings = {}
    if part_two.pk:
        for rating_obj in part_two.aspect_ratings.all():
            existing_ratings[rating_obj.aspect_id] = rating_obj.rating

    action = request.POST.get('action', 'draft')
    is_submitting = (action == 'submit')

    form = PartTwoForm(request.POST or None, instance=part_two)
    form.is_submitting = is_submitting

    if request.method == 'POST':
        if form.is_valid():
            part_two = form.save(commit=False)
            part_two.appraisal = appraisal
            part_two.reporting_officer = request.user
            part_two.save()

            # Save aspect ratings
            # For each aspect, read the rating from POST data
            # POST field name: rating_<aspect_id>
            for aspect in aspects:
                field_name = f'rating_{aspect.id}'
                rating_value = request.POST.get(field_name, 'C')

                # get_or_create per aspect — safe to call multiple times
                aspect_rating, created = (
                    AppraisalAspectRating.objects.get_or_create(
                        part_two=part_two,
                        aspect=aspect,
                        defaults={'rating': rating_value}
                    )
                )
                if not created:
                    # Update existing rating if already saved
                    aspect_rating.rating = rating_value
                    aspect_rating.save()

            if is_submitting:
                part_two.is_draft = False
                part_two.submitted_at = timezone.now()
                part_two.save()

                # Advance status to part2_submitted
                # Part 3 is filled by the SAME reporting officer
                # immediately after Part 2, so we redirect to Part 3
                appraisal.status = 'part2_submitted'
                appraisal.part2_submitted_at = timezone.now()
                appraisal.save()

                messages.success(
                    request,
                    'Part 2 submitted successfully. '
                    'Please proceed to fill Part 3.'
                )
                # Redirect directly to Part 3 since same officer fills it
                return redirect('appraisal:part3_form', pk=appraisal.pk)

            else:
                part_two.is_draft = True
                part_two.save()
                messages.success(request, 'Draft saved.')
                return redirect('appraisal:part2_form', pk=appraisal.pk)

        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )

    return render(request, 'appraisal/part2_form.html', {
        'form': form,
        'appraisal': appraisal,
        'part_one': part_one,
        'aspects': aspects,
        'existing_ratings': existing_ratings,
        'is_draft': part_two.is_draft if part_two.pk else True,
        'rating_choices': AppraisalAspectRating.RATING_CHOICES,
    })


# ═══════════════════════════════════════════════════════
# PART 3 VIEW — Reporting Officer fills training/promotability
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def part3_form(request, pk):
    """
    Reporting Officer fills Part 3 immediately after Part 2.
    Training needs, next job recommendations, promotability.

    Why same officer fills Part 2 and Part 3?
    The GEN 79 form has both on the same assessment sheet.
    The reporting officer fills all of fields 12-19.
    Part 3 is just the continuation of the officer's assessment.

    After Part 3 submission:
    Status changes to 'part3_submitted'
    Countersigning Officer can now fill Part 4.
    """
    organisation = get_user_organisation(request)

    appraisal = get_object_or_404(
        Appraisal,
        pk=pk,
        organisation=organisation,
        employee__profile__reporting_officer=request.user.profile
    )

    # Part 3 available only after Part 2 is submitted
    if appraisal.status not in ['part2_submitted', 'part3_submitted']:
        messages.warning(
            request,
            'Part 3 is not available yet. Submit Part 2 first.'
        )
        return redirect('appraisal:detail', pk=appraisal.pk)

    if appraisal.status == 'part3_submitted':
        messages.info(request, 'Part 3 has already been submitted.')
        return redirect('appraisal:detail', pk=appraisal.pk)

    try:
        part_three = PartThree.objects.get(appraisal=appraisal)
    except PartThree.DoesNotExist:
        part_three = PartThree(
            appraisal=appraisal,
            reporting_officer=request.user
        )

    action = request.POST.get('action', 'draft')
    is_submitting = (action == 'submit')

    form = PartThreeForm(request.POST or None, instance=part_three)
    form.is_submitting = is_submitting

    if request.method == 'POST':
        if form.is_valid():
            part_three = form.save(commit=False)
            part_three.appraisal = appraisal
            part_three.reporting_officer = request.user
            part_three.save()

            if is_submitting:
                part_three.is_draft = False
                part_three.submitted_at = timezone.now()
                part_three.save()

                appraisal.status = 'part3_submitted'
                appraisal.part3_submitted_at = timezone.now()
                appraisal.save()

                messages.success(
                    request,
                    'Part 3 submitted successfully. '
                    'The Countersigning Officer has been notified.'
                )
                return redirect('appraisal:detail', pk=appraisal.pk)

            else:
                part_three.is_draft = True
                part_three.save()
                messages.success(request, 'Draft saved.')
                return redirect('appraisal:part3_form', pk=appraisal.pk)

        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'appraisal/part3_form.html', {
        'form': form,
        'appraisal': appraisal,
        'is_draft': part_three.is_draft if part_three.pk else True,
    })


# ═══════════════════════════════════════════════════════
# PART 4 VIEW — Countersigning Officer finalizes
# ═══════════════════════════════════════════════════════

@appraisal_login_required
def part4_form(request, pk):
    """
    Countersigning Officer fills Part 4 — the final step.

    After Part 4 submission:
    - Status changes to 'completed'
    - Employee is notified
    - Employee can now pay and download the PDF

    Security:
    Only the assigned Countersigning Officer of this
    employee can fill Part 4.
    """
    organisation = get_user_organisation(request)

    appraisal = get_object_or_404(
        Appraisal,
        pk=pk,
        organisation=organisation,
        employee__profile__countersigning_officer=request.user.profile
    )

    if appraisal.status not in ['part3_submitted', 'completed']:
        messages.warning(
            request,
            'Part 4 is not available yet. '
            'Parts 1, 2 and 3 must be completed first.'
        )
        return redirect('appraisal:detail', pk=appraisal.pk)

    if appraisal.status == 'completed':
        messages.info(request, 'This appraisal has been completed.')
        return redirect('appraisal:detail', pk=appraisal.pk)

    try:
        part_four = PartFour.objects.get(appraisal=appraisal)
    except PartFour.DoesNotExist:
        part_four = PartFour(
            appraisal=appraisal,
            countersigning_officer=request.user
        )

    action = request.POST.get('action', 'draft')
    is_submitting = (action == 'submit')

    form = PartFourForm(request.POST or None, instance=part_four)
    form.is_submitting = is_submitting

    if request.method == 'POST':
        if form.is_valid():
            part_four = form.save(commit=False)
            part_four.appraisal = appraisal
            part_four.countersigning_officer = request.user
            part_four.save()

            if is_submitting:
                part_four.is_draft = False
                part_four.submitted_at = timezone.now()
                part_four.save()

                # completed = all 4 parts done
                # Employee can now pay and download PDF
                appraisal.status = 'completed'
                appraisal.part4_submitted_at = timezone.now()
                appraisal.save()

                messages.success(
                    request,
                    'Part 4 submitted. The appraisal is now complete. '
                    'The employee can download their PDF.'
                )
                return redirect('appraisal:detail', pk=appraisal.pk)

            else:
                part_four.is_draft = True
                part_four.save()
                messages.success(request, 'Draft saved.')
                return redirect('appraisal:part4_form', pk=appraisal.pk)

        else:
            messages.error(request, 'Please correct the errors below.')

    # Get Part 2 summary for countersigning officer reference
    try:
        part_two = appraisal.part_two
        aspect_ratings = part_two.aspect_ratings.select_related(
            'aspect'
        ).order_by('aspect__order')
    except PartTwo.DoesNotExist:
        part_two = None
        aspect_ratings = []

    return render(request, 'appraisal/part4_form.html', {
        'form': form,
        'appraisal': appraisal,
        'part_two': part_two,
        'aspect_ratings': aspect_ratings,
        'is_draft': part_four.is_draft if part_four.pk else True,
    })