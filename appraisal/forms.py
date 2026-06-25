from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, HTML
from .models import PartOne, PartTwo, PartThree, PartFour


class PartOneForm(forms.ModelForm):
    """
    Part 1 of the GEN 79 Annual Performance Evaluation.
    Filled by the employee themselves.

    Fields 1-3 (name, DOB, dept) come from UserProfile.
    This form only handles fields 4-11b.

    Two submit buttons:
    - "Save Draft" → saves without changing appraisal status
    - "Submit Part 1" → saves and locks the form permanently
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

        # Make all fields optional for draft saving
        # Validation only runs on final submission
        # This is handled in the view, not the form
        for field in self.fields:
            self.fields[field].required = False

        self.helper.layout = Layout(

            # Field 4
            Fieldset(
                '',
                'qualification',
            ),

            # Fields 5-7
            Fieldset(
                '',
                Row(
                    Column(
                        'date_of_first_appointment',
                        css_class='col-md-4'
                    ),
                    Column(
                        'present_substantive_grade',
                        css_class='col-md-4'
                    ),
                    Column(
                        'date_appointed_to_grade',
                        css_class='col-md-4'
                    ),
                ),
            ),

            # Field 8
            Fieldset('', 'acting_appointment'),

            # Field 9
            Fieldset('', 'courses_undertaken'),

            # Field 10
            Fieldset(
                '',
                Row(
                    Column('days_absent_sick', css_class='col-md-4'),
                ),
            ),

            # Field 11
            Fieldset(
                '',
                Row(
                    Column('present_job', css_class='col-md-6'),
                ),
                'job_description',
            ),

            # Field 11a
            Fieldset(
                '11(a). State below in order of importance the main duties '
                'performed during the period of report',
                'main_duty_1',
                'main_duty_2',
                'main_duty_3',
                'main_duty_4',
                'main_duty_5',
            ),

            # Field 11b
            Fieldset('', 'adhoc_duties'),
        )

    def clean(self):
        """
        Full validation runs only when employee submits
        (not when saving draft).

        The view passes is_submitting=True when the employee
        clicks the final Submit button.
        We check that flag here to decide whether to enforce
        required field validation.
        """
        cleaned_data = super().clean()

        # is_submitting is set on the form instance by the view
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