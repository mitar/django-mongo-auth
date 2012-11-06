import sys

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import forms as auth_forms, hashers, tokens
from django.contrib.sites import models as sites_models
from django.template import loader
from django.utils import http
from django.utils.translation import ugettext_lazy as _

import bson

from . import backends, models

class UserUsernameForm(forms.Form):
    """
    Class with username form.
    """

    username = forms.RegexField(
        label=_("Username"),
        max_length=30,
        min_length=4,
        regex=r'^' + models.USERNAME_REGEX + r'$',
        help_text=_("Minimal of 4 characters and maximum of 30. Letters, digits and @/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters."),
        }
    )

    def clean_username(self):
        """
        This method checks whether the username exists in a case-insensitive manner.
        """

        username = self.cleaned_data['username']
        if backends.User.objects(username__iexact=username).count():
            raise forms.ValidationError(_("A user with that username already exists."), code='username_exists')
        return username

class UserPasswordForm(forms.Form):
    """
    Class with user password form.
    """

    password1 = forms.CharField(
        label=_("Password"),
        min_length=6,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_("Password (repeat)"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."),
    )

    def clean_password2(self):
        """
        This method checks whether the passwords match.
        """

        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password1 != password2:
            raise forms.ValidationError(_("The two password fields did not match."), code='password_mismatch')
        return password2

class UserCurrentPasswordForm(forms.Form):
    """
    Class with user current password form.
    """

    current_password = forms.CharField(
        label=_("Current password"),
        widget=forms.PasswordInput,
        help_text=_("Enter your current password, for verification."),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserCurrentPasswordForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        """
        This method checks if user password is correct.
        """

        password = self.cleaned_data['current_password']
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Your current password was incorrect."), code='password_incorrect')
        return password

class UserBasicInfoForm(forms.Form):
    """
    Class with user basic information form.
    """

    first_name = forms.CharField(label=_("First name"))
    last_name = forms.CharField(label=_("Last name"))
    email = forms.EmailField(label=_("E-mail"))

class RegistrationForm(UserUsernameForm, UserPasswordForm, UserBasicInfoForm):
    """
    Class with registration form.
    """

class AccountChangeForm(UserBasicInfoForm, UserCurrentPasswordForm):
    """
    Class with form for changing your account settings.
    """

class PasswordChangeForm(UserCurrentPasswordForm, UserPasswordForm):
    """
    Class with form for changing password.
    """

class EmailConfirmationSendTokenForm(forms.Form):
    """
    Form for sending an e-mail address confirmation token.
    """

class EmailConfirmationProcessTokenForm(forms.Form):
    """
    Form for processing an e-mail address confirmation token.
    """

    confirmation_token = forms.CharField(
        label=_("Confirmation token"),
        min_length=20,
        max_length=20,
        required=True,
        help_text=_("Please enter the confirmation token you received to your e-mail address."),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(EmailConfirmationProcessTokenForm, self).__init__(*args, **kwargs)

    def clean_confirmation_token(self):
        """
        This method checks if user confirmation token is correct.
        """

        confirmation_token = self.cleaned_data['confirmation_token']
        if not self.user.email_confirmation_token.check_token(confirmation_token):
            raise forms.ValidationError(_("The confirmation token is invalid or has expired. Please retry."), code='confirmation_token_incorrect')
        return confirmation_token

def objectid_to_base36(i):
    assert isinstance(i, bson.ObjectId), type(i)
    old_maxint = sys.maxint
    sys.maxint = old_maxint**2
    try:
        return http.int_to_base36(int(str(i), 16))
    finally:
        sys.maxint = old_maxint

class PasswordResetForm(auth_forms.PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        self.users_cache = backends.User.objects.filter(email__iexact=email, is_active=True)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        # We use "all" instead of "any" and skip all users with unusable passwords in save
        if all((user.password == hashers.UNUSABLE_PASSWORD) for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email

    def save(self, domain_override=None, subject_template_name='mongo_auth/password_reset_subject.txt', email_template_name='mongo_auth/password_reset_email.html', use_https=False, token_generator=tokens.default_token_generator, from_email=None, request=None):
        for user in self.users_cache:
            if user.password == hashers.UNUSABLE_PASSWORD:
                continue
            if not domain_override:
                current_site = sites_models.get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'PASSWORD_RESET_TIMEOUT_DAYS': settings.PASSWORD_RESET_TIMEOUT_DAYS,
                'EMAIL_SUBJECT_PREFIX': settings.EMAIL_SUBJECT_PREFIX,
                'SITE_NAME': getattr(settings, 'SITE_NAME', None),
                'email': user.email,
                'email_address': user.email,
                'request': request,
                'domain': domain,
                'site_name': site_name,
                'uid': objectid_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            user.email_user(subject, email, from_email)
        messages.success(request, _("We've e-mailed you instructions for setting your password to the e-mail address you submitted. You should be receiving it shortly."))
