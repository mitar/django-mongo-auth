from django.conf import settings
from django.contrib import auth

def mongo_auth(request):
    context = {
        'LOGIN_REDIRECT_URL': settings.LOGIN_REDIRECT_URL,
        'REDIRECT_FIELD_NAME': auth.REDIRECT_FIELD_NAME,
        'request_get_next': request.REQUEST.get(auth.REDIRECT_FIELD_NAME),
    }
    return context
