from django.contrib import auth
from django.contrib.auth import models as auth_models

from . import backends

class LazyUserMiddleware(object):
    def process_request(self, request):
        if request.user and not isinstance(request.user, auth_models.AnonymousUser):
            assert isinstance(request.user, backends.User)
            return None

        user = auth.authenticate(request=request)
        assert user.is_anonymous()

        # We set the auth session key to prevent login to
        # cycle the session key or flush the whole session
        request.session[auth.SESSION_KEY] = user.id

        auth.login(request, user)

        return None
