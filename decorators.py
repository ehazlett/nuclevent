#!/usr/bin/env python
from functools import wraps
from flask import g, session, redirect, url_for, request
from flask import flash
from flask import current_app
from flask import json, jsonify
import schema
import messages
import utils

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session or 'auth_token' not in session:
            flash(messages.ACCESS_DENIED, 'error')
            return redirect(url_for('index'))
        user = g.db.users.find_one({'username': session['user']})
        if 'role' not in user or user['role'].lower() != 'admin':
            flash(messages.ACCESS_DENIED, 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'auth_token' not in session:
            url = url_for('login', next=request.path)
            return redirect(url)
        return f(*args, **kwargs)
    return decorated

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = utils.get_user(session['user'])
        if 'uuid' in kwargs:
            evt = g.db.events.find_one({'uuid': kwargs['uuid']})
            if user['role'].lower() != 'admin':
                if evt:
                    if evt['owner'] != session['user_id']:
                        flash(messages.ACCESS_DENIED, 'error')
                        return redirect(url_for('events'))
        return f(*args, **kwargs)
    return decorated

def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = None
        if 'api_key' in request.form:
            api_key = request.form['api_key']
        elif 'X-Apikey' in request.headers.keys():
            api_key = request.headers['X-Apikey']
        # validate
        if not api_key:
            data = {'error': messages.NO_API_KEY}
            return jsonify(data)
        if api_key not in current_app.config['API_KEYS']:
            data = {'error': messages.INVALID_API_KEY}
            return jsonify(data)
        session['api_key'] = api_key
        return f(*args, **kwargs)
    return decorated

