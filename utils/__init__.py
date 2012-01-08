import hashlib
import schema
import application
import messages
import settings
import gridfs
import os
import tempfile
import tarfile
import shutil
try:
    import simplejson as json
except ImportError:
    import json
from flask import session

def create_user(username=None, email=None, password=None, role=None, enabled=True):
    if not username or not password or not role:
        raise NameError('You must specify a username, password, and role')
    db = application.get_db_connection()
    # check for existing
    if list(db.users.find({'username': username})):
        raise RuntimeError('An account with that username already exists')
    data = schema.user(username=username, email=email, \
        password=encrypt_password(password, settings.SECRET_KEY), \
        role=role, enabled=enabled)
    db.users.insert(data)
    return True

def create_role(rolename=None):
    if not rolename:
        raise NameError('You must specify a rolename')
    db = application.get_db_connection()
    if not list(db.roles.find({'rolename': rolename})):
        data = schema.role(rolename)
        db.roles.insert(data)
    return True

def delete_user(username=None):
    if not username:
        raise NameError('You must specify a username')
    db = application.get_db_connection()
    db.users.remove({'username': username})
    return True

def delete_role(rolename=None):
    if not rolename:
        raise NameError('You must specify a rolename')
    db = application.get_db_connection()
    db.roles.remove(schema.role(rolename=rolename))
    return True

def toggle_user(username=None, enabled=None):
    if not username:
        raise NameError('You must specify a username')
    db = application.get_db_connection()
    user = db.users.find_one({'username': username})
    if user:
        if enabled != None:
            user['enabled'] = enabled
        else:
            current_status = user['enabled']
            if current_status:
                enabled = False
            else:
                enabled = True
        db.users.update({'username': username}, {"$set": {'enabled': enabled} })
        return True
    else:
        raise RuntimeError('User not found')

def get_user(username=None, api_key=None):
    if not username and not api_key:
        raise NameError('You must specify a username or api_key')
    db = application.get_db_connection()
    if username:
        return db.users.find_one({'username': username})
    else:
        return db.users.find_one({'api_key': api_key})

def encrypt_password(password=None, salt=None):
    h = hashlib.sha256(salt)
    h.update(password+salt)
    return h.hexdigest()

def save_file(filename=None, path=None, version=None, **kwargs):
    if not filename or not path:
        raise NameError('You must specify a filename and path')
    if not os.path.exists(path):
        raise RuntimeError('Unable to locate file {0}'.format(path))
    db = application.get_db_connection()
    fs = gridfs.GridFS(db)
    return fs.put(open(path).read(), filename=filename, version=version, **kwargs)

def get_file(filename=None, version=-1, **kwargs):
    if not filename:
        raise NameError('You must specify a filename')
    db = application.get_db_connection()
    fs = gridfs.GridFS(db)
    return fs.get_version(filename=filename, version=version, **kwargs)

def delete_file(filename=None, version=-1, **kwargs):
    if not filename:
        raise NameError('You must specify a filename')
    db = application.get_db_connection()
    fs = gridfs.GridFS(db)
    return fs.delete(get_file(filename=filename, version=version, **kwargs)._id)

def add_event(title=None, description=None, start_date=None, start_time=None, \
    end_date=None, end_time=None, location=None, latlng=None):
    if not title or not description or not location:
        raise NameError('You must specify a title, description, and location')
    db = application.get_db_connection()
    data = schema.event(title=title, description=description, start_date=start_date, \
        start_time=start_time, end_date=end_date, end_time=end_time, \
        location=location, latlng=latlng)
    return db.events.insert(data)

def get_event(uuid=None):
    if not uuid:
        raise NameError('You must specify a uuid')
    db = application.get_db_connection()
    return db.events.find_one({'uuid': uuid})

def delete_event(uuid=None):
    if not uuid:
        raise NameError('You must specify a uuid')
    db = application.get_db_connection()
    return db.events.remove({'uuid': uuid})

