from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
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
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'name',
            'description',
            'is_active',
        )


class AppraisalCycleForm(forms.ModelForm):
    """
    Why does this form accept organisation?

    The category dropdown must only show categories belonging
    to the current user's organisation.

    Without passing organisation, the dropdown would show
    ALL categories from ALL organisations — a data leak.

    We pass organisation through kwargs, pop it before
    calling super().__init__() because ModelForm does not
    know what to do with a custom kwarg.
    """

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
        # Pop organisation from kwargs BEFORE calling super()
        # If we don't pop it, super().__init__() will crash
        # because ModelForm doesn't expect 'organisation'
        organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)

        # Filter category dropdown to this organisation only
        if organisation:
            self.fields['category'].queryset = (
                AppraisalCategory.objects.filter(
                    organisation=organisation,
                    is_active=True
                )
            )
        else:
            self.fields['category'].queryset = (
                AppraisalCategory.objects.none()
            )

        self.helper = FormHelper()
        self.helper.form_tag = False
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
        self.helper.form_tag = False
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
    """
    Same pattern as AppraisalCycleForm.
    We pass organisation to filter:
    1. The cycle dropdown — only this org's cycles
    2. The aspects — platform defaults + org custom aspects
    """
    aspects = forms.ModelMultipleChoiceField(
        queryset=PerformanceAspect.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text='Select performance aspects for this template'
    )

    class Meta:
        model = AppraisalTemplate
        fields = ['name', 'cycle', 'aspects', 'is_active']

    def __init__(self, *args, **kwargs):
        # Pop organisation before super().__init__()
        organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)

        if organisation:
            # Cycles dropdown — only this org's non-closed cycles
            self.fields['cycle'].queryset = (
                AppraisalCycle.objects.filter(
                    organisation=organisation
                ).exclude(status='closed')
            )

            # Aspects — platform defaults (org=None) + org custom
            self.fields['aspects'].queryset = (
                PerformanceAspect.objects.filter(
                    Q(organisation=None) |
                    Q(organisation=organisation)
                ).order_by('order')
            )
        else:
            self.fields['cycle'].queryset = AppraisalCycle.objects.none()
            self.fields['aspects'].queryset = PerformanceAspect.objects.none()

        # Pre-select aspects if editing existing template
        if self.instance.pk:
            self.fields['aspects'].initial = self.instance.aspects.all()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('cycle', css_class='col-md-4'),
            ),
            'is_active',
            'aspects',
        )