from flask import Flask
from flask import jsonify
from flask import json
from flask import request, Response
from flask import session
from flask import g
from flask import render_template
from flask import redirect, url_for
from flask import flash
from flask import send_file
from flask import current_app
from flaskext.babel import gettext, ngettext, lazy_gettext
from flaskext.babel import Babel
from flaskext.babel import format_datetime
from flaskext.gravatar import Gravatar
from datetime import datetime
import logging
import os
import sys
import pytz
import uuid
import traceback
import settings
from optparse import OptionParser
from getpass import getpass
import pymongo
import bson
from bson import json_util, BSON
import utils
import schema
import messages
from decorators import admin_required, login_required, api_key_required
from api import api

app = Flask(__name__)
app.register_blueprint(api)
app.debug = settings.DEBUG
app.logger.setLevel(logging.ERROR)
app.config.from_object('settings')
# extensions
babel = Babel(app)
gravatar = Gravatar(app, size=16, rating='pg', default='mm', force_lower=False)

# ----- context processors -----
@app.context_processor
def inject_user():
    data = {}
    if session.has_key('user_id'):
        user = g.db.users.find_one({'uuid': session['user_id']})
        data['user'] = user
    else:
        data['user'] = None
    return data
# ----- end context processors

# ----- filters -----
@app.template_filter('date_from_timestamp')
def date_from_timestamp(timestamp):
    return format_datetime(datetime.fromtimestamp(timestamp))

@app.template_filter('convert_to_localtime')
def convert_to_localtime(dt):
    return format_datetime(dt)

@app.template_filter('convert_from_bytes')
def convert_from_bytes(size):
    bytes = float(size)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2f TB' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2f GB' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2f MB' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2f KB' % kilobytes
    else:
        size = '{0} bytes'.format(int(bytes))
    return size

# ----- end filters -----
@app.before_request
def before_request():
    g.db = get_db_connection()

@app.teardown_request
def teardown_request(exception):
    pass

def get_db_connection():
    conn = pymongo.Connection(host=app.config['DB_HOST'], \
        port=app.config['DB_PORT'], username=app.config['DB_USER'], \
        password=app.config['DB_PASSWORD'])
    return conn[app.config['DB_NAME']]

@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the account
    if session.has_key('user'):
        user = g.db.users.find_one({'username': session['user']})
        if user.has_key('locale'):
            return user['locale']
    # otherwise try to guess the language from the user accept
    # header the browser sends
    return request.accept_languages.best_match([x[0] for x in app.config['LOCALES']])

@babel.timezoneselector
def get_timezone():
    # if a user is logged in, use the locale from the account
    if session.has_key('user'):
        user = g.db.users.find_one({'username': session['user']})
        if user.has_key('timezone'):
            return user['timezone']

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about/")
def about():
    return render_template("about.html")

@app.route("/events/")
def events():
    ctx = {
        'events': tuple(utils.find_events()),
    }
    return render_template("events.html", **ctx)

@app.route("/events/new/", methods=['GET', 'POST'])
@login_required
def new_event():
    if request.method == 'GET':
        return render_template("new_event.html")
    try:
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        start_time = request.form['start_time']
        end_date = request.form['end_date']
        end_time = request.form['end_time']
        location = request.form['location']
        latlng = request.form['latlng']
        owner = session['user_id']
        utils.add_event(title=title, description=description, start_date=start_date,\
            start_time=start_time, end_date=end_date, end_time=end_time, \
            location=location, latlng=latlng, owner=owner)
    except Exception, e:
        flash(str(e), 'error')
    return redirect(url_for('events'))

@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    username = request.form['username']
    password = request.form['password']
    user = g.db.users.find_one({'username': username})
    errors = False
    if not user:
        flash(messages.INVALID_USERNAME_PASSWORD, 'error')
        errors = True
    else:
        if utils.encrypt_password(password, app.config['SECRET_KEY']) == user['password']:
            auth_token = str(uuid.uuid4())
            g.db.users.update({'username': username}, {"$set": {'auth_token': auth_token} })
            session['user_id'] = user['uuid']
            session['user'] = username
            session['role'] = user['role']
            session['auth_token'] = auth_token
        else:
            flash(messages.INVALID_USERNAME_PASSWORD, 'error')
            errors = True
    if errors:
        url = url_for('login')
    else:
        if request.args.has_key('next'):
            url = request.args['next']
        else:
            url = url_for('index')
    return redirect(url)

@app.route("/logout/", methods=['GET'])
def logout():
    if 'auth_token' in session:
        session.pop('auth_token')
    if 'role' in session:
        session.pop('role')
    if 'user' in session:
        g.db.users.update({'username': session['user']}, {"$set": {'auth_token': None} })
        session.pop('user')
        session.pop('user_id')
    return redirect(url_for('index'))

@app.route("/accounts/")
@admin_required
def accounts():
    users = g.db.users.find()
    roles = g.db.roles.find()
    # sort
    ctx = {
        'users': list(users),
        'roles': list(roles),
    }
    return render_template('accounts.html', **ctx)

@app.route("/account/", methods=['GET', 'POST'])
@login_required
def account():
    username = session['user']
    if request.method == 'POST':
        g.db.users.update({'username': username}, {"$set": {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'api_key': request.form['api_key'],
            'locale': request.form['locale'],
            'timezone': request.form['timezone'],
            } 
        })
        flash(messages.ACCOUNT_UPDATED, 'success')
    account = g.db.users.find_one({'username': username})
    ctx = {
        'account': account,
        'timezones': pytz.all_timezones,
        'locales': app.config['LOCALES'],
    }
    return render_template('account.html', **ctx)

@app.route("/accounts/adduser/", methods=['POST'])
@admin_required
def add_user():
    form = request.form
    try:
        utils.create_user(username=form['username'], email=form['email'], \
            password=form['password'], role=form['role'], enabled=True)
        flash(messages.USER_CREATED, 'success')
    except Exception, e:
        flash('{0} {1}'.format(messages.NEW_USER_ERROR, e), 'error')
    return redirect(url_for('accounts'))

@app.route("/accounts/toggleuser/<username>/")
@admin_required
def toggle_user(username):
    try:
        utils.toggle_user(username)
    except Exception, e:
        app.logger.error(e)
        flash('{0} {1}'.format(messages.ERROR_DISABLING_USER, e), 'error')
    return redirect(url_for('accounts'))

@app.route("/accounts/deleteuser/<username>/")
@admin_required
def delete_user(username):
    try:
        utils.delete_user(username)
        flash(messages.USER_DELETED, 'success')
    except Exception, e:
        flash('{0} {1}'.format(messages.ERROR_DELETING_USER, e), 'error')
    return redirect(url_for('accounts'))

@app.route("/accounts/addrole/", methods=['POST'])
@admin_required
def add_role():
    form = request.form
    try:
        utils.create_role(form['rolename'])
        flash(messages.ROLE_CREATED, 'success')
    except Exception, e:
        flash('{0} {1}'.format(messages.NEW_ROLE_ERROR, e), 'error')
    return redirect(url_for('accounts'))

@app.route("/users/deleterole/<rolename>/")
@admin_required
def delete_role(rolename):
    try:
        utils.delete_role(rolename)
        flash(messages.ROLE_DELETED, 'success')
    except Exception, e:
        flash('{0} {1}'.format(messages.ERROR_DELETING_ROLE, e), 'error')
    return redirect(url_for('accounts'))

# ----- api -----

@app.route("/api/generatekey/")
@login_required
def api_generate_key():
    ctx = {
        'key': ''.join(Random().sample(string.letters+string.digits, 32)),
    }
    return jsonify(ctx)

def bson_to_json(data):
    return json.dumps(data, default=json_util.default, sort_keys=True)

def make_api_response(data=None, status=200):
    return Response(data, status=status, mimetype='application/json')
# ----- end api -----

# ----- management command -----
def create_user():
    db = get_db_connection()
    try:
        username = raw_input('Username: ').strip()
        email = raw_input('Email: ').strip()
        while True:
            password = getpass('Password: ')
            password_confirm = getpass(' (confirm): ')
            if password_confirm == password:
                break
            else:
                print('Passwords do not match... Try again...')
        role = raw_input('Role: ').strip()
        # create role if needed
        if not db.roles.find_one(schema.role(role)):
            utils.create_role(role)
        utils.create_user(username=username, email=email, password=password, \
            role=role, enabled=True)
        print('User created/updated successfully...')
    except KeyboardInterrupt:
        pass

def toggle_user(active):
    try:
        username = raw_input('Enter username: ').strip()
        try:
            utils.toggle_user(username, active)
        except Exception, e:
            print(e)
            sys.exit(1)
    except KeyboardInterrupt:
        pass

if __name__=="__main__":
    op = OptionParser()
    op.add_option('--create-user', dest='create_user', action='store_true', default=False, help='Create/update user')
    op.add_option('--enable-user', dest='enable_user', action='store_true', default=False, help='Enable user')
    op.add_option('--disable-user', dest='disable_user', action='store_true', default=False, help='Disable user')
    opts, args = op.parse_args()

    if opts.create_user:
        create_user()
        sys.exit(0)
    if opts.enable_user:
        toggle_user(True)
        sys.exit(0)
    if opts.disable_user:
        toggle_user(False)
        sys.exit(0)
    # run app
    app.run()


