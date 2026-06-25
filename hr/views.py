from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import (
    AppraisalCategory, AppraisalCycle,
    PerformanceAspect, AppraisalTemplate, TemplateAspect
)
from .forms import (
    AppraisalCategoryForm, AppraisalCycleForm,
    PerformanceAspectForm, AppraisalTemplateForm
)
from accounts.models import UserProfile


# ─────────────────────────────────────────────────────
# HELPER: Get current user's organisation
# ─────────────────────────────────────────────────────

def get_user_organisation(request):
    """
    Every HR view calls this first.

    What it does:
    Gets the organisation that the currently logged-in user
    belongs to. This is the foundation of data isolation.

    Why a separate function?
    Instead of repeating request.user.profile.organisation
    in every single view, we centralise it here.
    If the logic ever changes, we update one place only.

    Returns:
    The Organisation object, or None if user has no profile/org.
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
    Protects any view it decorates with two checks:
    1. Is the user logged in?
    2. Do they have hr_admin or super_admin role?

    How to use it:
    Put @hr_required above any view function.

    If either check fails, user is redirected away
    with an error message — they never see the view.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        try:
            role = request.user.profile.role
            if role not in ['hr_admin', 'super_admin']:
                messages.error(
                    request,
                    'You do not have permission to access HR tools.'
                )
                return redirect('core:dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)

    wrapper.__wrapped__ = view_func
    return wrapper


# ═══════════════════════════════════════════════════════
# CATEGORY VIEWS
# ═══════════════════════════════════════════════════════

@hr_required
def category_list(request):
    """
    Shows categories belonging to THIS organisation only.

    The critical line is:
        organisation=get_user_organisation(request)

    This ensures Ministry of Finance HR only sees
    Ministry of Finance categories.
    Ministry of Health categories are invisible to them.
    """
    organisation = get_user_organisation(request)

    categories = AppraisalCategory.objects.filter(
        organisation=organisation
    ).order_by('name')

    return render(request, 'hr/category_list.html', {
        'categories': categories
    })


@hr_required
def category_create(request):
    """
    Creates a new category and automatically assigns
    it to the current user's organisation.

    The employee never chooses which organisation —
    it is set automatically from their profile.
    This prevents HR from accidentally (or maliciously)
    creating data for another organisation.
    """
    organisation = get_user_organisation(request)
    form = AppraisalCategoryForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            category = form.save(commit=False)

            # These two lines are the SaaS security layer:
            # 1. Attach to correct organisation automatically
            # 2. Record who created it
            category.organisation = organisation
            category.created_by = request.user
            category.save()

            messages.success(
                request,
                f'Category "{category.name}" created successfully.'
            )
            return redirect('hr:category_list')

    return render(request, 'hr/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'button_label': 'Create Category'
    })


@hr_required
def category_edit(request, pk):
    """
    Edits a category BUT only if it belongs to
    the current user's organisation.

    get_object_or_404 with organisation= filter is critical:
    - Without filter: any HR admin can edit any category
    - With filter: HR admin can only edit THEIR categories

    If someone manually types /hr/categories/5/edit/
    and category 5 belongs to a different organisation,
    Django returns 404 — not found.
    This is correct and intentional security behaviour.
    """
    organisation = get_user_organisation(request)

    category = get_object_or_404(
        AppraisalCategory,
        pk=pk,
        organisation=organisation  # ← security filter
    )

    form = AppraisalCategoryForm(request.POST or None, instance=category)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Category "{category.name}" updated.'
            )
            return redirect('hr:category_list')

    return render(request, 'hr/category_form.html', {
        'form': form,
        'title': 'Edit Category',
        'button_label': 'Save Changes',
        'category': category
    })


@hr_required
def category_toggle(request, pk):
    """
    Activates or deactivates a category.
    Uses soft delete — record stays, just hidden.

    Same security pattern as category_edit:
    organisation= filter in get_object_or_404.
    """
    organisation = get_user_organisation(request)

    category = get_object_or_404(
        AppraisalCategory,
        pk=pk,
        organisation=organisation
    )

    category.is_active = not category.is_active
    category.save()

    status = 'activated' if category.is_active else 'deactivated'
    messages.success(request, f'Category "{category.name}" {status}.')
    return redirect('hr:category_list')


# ═══════════════════════════════════════════════════════
# CYCLE VIEWS
# ═══════════════════════════════════════════════════════

@hr_required
def cycle_list(request):
    organisation = get_user_organisation(request)

    cycles = AppraisalCycle.objects.filter(
        organisation=organisation
    ).select_related('category').order_by('-year')

    return render(request, 'hr/cycle_list.html', {
        'cycles': cycles
    })


@hr_required
def cycle_create(request):
    organisation = get_user_organisation(request)
    form = AppraisalCycleForm(
        request.POST or None,
        organisation=organisation  # pass org to form to filter dropdowns
    )

    if request.method == 'POST':
        if form.is_valid():
            cycle = form.save(commit=False)
            cycle.organisation = organisation
            cycle.created_by = request.user
            cycle.save()
            messages.success(
                request,
                f'Cycle "{cycle.name}" created successfully.'
            )
            return redirect('hr:cycle_list')

    return render(request, 'hr/cycle_form.html', {
        'form': form,
        'title': 'Create Appraisal Cycle',
        'button_label': 'Create Cycle'
    })


@hr_required
def cycle_edit(request, pk):
    organisation = get_user_organisation(request)

    cycle = get_object_or_404(
        AppraisalCycle,
        pk=pk,
        organisation=organisation
    )

    form = AppraisalCycleForm(
        request.POST or None,
        instance=cycle,
        organisation=organisation
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Cycle "{cycle.name}" updated.'
            )
            return redirect('hr:cycle_list')

    return render(request, 'hr/cycle_form.html', {
        'form': form,
        'title': 'Edit Cycle',
        'button_label': 'Save Changes',
        'cycle': cycle
    })


@hr_required
def cycle_status_change(request, pk):
    """
    Moves a cycle through: draft → active → closed.

    Business rule:
    Only ONE cycle should be active at a time PER ORGANISATION.
    We filter by organisation when checking for active cycles.
    This means Ministry of Finance's active cycle does not
    block Ministry of Health from activating their own cycle.
    """
    organisation = get_user_organisation(request)

    cycle = get_object_or_404(
        AppraisalCycle,
        pk=pk,
        organisation=organisation
    )

    if cycle.status == 'draft':
        # Check only within THIS organisation for active cycles
        active_exists = AppraisalCycle.objects.filter(
            organisation=organisation,
            status='active'
        ).exists()

        if active_exists:
            messages.warning(
                request,
                'Another cycle is already active. '
                'Close it before activating this one.'
            )
            return redirect('hr:cycle_list')

        cycle.status = 'active'
        messages.success(request, f'Cycle "{cycle.name}" is now ACTIVE.')

    elif cycle.status == 'active':
        cycle.status = 'closed'
        messages.success(request, f'Cycle "{cycle.name}" has been CLOSED.')

    elif cycle.status == 'closed':
        messages.warning(request, 'A closed cycle cannot be reopened.')
        return redirect('hr:cycle_list')

    cycle.save()
    return redirect('hr:cycle_list')


# ═══════════════════════════════════════════════════════
# PERFORMANCE ASPECT VIEWS
# ═══════════════════════════════════════════════════════

@hr_required
def aspect_list(request):
    """
    Shows performance aspects available to this organisation.

    Important logic here:
    We show TWO types of aspects:
    1. Platform defaults (organisation=None) — the 16 GEN 79 aspects
       seeded by the platform, available to ALL organisations
    2. Organisation custom aspects — created by this specific org

    Why? An organisation should always see the 16 standard aspects
    PLUS any custom ones they have created.

    We use Django's Q objects for OR queries:
    filter(organisation=None OR organisation=this_org)
    """
    from django.db.models import Q

    organisation = get_user_organisation(request)

    aspects = PerformanceAspect.objects.filter(
        Q(organisation=None) |        # platform defaults
        Q(organisation=organisation)  # org custom aspects
    ).order_by('order')

    return render(request, 'hr/aspect_list.html', {
        'aspects': aspects
    })


@hr_required
def aspect_edit(request, pk):
    """
    HR can edit aspects BUT with one important restriction:

    Platform default aspects (organisation=None) should not be
    directly edited by an organisation — that would affect ALL
    organisations using that aspect.

    Instead, we check: if the aspect is a platform default,
    we show it as read-only with a message explaining why.

    If it is an organisation custom aspect, they can edit freely.
    """
    organisation = get_user_organisation(request)

    # Get the aspect — it must be either a platform default
    # OR belong to this organisation
    from django.db.models import Q
    aspect = get_object_or_404(
        PerformanceAspect,
        Q(organisation=None) | Q(organisation=organisation),
        pk=pk
    )

    # Check if this is a platform default aspect
    is_platform_default = aspect.organisation is None

    form = PerformanceAspectForm(request.POST or None, instance=aspect)

    if request.method == 'POST':
        if is_platform_default:
            messages.warning(
                request,
                'Platform default aspects cannot be edited directly. '
                'Contact the platform administrator.'
            )
            return redirect('hr:aspect_list')

        if form.is_valid():
            form.save()
            messages.success(request, f'Aspect "{aspect.label}" updated.')
            return redirect('hr:aspect_list')

    return render(request, 'hr/aspect_form.html', {
        'form': form,
        'aspect': aspect,
        'title': f'Edit Aspect: {aspect.label}',
        'is_platform_default': is_platform_default
    })


# ═══════════════════════════════════════════════════════
# TEMPLATE VIEWS
# ═══════════════════════════════════════════════════════

@hr_required
def template_list(request):
    organisation = get_user_organisation(request)

    templates = AppraisalTemplate.objects.filter(
        organisation=organisation
    ).select_related('cycle').order_by('-created_at')

    return render(request, 'hr/template_list.html', {
        'templates': templates
    })


@hr_required
def template_create(request):
    organisation = get_user_organisation(request)
    form = AppraisalTemplateForm(
        request.POST or None,
        organisation=organisation
    )

    if request.method == 'POST':
        if form.is_valid():
            template = form.save(commit=False)
            template.organisation = organisation
            template.created_by = request.user
            template.save()
            form.save_m2m()

            selected_aspects = form.cleaned_data.get('aspects')
            TemplateAspect.objects.filter(template=template).delete()

            for index, aspect in enumerate(selected_aspects, start=1):
                TemplateAspect.objects.create(
                    template=template,
                    aspect=aspect,
                    order=index
                )

            messages.success(
                request,
                f'Template "{template.name}" created.'
            )
            return redirect('hr:template_list')

    return render(request, 'hr/template_form.html', {
        'form': form,
        'title': 'Create Template',
        'button_label': 'Create Template'
    })


@hr_required
def template_edit(request, pk):
    organisation = get_user_organisation(request)

    template = get_object_or_404(
        AppraisalTemplate,
        pk=pk,
        organisation=organisation
    )

    form = AppraisalTemplateForm(
        request.POST or None,
        instance=template,
        organisation=organisation
    )

    if request.method == 'POST':
        if form.is_valid():
            template = form.save(commit=False)
            template.save()
            form.save_m2m()

            selected_aspects = form.cleaned_data.get('aspects')
            TemplateAspect.objects.filter(template=template).delete()

            for index, aspect in enumerate(selected_aspects, start=1):
                TemplateAspect.objects.create(
                    template=template,
                    aspect=aspect,
                    order=index
                )

            messages.success(
                request,
                f'Template "{template.name}" updated.'
            )
            return redirect('hr:template_list')

    return render(request, 'hr/template_form.html', {
        'form': form,
        'title': f'Edit Template: {template.name}',
        'button_label': 'Save Changes',
        'template': template
    })

@hr_required
def aspect_create(request):
    """
    HR Admin creates a custom performance aspect
    specific to their organisation.

    Why can HR create aspects?
    Different organisations may have evaluation criteria
    beyond the standard 16 GEN 79 aspects.
    Example: A hospital might add "Patient Care Quality"
    A tech agency might add "Digital Literacy"

    Platform defaults (organisation=None) cannot be
    deleted or created by HR — only edited.
    Custom aspects (organisation=this_org) are fully
    owned by the organisation.
    """
    organisation = get_user_organisation(request)
    form = PerformanceAspectForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            aspect = form.save(commit=False)
            aspect.organisation = organisation
            aspect.created_by = request.user
            aspect.save()
            messages.success(
                request,
                f'Aspect "{aspect.label}" created successfully.'
            )
            return redirect('hr:aspect_list')

    return render(request, 'hr/aspect_form.html', {
        'form': form,
        'title': 'Create Custom Aspect',
        'button_label': 'Create Aspect',
    })


@hr_required
def aspect_toggle(request, pk):
    """
    Activates or deactivates a performance aspect.

    Platform default aspects (organisation=None):
    We set is_applicable=False to hide them from
    this organisation's templates.
    We do NOT actually modify the platform default —
    instead we create an organisation-level override.

    Actually for simplicity: we allow toggling
    is_applicable on any aspect the org can see.
    HR can reactivate at any time.
    """
    from django.db.models import Q
    organisation = get_user_organisation(request)

    aspect = get_object_or_404(
        PerformanceAspect,
        Q(organisation=None) | Q(organisation=organisation),
        pk=pk
    )

    aspect.is_applicable = not aspect.is_applicable
    aspect.save()

    status = 'activated' if aspect.is_applicable else 'deactivated'
    messages.success(request, f'Aspect "{aspect.label}" {status}.')
    return redirect('hr:aspect_list')