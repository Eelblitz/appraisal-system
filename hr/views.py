from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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


# ─────────────────────────────────────────────
# HELPER: Role check decorator
# ─────────────────────────────────────────────
# Instead of copying this role-check block into every view,
# we create one reusable function that wraps any view.
# This is called the "decorator pattern".

def hr_required(view_func):
    """
    A custom decorator that:
    1. Checks the user is logged in
    2. Checks the user has hr_admin or super_admin role
    3. If not, redirects them away with an error message

    Usage: put @hr_required above any view function
    """
    def wrapper(request, *args, **kwargs):
        # First check: are they logged in?
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        # Second check: do they have the right role?
        try:
            role = request.user.profile.role
            if role not in ['hr_admin', 'super_admin']:
                messages.error(request, 'You do not have permission to access HR tools.')
                return redirect('core:dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Profile not found. Contact system admin.')
            return redirect('core:dashboard')

        # All checks passed — run the actual view
        return view_func(request, *args, **kwargs)

    # This line preserves the original function name
    # Without it, Django gets confused when multiple views use this decorator
    wrapper.__wrapped__ = view_func
    return wrapper


# ═══════════════════════════════════════════════
# CATEGORY VIEWS
# ═══════════════════════════════════════════════

@hr_required
def category_list(request):
    """
    Shows all appraisal categories.
    HR can see, create, edit and deactivate categories here.
    """
    categories = AppraisalCategory.objects.all().order_by('name')
    return render(request, 'hr/category_list.html', {
        'categories': categories
    })


@hr_required
def category_create(request):
    """
    GET  → show empty category form
    POST → validate and save new category
    """
    form = AppraisalCategoryForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # commit=False means: build the object but don't save to DB yet
            # This gives us a chance to add extra fields (created_by)
            # before the final save
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('hr:category_list')

    return render(request, 'hr/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'button_label': 'Create Category'
    })


@hr_required
def category_edit(request, pk):
    """
    Same as create but pre-fills the form with existing data.
    get_object_or_404 fetches the category by ID.
    If it doesn't exist, Django automatically shows a 404 page.
    """
    category = get_object_or_404(AppraisalCategory, pk=pk)
    form = AppraisalCategoryForm(request.POST or None, instance=category)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
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
    We never DELETE categories — that would break historical appraisal records.
    Instead we toggle is_active on/off.
    This is called "soft delete" — the record stays in the database
    but is hidden from active use.
    """
    category = get_object_or_404(AppraisalCategory, pk=pk)

    # Flip the boolean: True becomes False, False becomes True
    category.is_active = not category.is_active
    category.save()

    status = 'activated' if category.is_active else 'deactivated'
    messages.success(request, f'Category "{category.name}" {status}.')
    return redirect('hr:category_list')


# ═══════════════════════════════════════════════
# CYCLE VIEWS
# ═══════════════════════════════════════════════

@hr_required
def cycle_list(request):
    """
    Shows all appraisal cycles ordered by most recent year first.
    select_related('category') fetches the linked category in the
    same database query — more efficient than separate queries.
    """
    cycles = AppraisalCycle.objects.select_related('category').order_by('-year')
    return render(request, 'hr/cycle_list.html', {'cycles': cycles})


@hr_required
def cycle_create(request):
    form = AppraisalCycleForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            cycle = form.save(commit=False)
            cycle.created_by = request.user
            cycle.save()
            messages.success(request, f'Cycle "{cycle.name}" created successfully.')
            return redirect('hr:cycle_list')

    return render(request, 'hr/cycle_form.html', {
        'form': form,
        'title': 'Create Appraisal Cycle',
        'button_label': 'Create Cycle'
    })


@hr_required
def cycle_edit(request, pk):
    cycle = get_object_or_404(AppraisalCycle, pk=pk)
    form = AppraisalCycleForm(request.POST or None, instance=cycle)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Cycle "{cycle.name}" updated successfully.')
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
    Moves a cycle through its lifecycle: draft → active → closed.
    Only one cycle should be active at a time — when HR activates
    a new cycle, we warn them if another is already active.
    """
    cycle = get_object_or_404(AppraisalCycle, pk=pk)

    if cycle.status == 'draft':
        # Check if another cycle is already active
        active_exists = AppraisalCycle.objects.filter(status='active').exists()
        if active_exists:
            messages.warning(
                request,
                'Another cycle is already active. Close it before activating this one.'
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


# ═══════════════════════════════════════════════
# PERFORMANCE ASPECT VIEWS
# ═══════════════════════════════════════════════

@hr_required
def aspect_list(request):
    """
    Shows all 16 GEN 79 performance aspects.
    HR can edit the descriptions but cannot delete them
    (they are the foundation of every appraisal).
    """
    aspects = PerformanceAspect.objects.all().order_by('order')
    return render(request, 'hr/aspect_list.html', {'aspects': aspects})


@hr_required
def aspect_edit(request, pk):
    """
    HR can update the label and descriptions of any aspect.
    This is why we made them editable — organizations may want
    to rephrase the GEN 79 descriptions to fit their context.
    """
    aspect = get_object_or_404(PerformanceAspect, pk=pk)
    form = PerformanceAspectForm(request.POST or None, instance=aspect)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Aspect "{aspect.label}" updated.')
            return redirect('hr:aspect_list')

    return render(request, 'hr/aspect_form.html', {
        'form': form,
        'aspect': aspect,
        'title': f'Edit Aspect: {aspect.label}'
    })


# ═══════════════════════════════════════════════
# TEMPLATE VIEWS
# ═══════════════════════════════════════════════

@hr_required
def template_list(request):
    templates = AppraisalTemplate.objects.select_related('cycle').order_by('-created_at')
    return render(request, 'hr/template_list.html', {'templates': templates})


@hr_required
def template_create(request):
    """
    HR creates a template and selects which aspects to include.
    The aspects are linked through the TemplateAspect 'through' model
    we created earlier.
    """
    form = AppraisalTemplateForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            # Save the ManyToMany aspects relationship
            # This is needed when using commit=False with ManyToMany fields
            form.save_m2m()

            # Now create TemplateAspect entries with proper ordering
            # We clear any auto-created ones first, then rebuild with order
            selected_aspects = form.cleaned_data.get('aspects')
            TemplateAspect.objects.filter(template=template).delete()

            for index, aspect in enumerate(selected_aspects, start=1):
                TemplateAspect.objects.create(
                    template=template,
                    aspect=aspect,
                    order=index
                )

            messages.success(request, f'Template "{template.name}" created successfully.')
            return redirect('hr:template_list')

    return render(request, 'hr/template_form.html', {
        'form': form,
        'title': 'Create Template',
        'button_label': 'Create Template'
    })


@hr_required
def template_edit(request, pk):
    template = get_object_or_404(AppraisalTemplate, pk=pk)
    form = AppraisalTemplateForm(request.POST or None, instance=template)

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

            messages.success(request, f'Template "{template.name}" updated.')
            return redirect('hr:template_list')

    return render(request, 'hr/template_form.html', {
        'form': form,
        'title': f'Edit Template: {template.name}',
        'button_label': 'Save Changes',
        'template': template
    })