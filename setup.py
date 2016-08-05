#!/usr/bin/env python

import os

from setuptools import setup, find_packages

try:
    # Workaround for http://bugs.python.org/issue15881
    import multiprocessing
except ImportError:
    pass

VERSION = '0.1.2'

if __name__ == '__main__':
    setup(
        name = 'django-mongo-auth',
        version = VERSION,
        description = "Django authentication based on an extensible MongoEngine user class.",
        long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
        author = 'Mitar',
        author_email = 'mitar.django@tnode.com',
        url = 'https://github.com/mitar/django-mongo-auth',
        license = 'AGPLv3',
        packages = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests')),
        package_data = {},
        classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Framework :: Django',
        ],
        include_package_data = True,
        zip_safe = False,
        install_requires = [
            'Django>=1.3',
            'mongoengine>=0.6.11',
            'tweepy>=1.9',
            'django-browserid>=0.6',
            'django-missing>=0.1.10',
            'django-sekizai>=0.5'
        ],
    )
