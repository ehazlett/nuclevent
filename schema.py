from uuid import uuid4
from datetime import datetime
import settings
import hashlib

def user(username=None, first_name=None, last_name=None, email=None, \
    password=None, role=None, enabled=True, uuid=None, locale=None, \
    timezone=settings.BABEL_DEFAULT_TIMEZONE):
    if not uuid:
        uuid = str(uuid4())
    data = {
        'uuid': uuid,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password,
        'role': role,
        'enabled': enabled,
        'locale': locale,
        'timezone': timezone,
    }
    return data

def role(rolename=None):
    return {'rolename': rolename}

def log(level=None, category='root', message=None):
    data = {
        'level': level,
        'category': category,
        'message': message,
    }
    return data

