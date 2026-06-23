from django.db import models
from django.contrib.auth.models import User
from organisations.models import Organisation


class AppraisalCategory(models.Model):
    """
    Staff groupings within ONE organisation.
    Ministry of Finance's "Admin Staff" is completely
    separate from Ministry of Health's "Admin Staff"
    even though they have the same name.
    The organisation field makes them distinct.
    """
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.organisation})"

    class Meta:
        verbose_name = 'Appraisal Category'
        verbose_name_plural = 'Appraisal Categories'
        # Same category name can exist in different organisations
        # but NOT twice in the same organisation
        unique_together = ['organisation', 'name']


class AppraisalCycle(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cycles'
    )
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        AppraisalCategory,
        on_delete=models.PROTECT,
        related_name='cycles'
    )
    year = models.PositiveIntegerField()
    period_from = models.DateField()
    period_to = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    download_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Amount in Naira employees pay to download their PDF'
    )
    part1_deadline = models.DateField(null=True, blank=True)
    part2_deadline = models.DateField(null=True, blank=True)
    part3_deadline = models.DateField(null=True, blank=True)
    part4_deadline = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.organisation})"

    class Meta:
        verbose_name = 'Appraisal Cycle'
        verbose_name_plural = 'Appraisal Cycles'
        ordering = ['-year']


class PerformanceAspect(models.Model):
    """
    Performance aspects are PLATFORM-LEVEL by default.
    The 16 GEN 79 aspects belong to no organisation —
    they are seeded by the platform and available to all.

    However organisations can create their OWN custom aspects.
    organisation = None means it is a platform default aspect.
    organisation = Finance means it is Finance's custom aspect.
    """
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='aspects',
        help_text='Null means this is a platform default aspect available to all'
    )
    label = models.CharField(max_length=100)
    outstanding_description = models.TextField()
    unsatisfactory_description = models.TextField()
    is_applicable = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = 'Performance Aspect'
        verbose_name_plural = 'Performance Aspects'
        ordering = ['order']


class AppraisalTemplate(models.Model):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='templates'
    )
    name = models.CharField(max_length=200)
    cycle = models.ForeignKey(
        AppraisalCycle,
        on_delete=models.PROTECT,
        related_name='templates'
    )
    aspects = models.ManyToManyField(
        PerformanceAspect,
        through='TemplateAspect',
        related_name='templates'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.cycle.name}"

    class Meta:
        verbose_name = 'Appraisal Template'
        verbose_name_plural = 'Appraisal Templates'


class TemplateAspect(models.Model):
    template = models.ForeignKey(AppraisalTemplate, on_delete=models.CASCADE)
    aspect = models.ForeignKey(PerformanceAspect, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ['template', 'aspect']