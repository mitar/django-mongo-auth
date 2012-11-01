import datetime

from django.utils import timezone, translation

from missing import timezone as timezone_missing

from . import fields
from .. import models

LOWER_DATE_LIMIT = 366 * 120 # days

def upper_birthdate_limit():
    return timezone_missing.to_date(timezone.now())

def lower_birthdate_limit():
    return timezone_missing.to_date(timezone.now() - datetime.timedelta(days=LOWER_DATE_LIMIT))

class User(models.User):
    birthdate = fields.LimitedDateTimeField(upper_limit=upper_birthdate_limit, lower_limit=lower_birthdate_limit)
    gender = fields.GenderField()
    language = fields.LanguageField()

    def authenticate_facebook(self, request):
        super(User, self).authenticate_facebook(request)

        if self.gender is None:
            self.gender = self.facebook_profile_data.get('gender') or None

    def authenticate_google(self, request):
        super(User, self).authenticate_google(request)

        if self.gender is None and self.google_profile_data.get('gender') != 'other':
            # TODO: Does it really map so cleanly?
            self.gender = self.google_profile_data.get('gender') or None

    def authenticate_foursquare(self, request):
        super(User, self).authenticate_foursquare(request)

        if self.gender is None:
            # TODO: Does it really map so cleanly?
            self.gender = self.foursquare_profile_data.get('gender') or None

    def authenticate_lazyuser(self, request):
        super(User, self).authenticate_lazyuser(request)

        self.language = translation.get_language_from_request(request)
