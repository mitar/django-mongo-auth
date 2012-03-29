import json, urlparse, urllib

from django.conf import settings
from django.core import urlresolvers

from mongoengine.django import auth as mongo_models

from piplmesh.account import models

class CustomUserModelBackend(mongo_models.MongoEngineBackend):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        user = self.user_class.objects(username__iexact=username).first()
        if user:
            if password and user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        return self.user_class.objects.with_id(user_id)

    @property
    def user_class(self):
        self._user_class = models.CustomUser
        return self._user_class

class FacebookBackend:
    def authenticate(self, token=None, request=None):
        """
        Facebook authentication.

        Retrieves an access token and Facebook data. Determine if user already has a
        profile. If not, a new profile is created using either the user's
        username or Facebook id. Finally, the user's Facebook data is saved.
        """
    
        args = {
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'redirect_uri': request.build_absolute_uri(urlresolvers.reverse('facebook_callback')),
            'code': token,
        }
    
        # Retrieve access token
        url = urllib.urlopen('https://graph.facebook.com/oauth/access_token?%s' % urllib.urlencode(args)).read()
        response = urlparse.parse_qs(url)
        access_token = response['access_token'][-1]
    
        # Retrieve user's public profile information
        data = urllib.urlopen('https://graph.facebook.com/me?access_token=%s' % access_token)
        fb = json.load(data)

        try:
            # Check if user profile exists
            user = self.user_class.objects(facebook_id=fb['id']).first()

            # Update access token
            user.token = access_token
            user.save()

        except self.user_class.DoesNotExist:
            # User profile doesn't exist, create new user
            username = fb.get('username', fb['id'])
            user = self.user_class.objects.create_user(username=username, email=fb['email'])
            user.first_name = fb['first_name']
            user.last_name = fb['last_name']
            user.token = access_token
            user.facebook_id = fb['id']
            user.gender = fb['gender']
            user.save()

        return user

    def get_user(self, user_id):
        """ 
        Returns the user from a given ID. 
        """
    
        try:
            return self.user_class.objects.with_id(user_id)
        except self.user_class.DoesNotExist:
            return None

        supports_object_permissions = False
        supports_anonymous_user = True

    @property
    def user_class(self):
        self._user_class = models.CustomUser
        return self._user_class
