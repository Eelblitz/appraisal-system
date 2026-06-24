from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from .models import Organisation


class OrganisationForm(forms.ModelForm):
    """
    Used by Platform Super Admin to create and edit organisations.
    Notice subscription_percentage is included here —
    only platform admins use this form.
    """

    class Meta:
        model = Organisation
        fields = [
            'name',
            'acronym',
            'email',
            'phone',
            'address',
            'logo',
            'subscription_percentage',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('acronym', css_class='col-md-4'),
            ),
            Row(
                Column('email', css_class='col-md-6'),
                Column('phone', css_class='col-md-6'),
            ),
            'address',
            Row(
                Column('logo', css_class='col-md-6'),
                Column('subscription_percentage', css_class='col-md-6'),
            ),
            'is_active',
        )


class OrganisationSettingsForm(forms.ModelForm):
    """
    Used by Organisation Super Admin to update their own details.
    Notice subscription_percentage is NOT included —
    organisations cannot change their own percentage.
    """

    class Meta:
        model = Organisation
        fields = [
            'email',
            'phone',
            'address',
            'logo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('email', css_class='col-md-6'),
                Column('phone', css_class='col-md-6'),
            ),
            'address',
            'logo',
        )


class OrgAdminCreationForm(forms.ModelForm):
    """
    Platform Super Admin uses this to create the first
    HR Admin account for a newly onboarded organisation.

    Why a separate form?
    When creating an org admin, we always set role='hr_admin'
    automatically. We do not give the platform admin a choice
    of role here — that would be a security risk.
    """
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('username', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
        )

    def clean_password2(self):
        """
        Validates that both passwords match.
        Django calls clean_<fieldname> automatically
        during form validation.
        """
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def save(self, commit=True):
        """
        Override save to hash the password properly.
        NEVER store plain text passwords.
        set_password() hashes it using Django's algorithm.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user