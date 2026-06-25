from django.db import models
from django.contrib.auth.models import User
from hr.models import AppraisalCycle, AppraisalTemplate, PerformanceAspect
from organisations.models import Organisation


class Appraisal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('part1_submitted', 'Part 1 Submitted'),
        ('part2_submitted', 'Part 2 Submitted'),
        ('part3_submitted', 'Part 3 Submitted'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    # Organisation added here — PartOne/Two/Three/Four
    # automatically belong to the same org via this Appraisal
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='appraisals'
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='appraisals'
    )
    cycle = models.ForeignKey(
        AppraisalCycle,
        on_delete=models.PROTECT,
        related_name='appraisals'
    )
    template = models.ForeignKey(
        AppraisalTemplate,
        on_delete=models.PROTECT,
        related_name='appraisals'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    part1_submitted_at = models.DateTimeField(null=True, blank=True)
    part2_submitted_at = models.DateTimeField(null=True, blank=True)
    part3_submitted_at = models.DateTimeField(null=True, blank=True)
    part4_submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.cycle.name}"

    class Meta:
        unique_together = ['employee', 'cycle']
        ordering = ['-created_at']


# PartOne, PartTwo, PartThree, PartFour remain exactly the same
# No organisation field needed — they link to Appraisal which has it
class PartOne(models.Model):
    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        related_name='part_one'
    )
    qualification = models.TextField(
        help_text='Degree, Diploma, Certificate etc.'
    )
    date_of_first_appointment = models.DateField(null=True, blank=True)
    present_substantive_grade = models.CharField(max_length=100)
    date_appointed_to_grade = models.DateField(null=True, blank=True)
    acting_appointment = models.TextField(blank=True)
    courses_undertaken = models.TextField(blank=True)
    days_absent_sick = models.PositiveIntegerField(default=0)
    present_job = models.CharField(max_length=200)
    job_description = models.TextField()
    main_duty_1 = models.TextField(blank=True)
    main_duty_2 = models.TextField(blank=True)
    main_duty_3 = models.TextField(blank=True)
    main_duty_4 = models.TextField(blank=True)
    main_duty_5 = models.TextField(blank=True)
    adhoc_duties = models.TextField(blank=True)
    is_draft = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Part 1 — {self.appraisal}"


class PartTwo(models.Model):
    """
    PART TWO — Reporting Officer's Assessment
    Fields 12, 13, 14 and overall rating.

    IMPORTANT ARCHITECTURE DECISION:
    We removed the 16 hardcoded rating fields
    (rating_foresight, rating_penetration etc.)

    Instead, ratings are stored in AppraisalAspectRating
    which links PartTwo → PerformanceAspect → rating (A-E)

    Why?
    1. Different organisations use different aspects
    2. HR can add/remove aspects per template
    3. Dynamic approach scales to any number of aspects
    4. One source of truth for aspect data
    """

    OVERALL_RATING_CHOICES = [
        ('1', '1 - Outstanding'),
        ('2', '2 - Very Good'),
        ('3', '3 - Good'),
        ('4', '4 - Fair'),
        ('5', '5 - Unsatisfactory'),
    ]

    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        related_name='part_two'
    )

    # Field 12
    agrees_with_job_description = models.BooleanField(
        default=True,
        verbose_name='Do you agree with the job description?'
    )
    job_description_disagreement = models.TextField(
        blank=True,
        verbose_name='If NO, state unresolved differences'
    )

    # Field 13
    performance_assessment = models.TextField(
        verbose_name='Assessment of Performance',
        help_text=(
            'How effective is he/she in the performance '
            'of duties set out in 11(a)?'
        )
    )

    # Field 14 overall rating (diamond boxes 1-5)
    overall_rating = models.CharField(
        max_length=1,
        choices=OVERALL_RATING_CHOICES,
        verbose_name='Overall Performance Rating'
    )

    # Reporting officer signature fields
    reporting_officer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='part_two_reports'
    )
    reporting_officer_grade = models.CharField(
        max_length=100,
        blank=True
    )
    reporting_officer_job_title = models.CharField(
        max_length=200,
        blank=True
    )
    years_known = models.PositiveIntegerField(
        default=0,
        help_text='He has served under me for the past X years'
    )

    is_draft = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Part 2 — {self.appraisal}"
    
class PartThree(models.Model):
    PROMOTION_FITNESS_CHOICES = [
        ('well_fitted', 'Well Fitted'),
        ('fitted', 'Fitted'),
        ('not_fitted', 'Not Fitted'),
    ]

    LONG_TERM_POTENTIAL_CHOICES = [
        ('1', '1 - Unlikely to progress further'),
        ('2', '2 - Potential to rise about one grade but probably no further'),
        ('3', '3 - Potential to rise two or three grades'),
        ('4', '4 - Exceptional potential'),
    ]

    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        related_name='part_three'
    )
    training_needs = models.TextField(blank=True)
    training_how_met = models.TextField(blank=True)
    different_job_same_grade = models.BooleanField(default=False)
    transfer_to_another_cadre = models.BooleanField(default=False)
    next_job_reasons = models.TextField(blank=True)
    promotion_fitness = models.CharField(max_length=15, choices=PROMOTION_FITNESS_CHOICES, blank=True)
    promotion_to_grade = models.CharField(max_length=100, blank=True)
    promotion_comment = models.TextField(blank=True)
    special_promotion_grade = models.CharField(max_length=100, blank=True)
    special_promotion_reasons = models.TextField(blank=True)
    long_term_potential = models.CharField(max_length=1, choices=LONG_TERM_POTENTIAL_CHOICES, blank=True)
    general_remarks = models.TextField(blank=True)
    years_served_under_reporting_officer = models.PositiveIntegerField(default=0)
    reporting_officer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='part_three_reports'
    )
    reporting_officer_grade = models.CharField(max_length=100, blank=True)
    reporting_officer_name = models.CharField(max_length=200, blank=True)
    is_draft = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Part 3 — {self.appraisal}"


class PartFour(models.Model):
    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        related_name='part_four'
    )
    countersigning_report = models.TextField()
    years_served_under_countersigning = models.PositiveIntegerField(default=0)
    countersigning_officer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='countersigned_appraisals'
    )
    countersigning_grade = models.CharField(max_length=100, blank=True)
    countersigning_name = models.CharField(max_length=200, blank=True)
    is_draft = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Part 4 — {self.appraisal}"


class AppraisalAspectRating(models.Model):
    """
    Stores each individual aspect rating for Part 2.

    One row per aspect per appraisal.
    Example:
        part_two=<PartTwo for Musa 2024>
        aspect=<Foresight>
        rating='A'

    This replaces the 16 hardcoded fields that were
    previously on PartTwo directly.
    """

    RATING_CHOICES = [
        ('A', 'A - Outstanding'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E - Unsatisfactory'),
        ('NA', 'Not Applicable'),
    ]

    part_two = models.ForeignKey(
        PartTwo,
        on_delete=models.CASCADE,
        related_name='aspect_ratings'
    )
    aspect = models.ForeignKey(
        PerformanceAspect,
        on_delete=models.PROTECT
    )
    rating = models.CharField(
        max_length=2,
        choices=RATING_CHOICES,
        default='C'
    )
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ['part_two', 'aspect']

    def __str__(self):
        return f"{self.aspect.label}: {self.rating}"