from django.db import models
from django.contrib.auth.models import User
from hr.models import AppraisalCycle, AppraisalTemplate, PerformanceAspect


class Appraisal(models.Model):
    """
    This is the MASTER record for one employee's appraisal in one cycle.
    Every part (1, 2, 3, 4) links back to this single record.

    Think of it as the 'container' that holds all four parts together.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),           # Created but employee hasn't started
        ('part1_submitted', 'Part 1 Submitted'),  # Employee done
        ('part2_submitted', 'Part 2 Submitted'),  # Reporting officer done
        ('part3_submitted', 'Part 3 Submitted'),  # Part 3 done
        ('completed', 'Completed'),       # Countersigning officer done
        ('closed', 'Closed'),             # Finalized, PDF available
    ]

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

    # Tracks when each part was submitted
    part1_submitted_at = models.DateTimeField(null=True, blank=True)
    part2_submitted_at = models.DateTimeField(null=True, blank=True)
    part3_submitted_at = models.DateTimeField(null=True, blank=True)
    part4_submitted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.cycle.name}"

    class Meta:
        verbose_name = 'Appraisal'
        verbose_name_plural = 'Appraisals'
        # One employee can only have ONE appraisal per cycle
        unique_together = ['employee', 'cycle']
        ordering = ['-created_at']


class PartOne(models.Model):
    """
    PART ONE - Personal Records of Employee
    Filled by the employee themselves.
    Maps directly to fields 1-11 on the GEN 79 form.
    """
    # One PartOne per appraisal — if appraisal deleted, this is deleted too
    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        related_name='part_one'
    )

    # Field 1: Name (first/last name already on User model)
    # Field 2: Date of Birth (already on UserProfile)
    # Field 3: Local Govt, Dept, Section (already on UserProfile)
    # We pull those from UserProfile — no need to duplicate here

    # Field 4
    qualification = models.TextField(
        help_text='Degree, Diploma, Certificate etc. Underline those acquired during report period'
    )

    # Field 5
    date_of_first_appointment = models.DateField()

    # Field 6
    present_substantive_grade = models.CharField(max_length=100)

    # Field 7
    date_appointed_to_grade = models.DateField()

    # Field 8
    acting_appointment = models.TextField(
        blank=True,
        help_text='Acting appointment held during period of report'
    )

    # Field 9
    courses_undertaken = models.TextField(
        blank=True,
        help_text='Courses undertaken during period of report'
    )

    # Field 10
    days_absent_sick = models.PositiveIntegerField(
        default=0,
        help_text='Total number of days absent on sick leave during period of report'
    )

    # Field 11
    present_job = models.CharField(max_length=200)
    job_description = models.TextField()

    # Field 11a - Main duties in order of importance
    main_duty_1 = models.TextField(blank=True, verbose_name='Main Duty 1')
    main_duty_2 = models.TextField(blank=True, verbose_name='Main Duty 2')
    main_duty_3 = models.TextField(blank=True, verbose_name='Main Duty 3')
    main_duty_4 = models.TextField(blank=True, verbose_name='Main Duty 4')
    main_duty_5 = models.TextField(blank=True, verbose_name='Main Duty 5')

    # Field 11b - Adhoc duties
    adhoc_duties = models.TextField(
        blank=True,
        help_text='Any adhoc duties performed which are not of a continuous nature'
    )

    is_draft = models.BooleanField(default=True)  # True = saved but not submitted
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Part 1 - {self.appraisal}"


class PartTwo(models.Model):
    """
    PART TWO - Reporting Officer's Assessment
    Filled by the Reporting Officer.
    Contains fields 12, 13, 14 and the overall rating.
    """
    RATING_CHOICES = [
        ('A', 'A - Outstanding'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E - Unsatisfactory'),
        ('NA', 'Not Applicable'),
    ]

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

    # Field 12 - Agreement on job description
    agrees_with_job_description = models.BooleanField(
        default=True,
        verbose_name='Do you agree with the job description?'
    )
    job_description_disagreement = models.TextField(
        blank=True,
        verbose_name='If NO, state unresolved differences'
    )

    # Field 13 - Assessment of performance narrative
    performance_assessment = models.TextField(
        verbose_name='Assessment of Performance',
        help_text='How effective is he/she in the performance of duties set out in 11(a)?'
    )

    # Field 14 - The 16 rated aspects (A to E)
    # Each aspect gets its own rating field and optional comment
    rating_foresight = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_penetration = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_judgement = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_expression_paper = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_oral_expression = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_numerical_ability = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_relations_colleagues = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_relations_public = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_acceptance_responsibility = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_reliability_pressure = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_drive_determination = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_professional_knowledge = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_management_staff = models.CharField(max_length=2, choices=RATING_CHOICES, default='C', verbose_name='Management of Staff (if applicable)')
    rating_output_of_work = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_quality_of_work = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')
    rating_punctuality = models.CharField(max_length=2, choices=RATING_CHOICES, default='C')

    # Overall performance rating (the diamond boxes 1-5)
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
    reporting_officer_grade = models.CharField(max_length=100)
    reporting_officer_job_title = models.CharField(max_length=200)
    years_known = models.PositiveIntegerField(
        default=0,
        help_text='He has served under me for the past X years'
    )

    is_draft = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Part 2 - {self.appraisal}"


class PartThree(models.Model):
    """
    PART THREE - Training Needs and Promotability
    Also filled by the Reporting Officer (fields 15-19)
    """
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

    # Field 15 - Training needs
    training_needs = models.TextField(
        blank=True,
        verbose_name='Training Needs',
        help_text='If performance could be improved by training, specify the needs'
    )
    training_how_met = models.TextField(
        blank=True,
        verbose_name='How Training Needs Can Be Met',
        help_text='If they cannot be met on the job, suggest how they might be met'
    )

    # Field 16 - Next job
    different_job_same_grade = models.BooleanField(
        default=False,
        verbose_name='Should be considered for a different job in the same grade'
    )
    transfer_to_another_cadre = models.BooleanField(
        default=False,
        verbose_name='Transfer to a job at similar level in another cadre'
    )
    next_job_reasons = models.TextField(
        blank=True,
        verbose_name='Reasons for next job recommendation'
    )

    # Field 17a - Normal promotion
    promotion_fitness = models.CharField(
        max_length=15,
        choices=PROMOTION_FITNESS_CHOICES,
        blank=True
    )
    promotion_to_grade = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Promotion to Grade'
    )
    promotion_comment = models.TextField(
        blank=True,
        verbose_name='Comment on promotion recommendation'
    )

    # Field 17b - Special promotion
    special_promotion_grade = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Special promotion to Grade'
    )
    special_promotion_reasons = models.TextField(
        blank=True,
        verbose_name='Reasons for special promotion recommendation'
    )

    # Field 18 - Long term potential
    long_term_potential = models.CharField(
        max_length=1,
        choices=LONG_TERM_POTENTIAL_CHOICES,
        blank=True
    )

    # Field 19 - General remarks
    general_remarks = models.TextField(
        blank=True,
        verbose_name='General Remarks',
        help_text='Additional relevant information, strengths or weaknesses'
    )
    years_served_under_reporting_officer = models.PositiveIntegerField(default=0)

    # Reporting officer signature
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
        return f"Part 3 - {self.appraisal}"


class PartFour(models.Model):
    """
    PART FOUR - Countersigning Officer's Report
    Field 20 - filled by the Countersigning Officer
    This is the final part before the appraisal is closed
    """
    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        related_name='part_four'
    )

    # Field 20
    countersigning_report = models.TextField(
        verbose_name="Countersigning Officer's Report",
        help_text='Confirm agreement or indicate disagreements with reporting officer assessment'
    )
    years_served_under_countersigning = models.PositiveIntegerField(default=0)

    # Countersigning officer details
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
        return f"Part 4 - {self.appraisal}"


class AppraisalAspectRating(models.Model):
    """
    This stores each individual aspect rating dynamically.
    It works ALONGSIDE the fixed ratings in PartTwo.
    This allows HR to add custom aspects beyond the standard 16.
    """
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
        choices=PartTwo.RATING_CHOICES
    )
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ['part_two', 'aspect']

    def __str__(self):
        return f"{self.aspect.label}: {self.rating}"