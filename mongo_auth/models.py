import hashlib, urllib

from django.conf import settings
from django.contrib.auth import hashers, models as auth_models
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core import mail
from django.test import client
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import mongoengine
from mongoengine.django import auth

from . import utils

USERNAME_REGEX = r'[\w.@+-]+'
CONFIRMATION_TOKEN_VALIDITY = 5 # days
DEFAULT_USER_IMAGE = 'mongo_auth/images/unknown.png'

# Used to reconstruct absolute/full URLs where request is not available
DEFAULT_REQUEST = {
    'SERVER_NAME': '127.0.0.1',
    'SERVER_PORT': '8000',
}

class EmailConfirmationToken(mongoengine.EmbeddedDocument):
    value = mongoengine.StringField(max_length=20, required=True)
    created_time = mongoengine.DateTimeField(default=lambda: timezone.now(), required=True)

    def check_token(self, confirmation_token):
        if confirmation_token != self.value:
            return False
        elif (timezone.now() - self.created_time).days > CONFIRMATION_TOKEN_VALIDITY:
            return False
        else:
            return True

class TwitterAccessToken(mongoengine.EmbeddedDocument):
    key = mongoengine.StringField(max_length=150)
    secret = mongoengine.StringField(max_length=150)

class User(auth.User):
    username = mongoengine.StringField(
        max_length=30,
        min_length=4,
        regex=r'^' + USERNAME_REGEX + r'$',
        required=True,
        verbose_name=_("username"),
        help_text=_("Minimal of 4 characters and maximum of 30. Letters, digits and @/./+/-/_ only."),
    )
    lazyuser_username = mongoengine.BooleanField(default=True)

    facebook_access_token = mongoengine.StringField(max_length=255)
    facebook_profile_data = mongoengine.DictField()

    twitter_access_token = mongoengine.EmbeddedDocumentField(TwitterAccessToken)
    twitter_profile_data = mongoengine.DictField()

    google_access_token = mongoengine.StringField(max_length=150)
    google_profile_data = mongoengine.DictField()

    foursquare_access_token = mongoengine.StringField(max_length=150)
    foursquare_profile_data = mongoengine.DictField()

    browserid_profile_data = mongoengine.DictField()

    email_confirmed = mongoengine.BooleanField(default=False)
    email_confirmation_token = mongoengine.EmbeddedDocumentField(EmailConfirmationToken)

    @classmethod
    def get_initial_fields(cls, request):
        return {}

    def is_anonymous(self):
        return not self.is_authenticated()

    def is_authenticated(self):
        # TODO: Check if *_data fields are really false if not linked with third-party authentication
        return self.has_usable_password() or \
            self.facebook_profile_data or \
            self.twitter_profile_data or \
            self.google_profile_data or \
            self.foursquare_profile_data or \
            self.browserid_profile_data

    def check_password(self, raw_password):
        def setter(raw_password):
            self.set_password(raw_password)
        return hashers.check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        self.password = hashers.make_password(None)
        self.save()
        return self

    def has_usable_password(self):
        return hashers.is_password_usable(self.password)

    def email_user(self, subject, message, from_email=None, allow_unconfirmed=False):
        if not self.email:
            raise ValueError("Account e-mail address not set.")
        if not allow_unconfirmed and not self.email_confirmed:
            raise ValueError("Account e-mail address not confirmed.")
        mail.send_mail(subject, message, from_email, [self.email])

    def get_image_url(self):
        if self.twitter_profile_data and 'profile_image_url' in self.twitter_profile_data:
            return self.twitter_profile_data['profile_image_url']

        elif self.facebook_profile_data:
            # TODO: Do we really need this utils/graph_api_url?
            return '%s?type=square' % utils.graph_api_url('%s/picture' % self.username)

        elif self.foursquare_profile_data and 'photo' in self.foursquare_profile_data:
            return self.foursquare_profile_data['photo']

        elif self.google_profile_data and 'picture' in self.google_profile_data:
            return self.google_profile_data['picture']

        elif self.email:
            request = client.RequestFactory(**getattr(settings, 'DEFAULT_REQUEST', DEFAULT_REQUEST)).request()
            default_url = request.build_absolute_uri(staticfiles_storage.url(getattr(settings, 'DEFAULT_USER_IMAGE', DEFAULT_USER_IMAGE)))

            return 'https://secure.gravatar.com/avatar/%(email_hash)s?%(args)s' % {
                'email_hash': hashlib.md5(self.email.lower()).hexdigest(),
                'args': urllib.urlencode({
                    'default': default_url,
                    'size': 50,
                }),
            }

        else:
            return staticfiles_storage.url(getattr(settings, 'DEFAULT_USER_IMAGE', DEFAULT_USER_IMAGE))

    @classmethod
    def create_user(cls, username, email=None, password=None, lazyuser=False):
        now = timezone.now()
        if not username:
            raise ValueError("The given username must be set")
        email = auth_models.UserManager.normalize_email(email)
        user = cls(
            username=username,
            lazyuser_username=lazyuser,
            email=email or None,
            is_staff=False,
            is_active=True,
            is_superuser=False,
            last_login=now,
            date_joined=now,
        )
        user.set_password(password)
        user.save()
        return user

    def authenticate_facebook(self, request):
        if self.lazyuser_username and self.facebook_profile_data.get('username'):
            # TODO: Does Facebook have same restrictions on username content as we do?
            self.username = self.facebook_profile_data.get('username')
            self.lazyuser_username = False
        if self.first_name is None:
            self.first_name = self.facebook_profile_data.get('first_name') or None
        if self.last_name is None:
            self.last_name = self.facebook_profile_data.get('last_name') or None
        if self.email is None:
            # TODO: Do we know if all e-mail addresses given by Facebook are verified?
            # TODO: Does not Facebook support multiple e-mail addresses? Which one is given here?
            self.email = self.facebook_profile_data.get('email') or None

    def authenticate_twitter(self, request):
        if self.lazyuser_username and self.twitter_profile_data.get('screen_name'):
            # TODO: Does Twitter have same restrictions on username content as we do?
            self.username = self.twitter_profile_data.get('screen_name')
            self.lazyuser_username = False
        if self.first_name is None:
            self.first_name = self.twitter_profile_data.get('name') or None

    def authenticate_google(self, request):
        username_guess = self.google_profile_data.get('email', '').rsplit('@', 1)[0]

        if self.lazyuser_username and username_guess:
            # Best username guess we can get from Google OAuth
            self.username = username_guess
            self.lazyuser_username = False
        if self.first_name is None:
            self.first_name = self.google_profile_data.get('given_name') or None
        if self.last_name is None:
            self.last_name = self.google_profile_data.get('family_name') or None
        if self.email is None:
            self.email = self.google_profile_data.get('email') or None
            if self.google_profile_data.get('verified_email'):
                self.email_confirmed = True

    def authenticate_foursquare(self, request):
        username_guess = self.foursquare_profile_data.get('contact', {}).get('email', '').rsplit('@', 1)[0]

        if self.lazyuser_username and username_guess:
            # Best username guess we can get from Foursquare
            self.username = username_guess
            self.lazyuser_username = False
        if self.first_name is None:
            self.first_name = self.foursquare_profile_data.get('firstName') or None
        if self.last_name is None:
            self.last_name = self.foursquare_profile_data.get('lastName') or None
        if self.email is None:
            self.email = self.foursquare_profile_data.get('contact', {}).get('email') or None

    def authenticate_browserid(self, request):
        if self.lazyuser_username:
            # Best username guess we can get from BrowserID
            self.username = self.browserid_profile_data['email'].rsplit('@', 1)[0]
            self.lazyuser_username = False
        if self.email is None:
            self.email = self.browserid_profile_data['email'] or None
            # BrowserID takes care of email confirmation
            self.email_confirmed = True

    def authenticate_lazyuser(self, request):
        pass
