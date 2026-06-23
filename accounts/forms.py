from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import UserProfile


class LoginForm(AuthenticationForm):
    """
    Extends Django's built-in login form.
    We only add crispy styling — the authentication
    logic is already handled by Django.
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
        self.helper.layout = Layout(
            Field('username', css_class='form-control mb-3'),
            Field('password', css_class='form-control mb-3'),
            Submit('submit', 'Login', css_class='btn btn-primary w-100')
        )


class UserRegistrationForm(forms.ModelForm):
    """
    HR uses this to create new employee accounts.
    Employees do not self-register — HR creates their accounts.
    This keeps the system controlled.
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
            Submit('submit', 'Create Account', css_class='btn btn-primary')
        )

    def clean_password2(self):
        """
        clean_password2 runs automatically when the form is validated.
        Django calls any method named clean_<fieldname> during validation.
        We use it to make sure both passwords match.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def save(self, commit=True):
        """
        Override save() to hash the password properly.
        Never store plain text passwords — set_password() hashes it.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Used when creating or editing a user's profile details.
    Maps to the UserProfile model fields.
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
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_of_first_appointment': forms.DateInput(attrs={'type': 'date'}),
            'date_appointed_to_grade': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
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
            Submit('submit', 'Save Profile', css_class='btn btn-primary mt-3')
        )