Installation
============

Using pip_ simply by doing::

    pip install django-mongo-auth

.. _pip: http://pypi.python.org/pypi/pip

You should then add ``mongo_auth`` and dependency ``django_browserid`` to ``INSTALLED_APPS``. Optionally,
to use provided templates, you can add ``mongo_auth.contrib``, too.

Add ``django_browserid.context_processors.browserid_form`` to ``TEMPLATE_CONTEXT_PROCESSORS`` to conclude
``django_browserid`` installation.

Afterwards, you configure authentication providers you want to offer:

    AUTHENTICATION_BACKENDS = (
        'mongo_auth.backends.MongoEngineBackend',
        'mongo_auth.backends.FacebookBackend',
        'mongo_auth.backends.TwitterBackend',
        'mongo_auth.backends.FoursquareBackend',
        'mongo_auth.backends.GoogleBackend',
        'mongo_auth.backends.BrowserIDBackend',
        'mongo_auth.backends.LazyUserBackend',
    )

Some require API keys by providers. Available settings:
* ``FACEBOOK_APP_ID``
* ``FACEBOOK_APP_SECRET``
* ``TWITTER_CONSUMER_KEY``
* ``TWITTER_CONSUMER_SECRET``
* ``FOURSQUARE_CLIENT_ID``
* ``FOURSQUARE_CLIENT_SECRET``
* ``GOOGLE_CLIENT_ID``
* ``GOOGLE_CLIENT_SECRET``

If you want to use custom User class (like ``mongo_auth.contrib.models.User``), you can set ``USER_CLASS`` to it.
Default is ``mongo_auth.models.User``.

``DEFAULT_USER_IMAGE`` can be used to configure user image for users without one. By default it is
``mongo_auth/images/unknown.png``.

Because ``django.contrib.sites`` does not work with MongoEngine, you can use ``SITE_NAME`` and ``DEFAULT_REQUEST``
to configure what site name is displayed and manually how full URLs are generated, respectively.