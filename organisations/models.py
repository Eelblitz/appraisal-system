from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Organisation(models.Model):
    """
    This is the TENANT model — the heart of our SaaS architecture.

    Every piece of data in the system belongs to one organisation.
    Think of this as the "container" that holds everything for
    one ministry or MDA.

    When we query ANY data, we always filter by organisation first.
    This guarantees complete data isolation between ministries.
    """

    # Basic identity
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text='Full official name e.g. Federal Ministry of Finance'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text='Auto-generated URL identifier e.g. federal-ministry-of-finance'
    )
    acronym = models.CharField(
        max_length=20,
        blank=True,
        help_text='Short form e.g. FMF, FIRS, NNPC'
    )

    # Contact information
    email = models.EmailField(
        blank=True,
        help_text='Official contact email of the organisation'
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Branding — used on PDF header
    logo = models.ImageField(
        upload_to='org_logos/',
        null=True,
        blank=True,
        help_text='Organisation logo shown on appraisal PDF'
    )

    # SaaS business logic
    # This is YOUR cut from every employee PDF download
    subscription_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text='Platform percentage from each employee PDF download e.g. 10 means 10%'
    )

    # Platform admin who onboarded this organisation
    # SET_NULL means if the admin account is deleted,
    # the organisation record is kept (we never lose client data)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_organisations'
    )

    # Status control
    # is_active = False means the organisation cannot log in
    # Use this instead of deleting — never delete client data
    is_active = models.BooleanField(
        default=True,
        help_text='Inactive organisations cannot access the system'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Override save() to auto-generate the slug from the name.

        Why override save()?
        We want the slug to be created automatically when HR types
        the organisation name. The admin should not have to type
        both the name AND the slug separately.

        slugify('Federal Ministry of Finance')
        → 'federal-ministry-of-finance'

        We only generate the slug if it doesn't already exist.
        This prevents the slug from changing if the name is edited later
        (that would break existing URLs).
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def calculate_platform_earning(self, amount):
        """
        Given a payment amount, calculate how much goes to the platform.

        Example:
            organisation.subscription_percentage = 10
            organisation.calculate_platform_earning(2000)
            → returns 200.00

        We put this logic ON the model because it belongs to the
        organisation — it knows its own percentage.
        This is called "fat models, thin views" — business logic
        lives in the model, not scattered across views.
        """
        return round((amount * self.subscription_percentage) / 100, 2)

    def calculate_organisation_earning(self, amount):
        """
        The remaining amount after platform takes its cut.

        Example:
            organisation.calculate_organisation_earning(2000)
            → returns 1800.00
        """
        platform_cut = self.calculate_platform_earning(amount)
        return round(amount - platform_cut, 2)

    class Meta:
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisations'
        ordering = ['name']