from flask import Blueprint
from flask import jsonify
from flask import json
from flask import request, Response
from flask import session
from flask import g
from flask import redirect, url_for
from flask import current_app
from flaskext.babel import gettext, ngettext, lazy_gettext
from bson import json_util, BSON
import messages
import schema
from decorators import api_key_required

api = Blueprint('api', __name__)

def bson_to_json(data):
    return json.dumps(data, default=json_util.default, sort_keys=True)

def make_api_response(data=None, status=200):
    return Response(data, status=status, mimetype='application/json')

@api.route("/api/version")
@api_key_required
def api_version():
    return make_api_response(json.dumps(
        {
            'app': current_app.config['APP_NAME'],
            'version': current_app.config['API_VERSION'],
        }
    ))

# version 1.0 API
@api.route("/api/v1.0/events")
@api_key_required
def api_10_events():
    return make_api_response(bson_to_json(list(g.db.events.find({}, limit=50))))

# end version 1.0 API
