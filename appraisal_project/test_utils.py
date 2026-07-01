"""
Test utilities — shared setup for all test cases.

Why a shared utility?
Every test needs users, organisations, cycles etc.
Instead of repeating 50 lines of setup in every test,
we define it once here and import it everywhere.
"""

from django.contrib.auth.models import User
from organisations.models import Organisation
from accounts.models import UserProfile
from hr.models import (
    AppraisalCategory, AppraisalCycle,
    PerformanceAspect, AppraisalTemplate, TemplateAspect
)
from appraisal.models import Appraisal


def create_organisation(name='Test Ministry', percentage=10):
    """Creates a test organisation."""
    return Organisation.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        acronym='TM',
        email='test@ministry.gov.ng',
        subscription_percentage=percentage,
        is_active=True
    )


def create_user(username, role, organisation, password='testpass123'):
    """
    Creates a Django user and UserProfile with the given role.

    Why use username as-is?
    The caller is responsible for passing a unique username.
    create_full_setup generates unique usernames per org
    to avoid duplicate key errors when testing multiple orgs.
    """
    user = User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password=password,
        first_name=username.capitalize(),
        last_name='Test'
    )
    UserProfile.objects.create(
        user=user,
        organisation=organisation,
        role=role,
        department='Test Department',
        section='Test Section',
        local_government='Test LGA',
        present_substantive_grade='GL 08'
    )
    return user


def create_full_setup(org_name='Test Ministry'):
    """
    Creates a complete test environment.

    Username strategy:
    We prefix every username with a slug of the org name.
    This guarantees unique usernames when called multiple times
    with different org names.

    Example:
        org_name='Ministry A' → prefix='ministry_a'
        usernames: ministry_a_hr_admin, ministry_a_employee, etc.

        org_name='Ministry B' → prefix='ministry_b'
        usernames: ministry_b_hr_admin, ministry_b_employee, etc.

    No collision possible even in the same test database.
    """
    # Create a safe prefix from the org name
    # 'Ministry A' → 'ministry_a'
    prefix = org_name.lower().replace(' ', '_')

    # Organisation
    org = create_organisation(org_name)

    # Users — all with unique prefixed usernames
    hr_admin = create_user(f'{prefix}_hr', 'hr_admin', org)
    reporting_officer = create_user(f'{prefix}_ro', 'reporting_officer', org)
    countersigning_officer = create_user(f'{prefix}_co', 'countersigning_officer', org)
    employee = create_user(f'{prefix}_emp', 'employee', org)

    # Link employee to their officers
    emp_profile = employee.profile
    emp_profile.reporting_officer = reporting_officer.profile
    emp_profile.countersigning_officer = countersigning_officer.profile
    emp_profile.save()

    # HR Setup
    category = AppraisalCategory.objects.create(
        organisation=org,
        name='Admin Staff',
        created_by=hr_admin
    )

    cycle = AppraisalCycle.objects.create(
        organisation=org,
        name='2024 Annual Appraisal',
        category=category,
        year=2024,
        period_from='2024-01-01',
        period_to='2024-12-31',
        download_fee=1000,
        status='active',
        created_by=hr_admin
    )

    # Use get_or_create for aspects since they are platform-level
    # and shared across all orgs — no organisation field
    aspect1, _ = PerformanceAspect.objects.get_or_create(
        label='Foresight',
        defaults={
            'outstanding_description': 'Anticipates problems in advance',
            'unsatisfactory_description': 'Grapples with problems after they arise',
            'order': 1,
            'is_applicable': True
        }
    )
    aspect2, _ = PerformanceAspect.objects.get_or_create(
        label='Punctuality',
        defaults={
            'outstanding_description': 'Regularly punctual',
            'unsatisfactory_description': 'No regard for punctuality',
            'order': 2,
            'is_applicable': True
        }
    )
    aspect3, _ = PerformanceAspect.objects.get_or_create(
        label='Judgement',
        defaults={
            'outstanding_description': 'Decisions consistently sound',
            'unsatisfactory_description': 'Poor perception of merits',
            'order': 3,
            'is_applicable': True
        }
    )

    template = AppraisalTemplate.objects.create(
        organisation=org,
        name='2024 Admin Template',
        cycle=cycle,
        created_by=hr_admin,
        is_active=True
    )

    for i, aspect in enumerate([aspect1, aspect2, aspect3], 1):
        TemplateAspect.objects.create(
            template=template,
            aspect=aspect,
            order=i
        )

    return {
        'org': org,
        'hr_admin': hr_admin,
        'reporting_officer': reporting_officer,
        'countersigning_officer': countersigning_officer,
        'employee': employee,
        'category': category,
        'cycle': cycle,
        'template': template,
        'aspects': [aspect1, aspect2, aspect3],
        'prefix': prefix,  # expose prefix for test login
    }