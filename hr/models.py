from django.db import models
from django.contrib.auth.models import User


class AppraisalCategory(models.Model):
    """
    Examples: 'Teaching Staff', 'Admin Staff', 'Technical Staff'
    HR creates these to group employees by type
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Appraisal Category'
        verbose_name_plural = 'Appraisal Categories'


class AppraisalCycle(models.Model):
    """
    Examples: '2024 Annual Appraisal', '2025 Mid-Year Review'
    HR creates one cycle per appraisal period
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        AppraisalCategory,
        on_delete=models.PROTECT,  # Prevent deleting a category that has cycles
        related_name='cycles'
    )
    year = models.PositiveIntegerField()
    period_from = models.DateField()
    period_to = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    # The token amount employees pay to download their PDF
    # HR sets this per cycle as you requested
    download_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Amount in Naira employees pay to download their appraisal PDF'
    )

    # Deadlines for each part
    part1_deadline = models.DateField(null=True, blank=True)
    part2_deadline = models.DateField(null=True, blank=True)
    part3_deadline = models.DateField(null=True, blank=True)
    part4_deadline = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.year})"

    class Meta:
        verbose_name = 'Appraisal Cycle'
        verbose_name_plural = 'Appraisal Cycles'
        ordering = ['-year']


class PerformanceAspect(models.Model):
    """
    These are the 16 rated aspects from Part 2 of the GEN 79 form.
    HR can modify the label and descriptions.

    Examples:
    - label: 'Foresight'
    - outstanding_description: 'Anticipates problems and develops solution in advance'
    - unsatisfactory_description: 'Grapples with problems after they arise'
    """
    label = models.CharField(max_length=100)
    outstanding_description = models.TextField(
        help_text='Description for rating A (Outstanding)'
    )
    unsatisfactory_description = models.TextField(
        help_text='Description for rating E (Unsatisfactory)'
    )
    is_applicable = models.BooleanField(
        default=True,
        help_text='Uncheck if this aspect does not apply to certain staff'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Controls the display order on the form'
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = 'Performance Aspect'
        verbose_name_plural = 'Performance Aspects'
        ordering = ['order']


class AppraisalTemplate(models.Model):
    """
    A template ties a cycle to a set of performance aspects.
    This way HR can have different questions for different cycles.

    Example:
    - Template: '2024 Admin Staff Appraisal'
    - Cycle: '2024 Annual'
    - Aspects: All 16 from GEN 79
    """
    name = models.CharField(max_length=200)
    cycle = models.ForeignKey(
        AppraisalCycle,
        on_delete=models.PROTECT,
        related_name='templates'
    )
    aspects = models.ManyToManyField(
        PerformanceAspect,
        through='TemplateAspect',  # We use a through model to control ordering per template
        related_name='templates'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.cycle.name}"

    class Meta:
        verbose_name = 'Appraisal Template'
        verbose_name_plural = 'Appraisal Templates'


class TemplateAspect(models.Model):
    """
    This is the 'through' model between Template and PerformanceAspect.
    It lets HR control the ORDER of aspects per template,
    and whether a specific aspect is required in that template.
    """
    template = models.ForeignKey(AppraisalTemplate, on_delete=models.CASCADE)
    aspect = models.ForeignKey(PerformanceAspect, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ['template', 'aspect']  # No duplicate aspects per template