from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import (
    AppraisalCategory, AppraisalCycle,
    PerformanceAspect, AppraisalTemplate
)


class AppraisalCategoryForm(forms.ModelForm):
    class Meta:
        model = AppraisalCategory
        fields = ['name', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Template handles the <form> tag
        self.helper.layout = Layout(
            'name',
            'description',
            'is_active',
        )


class AppraisalCycleForm(forms.ModelForm):
    class Meta:
        model = AppraisalCycle
        fields = [
            'name', 'category', 'year',
            'period_from', 'period_to',
            'download_fee',
            'part1_deadline', 'part2_deadline',
            'part3_deadline', 'part4_deadline',
        ]
        widgets = {
            'period_from': forms.DateInput(attrs={'type': 'date'}),
            'period_to': forms.DateInput(attrs={'type': 'date'}),
            'part1_deadline': forms.DateInput(attrs={'type': 'date'}),
            'part2_deadline': forms.DateInput(attrs={'type': 'date'}),
            'part3_deadline': forms.DateInput(attrs={'type': 'date'}),
            'part4_deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AppraisalCategory.objects.filter(
            is_active=True
        )
        self.helper = FormHelper()
        self.helper.form_tag = False  # Template handles the <form> tag
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('year', css_class='col-md-4'),
            ),
            Row(
                Column('category', css_class='col-md-6'),
                Column('download_fee', css_class='col-md-6'),
            ),
            Row(
                Column('period_from', css_class='col-md-6'),
                Column('period_to', css_class='col-md-6'),
            ),
            Row(
                Column('part1_deadline', css_class='col-md-3'),
                Column('part2_deadline', css_class='col-md-3'),
                Column('part3_deadline', css_class='col-md-3'),
                Column('part4_deadline', css_class='col-md-3'),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        period_from = cleaned_data.get('period_from')
        period_to = cleaned_data.get('period_to')

        if period_from and period_to:
            if period_from >= period_to:
                raise forms.ValidationError(
                    'Period start date must be before the end date.'
                )
        return cleaned_data


class PerformanceAspectForm(forms.ModelForm):
    class Meta:
        model = PerformanceAspect
        fields = [
            'label',
            'outstanding_description',
            'unsatisfactory_description',
            'is_applicable',
            'order'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Template handles the <form> tag
        self.helper.layout = Layout(
            Row(
                Column('label', css_class='col-md-8'),
                Column('order', css_class='col-md-4'),
            ),
            'outstanding_description',
            'unsatisfactory_description',
            'is_applicable',
        )


class AppraisalTemplateForm(forms.ModelForm):
    aspects = forms.ModelMultipleChoiceField(
        queryset=PerformanceAspect.objects.filter(
            is_applicable=True
        ).order_by('order'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text='Select the performance aspects to include in this template'
    )

    class Meta:
        model = AppraisalTemplate
        fields = ['name', 'cycle', 'aspects', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cycle'].queryset = AppraisalCycle.objects.exclude(
            status='closed'
        )
        if self.instance.pk:
            self.fields['aspects'].initial = self.instance.aspects.all()

        self.helper = FormHelper()
        self.helper.form_tag = False  # Template handles the <form> tag
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('cycle', css_class='col-md-4'),
            ),
            'is_active',
            'aspects',
        )