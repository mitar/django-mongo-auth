from django.conf.urls import patterns, include, url
from django.core import urlresolvers

from . import forms, views

def build_patterns(alternative_views=None):
    def get_view(name):
        return getattr(alternative_views, name, getattr(views, name))

    return patterns('',
        # Registration, login, logout
        url(r'^register/$', get_view('RegistrationView').as_view(), name='registration'),
        url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'mongo_auth/login.html'}, name='login'),
        url(r'^logout/$', get_view('logout'), name='logout'),

        # Facebook
        url(r'^facebook/login/$', get_view('FacebookLoginView').as_view(), name='facebook_login'),
        url(r'^facebook/callback/$', get_view('FacebookCallbackView').as_view(), name='facebook_callback'),

        # Twitter
        url(r'^twitter/login/$', get_view('TwitterLoginView').as_view(), name='twitter_login'),
        url(r'^twitter/callback/$', get_view('TwitterCallbackView').as_view(), name='twitter_callback'),

        # Foursquare
        url(r'^foursquare/login/$', get_view('FoursquareLoginView').as_view(), name='foursquare_login'),
        url(r'^foursquare/callback/$', get_view('FoursquareCallbackView').as_view(), name='foursquare_callback'),

        # Google
        url(r'^google/login/$', get_view('GoogleLoginView').as_view(), name='google_login'),
        url(r'^google/callback/$', get_view('GoogleCallbackView').as_view(), name='google_callback'),

        # BrowserID
        url(r'^browserid/', get_view('BrowserIDVerifyView').as_view(), name='browserid_verify'),

        # Account
        url(r'^account/$', get_view('AccountChangeView').as_view(), name='account'),
        url(r'^account/password/change/$', get_view('PasswordChangeView').as_view(), name='password_change'),
        url(r'^account/confirmation/$', get_view('EmailConfirmationSendToken').as_view(), name='email_confirmation_send_token'),
        url(r'^account/confirmation/token/(?:(?P<confirmation_token>\w+)/)?$', get_view('EmailConfirmationProcessToken').as_view(), name='email_confirmaton_process_token'),

        # Password reset
        url(r'^account/password/reset/$', get_view('password_reset'), name='password_reset', kwargs={
            'password_reset_form': forms.PasswordResetForm,
            'template_name': 'mongo_auth/password_reset_form.html',
            'email_template_name': 'mongo_auth/password_reset_email.txt',
            'subject_template_name': 'mongo_auth/password_reset_subject.txt',
        }),
        url(r'^account/password/confirm/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$', get_view('password_reset_confirm'), name='password_reset_confirm', kwargs={
            'post_reset_redirect': urlresolvers.reverse_lazy('login'),
            'template_name': 'mongo_auth/password_reset_confirm.html',
        }),
    )

urlpatterns = build_patterns()
