from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field
from .models import UserProfile


class LoginForm(AuthenticationForm):
    """
    Extends Django's built-in login form.
    Django handles all the authentication logic.
    We only add crispy styling.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class UserRegistrationForm(forms.ModelForm):
    """
    Creates a new Django User account.
    Used by HR Admin to onboard employees.
    """
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
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
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Creates or updates a UserProfile.

    Why does this form accept organisation?
    The reporting_officer and countersigning_officer dropdowns
    must only show users from the SAME organisation.

    Without passing organisation, the dropdowns would show
    ALL users from ALL organisations — a serious data leak.

    Pattern: pop organisation from kwargs before super().__init__()
    because ModelForm does not know what to do with it.
    Then use it to filter the queryset on those two fields.
    """

    class Meta:
        model = UserProfile
        fields = [
            'role',
            'date_of_birth',
            'local_government',
            'department',
            'section',
            'qualification',
            'date_of_first_appointment',
            'present_substantive_grade',
            'date_appointed_to_grade',
            'phone_number',
            'reporting_officer',
            'countersigning_officer',
            'profile_photo',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'date_of_first_appointment': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'date_appointed_to_grade': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):
        # Pop organisation before calling super().__init__()
        # This is the standard pattern for passing extra
        # context into a Django ModelForm
        organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)

        if organisation:
            # Reporting officer dropdown:
            # Only show users with reporting_officer role
            # in the same organisation
            self.fields['reporting_officer'].queryset = (
                UserProfile.objects.filter(
                    organisation=organisation,
                    role='reporting_officer'
                ).select_related('user')
            )

            # Countersigning officer dropdown:
            # Only show users with countersigning_officer role
            # in the same organisation
            self.fields['countersigning_officer'].queryset = (
                UserProfile.objects.filter(
                    organisation=organisation,
                    role='countersigning_officer'
                ).select_related('user')
            )
        else:
            # If no organisation, show empty dropdowns
            # This prevents accidental data leaks
            self.fields['reporting_officer'].queryset = (
                UserProfile.objects.none()
            )
            self.fields['countersigning_officer'].queryset = (
                UserProfile.objects.none()
            )

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('role', css_class='col-md-6'),
                Column('phone_number', css_class='col-md-6'),
            ),
            Row(
                Column('date_of_birth', css_class='col-md-4'),
                Column('local_government', css_class='col-md-4'),
                Column('department', css_class='col-md-4'),
            ),
            Row(
                Column('section', css_class='col-md-6'),
                Column('present_substantive_grade', css_class='col-md-6'),
            ),
            Row(
                Column('date_of_first_appointment', css_class='col-md-6'),
                Column('date_appointed_to_grade', css_class='col-md-6'),
            ),
            'qualification',
            Row(
                Column('reporting_officer', css_class='col-md-6'),
                Column('countersigning_officer', css_class='col-md-6'),
            ),
            'profile_photo',
        )