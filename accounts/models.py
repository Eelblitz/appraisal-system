from django.db import models
from django.contrib.auth.models import User
from organisations.models import Organisation  # ← NEW IMPORT


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('reporting_officer', 'Reporting Officer'),
        ('countersigning_officer', 'Countersigning Officer'),
        ('hr_admin', 'HR Admin'),
        ('super_admin', 'Super Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # ← NEW FIELD
    # null=True temporarily during migration
    # We will make it required after setting up default data
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='members',
        help_text='Which organisation does this user belong to?'
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='employee'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    local_government = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    section = models.CharField(max_length=100, blank=True)
    qualification = models.TextField(blank=True)
    date_of_first_appointment = models.DateField(null=True, blank=True)
    present_substantive_grade = models.CharField(max_length=100, blank=True)
    date_appointed_to_grade = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    reporting_officer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    countersigning_officer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='countersigned_employees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"

    def get_full_name(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'