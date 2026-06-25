from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, HTML
from .models import PartOne, PartTwo, PartThree, PartFour, AppraisalAspectRating


class PartOneForm(forms.ModelForm):
    """
    Part 1 of the Annual Performance Evaluation.
    Filled by the employee themselves.
    Fields 4-11b only. Fields 1-3 come from UserProfile.
    """

    class Meta:
        model = PartOne
        fields = [
            'qualification',
            'date_of_first_appointment',
            'present_substantive_grade',
            'date_appointed_to_grade',
            'acting_appointment',
            'courses_undertaken',
            'days_absent_sick',
            'present_job',
            'job_description',
            'main_duty_1',
            'main_duty_2',
            'main_duty_3',
            'main_duty_4',
            'main_duty_5',
            'adhoc_duties',
        ]
        widgets = {
            'date_of_first_appointment': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'date_appointed_to_grade': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'qualification': forms.Textarea(attrs={'rows': 3}),
            'acting_appointment': forms.Textarea(attrs={'rows': 3}),
            'courses_undertaken': forms.Textarea(attrs={'rows': 3}),
            'job_description': forms.Textarea(attrs={'rows': 3}),
            'main_duty_1': forms.Textarea(attrs={'rows': 2}),
            'main_duty_2': forms.Textarea(attrs={'rows': 2}),
            'main_duty_3': forms.Textarea(attrs={'rows': 2}),
            'main_duty_4': forms.Textarea(attrs={'rows': 2}),
            'main_duty_5': forms.Textarea(attrs={'rows': 2}),
            'adhoc_duties': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'qualification': '4. Qualification held (Degree, Diploma, Certificate, etc.)',
            'date_of_first_appointment': '5. Date of first appointment in the service',
            'present_substantive_grade': '6. Present Substantive Grade',
            'date_appointed_to_grade': '7. Date appointed to Substantive Grade',
            'acting_appointment': '8. Acting appointment held during period of report',
            'courses_undertaken': '9. Courses undertaken during period of report',
            'days_absent_sick': '10. Total number of days absent on sick leave',
            'present_job': '11. Present Job',
            'job_description': 'Job Description',
            'main_duty_1': 'Main Duty 1 (Most Important)',
            'main_duty_2': 'Main Duty 2',
            'main_duty_3': 'Main Duty 3',
            'main_duty_4': 'Main Duty 4',
            'main_duty_5': 'Main Duty 5',
            'adhoc_duties': '11(b). Adhoc duties performed (not of a continuous nature)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        if getattr(self, 'is_submitting', False):
            required_fields = [
                'qualification',
                'date_of_first_appointment',
                'present_substantive_grade',
                'date_appointed_to_grade',
                'present_job',
                'job_description',
                'main_duty_1',
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(
                        field,
                        'This field is required before submitting.'
                    )
        return cleaned_data


class PartTwoForm(forms.ModelForm):
    """
    Part 2 of the GEN 79 form.
    Filled by the Reporting Officer.

    This form handles fields 12, 13, overall rating
    and signature details.

    The 16 aspect ratings (field 14) are NOT handled
    by this ModelForm. Instead they are handled separately
    as a formset-like structure in the view and template.

    Why separately?
    Each aspect needs its own A-E radio button row.
    The number of aspects varies per template.
    A standard ModelForm cannot handle dynamic fields.
    We build the aspect ratings manually in the view.
    """

    class Meta:
        model = PartTwo
        fields = [
            'agrees_with_job_description',
            'job_description_disagreement',
            'performance_assessment',
            'overall_rating',
            'reporting_officer_grade',
            'reporting_officer_job_title',
            'years_known',
        ]
        widgets = {
            'job_description_disagreement': forms.Textarea(
                attrs={'rows': 3}
            ),
            'performance_assessment': forms.Textarea(
                attrs={'rows': 4}
            ),
        }
        labels = {
            'agrees_with_job_description': (
                '12. Do you and the person reported upon agree on '
                'the job description and order of importance?'
            ),
            'job_description_disagreement': (
                'If NO, record any unresolved differences here'
            ),
            'performance_assessment': (
                '13. Assessment of Performance — How effective is '
                'he/she in the performance of the duties set out '
                'in 11(a)?'
            ),
            'overall_rating': 'Overall Performance Rating',
            'reporting_officer_grade': 'Your Grade Level',
            'reporting_officer_job_title': 'Your Job Title',
            'years_known': 'He/She has served under me for (years)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        # Make all fields optional for draft saving
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        """
        Full validation on final submission only.
        is_submitting is set by the view before calling is_valid().
        """
        cleaned_data = super().clean()

        if getattr(self, 'is_submitting', False):
            required_on_submit = [
                'performance_assessment',
                'overall_rating',
                'reporting_officer_grade',
                'reporting_officer_job_title',
            ]
            for field in required_on_submit:
                if not cleaned_data.get(field):
                    self.add_error(
                        field,
                        'This field is required before submitting.'
                    )

        return cleaned_data


class PartThreeForm(forms.ModelForm):
    """
    Part 3 of the Annual Performance Evaluation form.
    Also filled by the Reporting Officer.
    Fields 15-19: Training needs, next job, promotability.
    """

    class Meta:
        model = PartThree
        fields = [
            'training_needs',
            'training_how_met',
            'different_job_same_grade',
            'transfer_to_another_cadre',
            'next_job_reasons',
            'promotion_fitness',
            'promotion_to_grade',
            'promotion_comment',
            'special_promotion_grade',
            'special_promotion_reasons',
            'long_term_potential',
            'general_remarks',
            'years_served_under_reporting_officer',
            'reporting_officer_grade',
            'reporting_officer_name',
        ]
        widgets = {
            'training_needs': forms.Textarea(attrs={'rows': 3}),
            'training_how_met': forms.Textarea(attrs={'rows': 3}),
            'next_job_reasons': forms.Textarea(attrs={'rows': 3}),
            'promotion_comment': forms.Textarea(attrs={'rows': 3}),
            'special_promotion_reasons': forms.Textarea(attrs={'rows': 3}),
            'general_remarks': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'training_needs': (
                '15(a). If performance could be improved by training, '
                'specify the needs'
            ),
            'training_how_met': (
                '15(b). If they cannot be met on the job, suggest '
                'how they might be met'
            ),
            'different_job_same_grade': (
                '16(a). Should be considered for a different job '
                'in the same grade'
            ),
            'transfer_to_another_cadre': (
                '16(b). Transfer to a job at similar level in '
                'another occupational group or cadre'
            ),
            'next_job_reasons': (
                'If YES to either above, say which kind of job '
                'and give your reasons'
            ),
            'promotion_fitness': '17(a). Normal Promotion — He/She is at present',
            'promotion_to_grade': 'For promotion to Grade',
            'promotion_comment': 'Comment on your recommendation',
            'special_promotion_grade': (
                '17(b). Special promotion — should be specially '
                'considered for promotion to Grade'
            ),
            'special_promotion_reasons': (
                'Give the reasons for your recommendation'
            ),
            'long_term_potential': '18. Long term potential',
            'general_remarks': (
                '19. General Remarks — Any additional relevant '
                'information, strengths or weaknesses'
            ),
            'years_served_under_reporting_officer': (
                'He/She has served under me for (years)'
            ),
            'reporting_officer_grade': 'Your Grade Level',
            'reporting_officer_name': 'Your Name (Block Letters)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        if getattr(self, 'is_submitting', False):
            required_on_submit = [
                'promotion_fitness',
                'long_term_potential',
                'reporting_officer_grade',
                'reporting_officer_name',
            ]
            for field in required_on_submit:
                if not cleaned_data.get(field):
                    self.add_error(
                        field,
                        'This field is required before submitting.'
                    )
        return cleaned_data


class PartFourForm(forms.ModelForm):
    """
    Part 4 of the Annual Performance Evaluation form.
    Filled by the Countersigning Officer.
    Field 20: Final report and countersignature.
    """

    class Meta:
        model = PartFour
        fields = [
            'countersigning_report',
            'years_served_under_countersigning',
            'countersigning_grade',
            'countersigning_name',
        ]
        widgets = {
            'countersigning_report': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'countersigning_report': (
                '20. Countersigning Officer\'s Report — Confirm '
                'agreement or indicate disagreements with the '
                'Reporting Officer\'s assessment'
            ),
            'years_served_under_countersigning': (
                'He/She has served under me for (years)'
            ),
            'countersigning_grade': 'Your Grade Level',
            'countersigning_name': 'Your Name (Block Letters)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        if getattr(self, 'is_submitting', False):
            required_on_submit = [
                'countersigning_report',
                'countersigning_grade',
                'countersigning_name',
            ]
            for field in required_on_submit:
                if not cleaned_data.get(field):
                    self.add_error(
                        field,
                        'This field is required before submitting.'
                    )
        return cleaned_data