from django.db import models
from django.contrib.auth.models import User


# This extends Django's built-in User model
# Django already gives us: username, email, password, first_name, last_name
# We add everything else our system needs here

class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('reporting_officer', 'Reporting Officer'),
        ('countersigning_officer', 'Countersigning Officer'),
        ('hr_admin', 'HR Admin'),
        ('super_admin', 'Super Admin'),
    ]

    # One profile per user — if user is deleted, profile is deleted too
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='employee')

    # Personal info matching Part 1 of the appraisal form
    date_of_birth = models.DateField(null=True, blank=True)
    local_government = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    section = models.CharField(max_length=100, blank=True)
    qualification = models.TextField(blank=True)
    date_of_first_appointment = models.DateField(null=True, blank=True)
    present_substantive_grade = models.CharField(max_length=100, blank=True)
    date_appointed_to_grade = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # Who is this employee's reporting officer?
    # A reporting officer can have many employees under them
    reporting_officer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )

    # Who is the countersigning officer for this employee?
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