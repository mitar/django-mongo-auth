django-mongo-auth
=================

Django_ authentication based on an extensible MongoEngine_ user class.

It supports common authentication providers (Facebook, Google, Twitter,
Foursquare, BrowserID/Persona, ...) and a traditional on-site registration workflow
with e-mail address confirmation. Additionally, anonymous users are given a
temporary account instance which can then be converted to an authenticated one.
Each account can be linked with multiple authentication providers.

.. _Django: https://www.djangoproject.com/
.. _MongoEngine: http://mongoengine.org/

Documentation is found at:

http://django-mongo-auth.readthedocs.org/
