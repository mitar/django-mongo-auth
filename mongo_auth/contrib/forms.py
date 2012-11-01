from django import forms
from django.forms.extras import widgets
from django.utils.translation import ugettext_lazy as _

from . import fields, form_fields, models
from .. import forms as base_forms

class UserAdditionalInfoForm(forms.Form):
    """
    Class with user additional information form.
    """

    # TODO: Language field is missing?

    gender = forms.ChoiceField(
        label=_("Gender"),
        choices=fields.GENDER_CHOICES,
        widget=forms.RadioSelect(),
        required=False,
    )
    birthdate = form_fields.LimitedDateTimeField(
        upper_limit=models.upper_birthdate_limit,
        lower_limit=models.lower_birthdate_limit,
        label=_("Birth date"),
        required=False,
        widget=widgets.SelectDateWidget(
            years=[
            y for y in range(
                models.upper_birthdate_limit().year,
                models.lower_birthdate_limit().year,
                -1,
            )
            ],
        ),
    )

class RegistrationForm(base_forms.UserUsernameForm, base_forms.UserPasswordForm, base_forms.UserBasicInfoForm, UserAdditionalInfoForm):
    """
    Class with registration form.
    """

class AccountChangeForm(base_forms.UserBasicInfoForm, UserAdditionalInfoForm, base_forms.UserCurrentPasswordForm):
    """
    Class with form for changing your account settings.
    """
