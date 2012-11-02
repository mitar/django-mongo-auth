import json, urllib

from django.conf import settings
from django.core import exceptions
from django.utils import crypto, importlib

from mongoengine import queryset
from mongoengine.django import auth

import tweepy

from django_browserid import auth as browserid_auth, base as browserid_base

from . import models

LAZYUSER_USERNAME_TEMPLATE = 'guest-%s'
USER_CLASS = 'mongo_auth.models.User'

def get_class(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = importlib.import_module(module)
    except ImportError, e:
        raise exceptions.ImproperlyConfigured('Error importing user class module %s: "%s"' % (path, e))
    except ValueError, e:
        raise exceptions.ImproperlyConfigured('Error importing user class module. Is USER_CLASS a correctly defined class path?')
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise exceptions.ImproperlyConfigured('Module "%s" does not define user class "%s"' % (module, attr))

    return cls

User = get_class(getattr(settings, 'USER_CLASS', USER_CLASS))

class MongoEngineBackend(auth.MongoEngineBackend):
    # TODO: Implement object permission support
    supports_object_permissions = False
    # TODO: Implement anonymous user backend
    supports_anonymous_user = False
    # TODO: Implement inactive user backend
    supports_inactive_user = False

    def authenticate(self, username, password):
        user = self.user_class.objects(username__iexact=username).first()
        if user:
            if password and user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        try:
            return self.user_class.objects.with_id(user_id)
        except self.user_class.DoesNotExist:
            return None

    @property
    def user_class(self):
        return User

class FacebookBackend(MongoEngineBackend):
    """
    Facebook authentication.
    
    Facebook uses strings 'male' and 'female' for representing user gender.
    """

    # TODO: List all profile data fields we (can) get

    def authenticate(self, facebook_access_token, request):
        # Retrieve user's profile information
        # TODO: Handle error, what if request was denied?
        facebook_profile_data = json.load(urllib.urlopen('https://graph.facebook.com/me?%s' % urllib.urlencode({'access_token': facebook_access_token})))

        try:
            user = self.user_class.objects.get(facebook_profile_data__id=facebook_profile_data.get('id'))
        except self.user_class.DoesNotExist:
            # TODO: Based on user preference, we might create a new user here, not just link with existing, if existing user is lazy user
            # We reload to make sure user object is recent
            request.user.reload()
            user = request.user
            # TODO: Is it OK to override Facebook link if it already exist with some other Facebook user?

        user.facebook_access_token = facebook_access_token
        user.facebook_profile_data = facebook_profile_data

        user.authenticate_facebook(request)
        user.save()

        return user

class TwitterBackend(MongoEngineBackend):
    """
    Twitter authentication.

    Twitter profile data fields are:
        name: user's full name
        screen_name: user's username
        profile_image_url
        profile_background_image_url
        id: id of Twitter user
        id_str: string id of Twitter user
        created_at: full date of user's registration on Twitter
        location: user's location
        time_zone
        lang: user's preferred language
        url: URL of user's website
        description: user's description of themselves
        profile_sidebar_fill_color
        profile_text_color
        profile_background_color
        profile_link_color
        profile_sidebar_border_color
        friends_count
        followers_count
        statuses_count
        favourites_count
        listed_count
        notifications: boolean value
        geo_enabled: boolean value
        following: boolean value
        follow_request_sent: boolean value
        profile_use_background_image: boolean value
        verified: boolean value; tells whether user's email is verified
        protected: boolean value
        show_all_inline_media: boolean value
        is_translator: boolean value
        profile_background_tile: boolean value
        contributors_enabled: boolean value
        utc_offset: integer
    """

    def authenticate(self, twitter_access_token, request):
        TWITTER_CONSUMER_KEY = getattr(settings, 'TWITTER_CONSUMER_KEY', None)
        TWITTER_CONSUMER_SECRET = getattr(settings, 'TWITTER_CONSUMER_SECRET', None)

        if not TWITTER_CONSUMER_KEY or not TWITTER_CONSUMER_SECRET:
            return None

        twitter_auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        twitter_auth.set_access_token(twitter_access_token.key, twitter_access_token.secret)
        twitter_api = tweepy.API(twitter_auth)

        twitter_profile_data = twitter_api.me()

        if 'id' not in twitter_profile_data:
            return None

        try:
            user = self.user_class.objects.get(twitter_profile_data__id=twitter_profile_data['id'])
        except self.user_class.DoesNotExist:
            # TODO: Based on user preference, we might create a new user here, not just link with existing, if existing user is lazy user
            # We reload to make sure user object is recent
            request.user.reload()
            user = request.user
            # TODO: Is it OK to override Twitter link if it already exist with some other Twitter user?

        user.twitter_access_token = models.TwitterAccessToken(key=twitter_access_token.key, secret=twitter_access_token.secret)
        user.twitter_profile_data = twitter_profile_data

        user.authenticate_twitter(request)
        user.save()

        return user

class GoogleBackend(MongoEngineBackend):
    """
    Google authentication.

    Google profile data fields are:
        family_name: last name
        given_name: first name
        name: full name
        link: URL of Google user profile page
        picture: URL of profile picture
        locale: the language Google user is using
        gender: the gender of Google user (other|female|male)
        timezone: the default timezone of Google user
        email: Google email of user
        id: id of Google user; should be a string
        verified_email: True, if email is verified by Google API
    """

    def authenticate(self, google_access_token, request):
        # Retrieve user's profile information
        # TODO: Handle error, what if request was denied?
        google_profile_data = json.load(urllib.urlopen('https://www.googleapis.com/oauth2/v1/userinfo?access_token=%s' % google_access_token))

        if 'id' not in google_profile_data:
            return None

        try:
            user = self.user_class.objects.get(google_profile_data__id=google_profile_data['id'])
        except self.user_class.DoesNotExist:
            # TODO: Based on user preference, we might create a new user here, not just link with existing, if existing user is lazy user
            # We reload to make sure user object is recent
            request.user.reload()
            user = request.user
            # TODO: Is it OK to override Google link if it already exist with some other Google user?

        user.google_access_token = google_access_token
        user.google_profile_data = google_profile_data

        user.authenticate_google(request)
        user.save()

        return user

class FoursquareBackend(MongoEngineBackend):
    """
    Foursquare authentication.

    Foursquare profile data fields are:
        id: a unique identifier for this user.
        firstName: user's first name
        lastName: user's last name
        homeCity: user's home city
        photo: URL of a profile picture for this user
        gender: user's gender: male, female, or none
        relationship: the relationship of the acting user (me) to this user (them) (optional)
        type: one of page, celebrity, or user
        contact: an object containing none, some, or all of twitter, facebook, email, and phone
        pings: pings from this user (optional)
        badges: contains the count of badges for this user, may eventually contain some selected badges
        checkins: contains the count of checkins by this user, may contain the most recent checkin as an array
        mayorships: contains the count of mayorships for this user and an items array that for now is empty
        tips: contains the count of tips from this user, may contain an array of selected tips as items
        todos: contains the count of todos this user has, may contain an array of selected todos as items
        photos: contains the count of photos this user has, may contain an array of selected photos as items
        friends: contains count of friends for this user and groups of users who are friends
        followers: contains count of followers for this user, if they are a page or celebrity
        requests: contains count of pending friend requests for this user
        pageInfo: contains a detailed page, if they are a page
    """

    def authenticate(self, foursquare_access_token, request):
        # Retrieve user's profile information
        # TODO: Handle error, what if request was denied?
        foursquare_profile_data = json.load(urllib.urlopen('https://api.foursquare.com/v2/users/self?%s' % urllib.urlencode({'oauth_token': foursquare_access_token})))['response']['user']

        if 'id' not in foursquare_profile_data:
            return None

        try:
            user = self.user_class.objects.get(foursquare_profile_data__id=foursquare_profile_data['id'])
        except self.user_class.DoesNotExist:
            # TODO: Based on user preference, we might create a new user here, not just link with existing, if existing user is lazy user
            # We reload to make sure user object is recent
            request.user.reload()
            user =  request.user
            # TODO: Is it OK to override Foursquare link if it already exist with some other Foursquare user?

        user.foursquare_access_token = foursquare_access_token
        user.foursquare_profile_data = foursquare_profile_data

        user.authenticate_foursquare(request)
        user.save()

        return user

class BrowserIDBackend(MongoEngineBackend, browserid_auth.BrowserIDBackend):
    """
    Persona authentication.

    Persona profile data fields are:
        email: email user uses for Persona
    """
    
    def authenticate(self, browserid_assertion=None, browserid_audience=None, request=None):
        browserid_profile_data = browserid_base.verify(browserid_assertion, browserid_audience)
        if not browserid_profile_data or 'email' not in browserid_profile_data:
            return None

        try:
            user = self.user_class.objects.get(browserid_profile_data__email=browserid_profile_data['email'])
            # TODO: What is we get more than one user?
        except self.user_class.DoesNotExist:
            # TODO: Based on user preference, we might create a new user here, not just link with existing, if existing user is lazy user
            # We reload to make sure user object is recent
            request.user.reload()
            user = request.user
            # TODO: Is it OK to override BrowserID link if it already exist with some other BrowserID user?
        
        user.browserid_profile_data = browserid_profile_data

        user.authenticate_browserid(request)
        user.save()

        return user

class LazyUserBackend(MongoEngineBackend):
    def authenticate(self, request):
        while True:
            try:
                username = LAZYUSER_USERNAME_TEMPLATE % crypto.get_random_string(6)
                user = self.user_class.create_user(username=username, lazyuser=True)

                user.authenticate_lazyuser(request)
                user.save()

                break
            except queryset.OperationError, e:
                msg = str(e)
                if 'E11000' in msg and 'duplicate key error' in msg and 'username' in msg:
                    continue
                raise

        return user
