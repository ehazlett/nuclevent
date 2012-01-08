import os
import logging
import sys
from flaskext.babel import gettext, lazy_gettext
sys.path.append('./')
try:
    import simplejson as json
except ImportError:
    import json

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

APP_NAME = 'nuclevent'
BABEL_DEFAULT_LOCALE = 'en'
BABEL_DEFAULT_TIMEZONE = 'UTC'
DEBUG = True
# mongo
DB_HOST = '127.0.0.1'
DB_PORT = 27017
DB_NAME = 'nuclevent'
DB_USER = 'nuclevent'
DB_PASSWORD = ''
STATIC_PATH = os.path.join(PROJECT_PATH, 'static')
LOCALES = (
    ('en', lazy_gettext(u'English')),
    ('fr', lazy_gettext(u'French')),
)
SECRET_KEY = "PX0(5Or@92w`_b z1:s%j$kL8p[6{D^'"
# app version
VERSION = '0.1'

# check dirs
if not os.path.exists(STATIC_PATH):
    os.makedirs(STATIC_PATH)
