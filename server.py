from flask import Flask, request, jsonify
import json
import threading
from datetime import datetime
from secret_manager import access_secret


app = Flask(__name__)


def require_api_key(view_function):
    from functools import wraps

    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        headers_api_key = request.headers.get("X-API-KEY")
        if headers_api_key != access_secret("kitrum-cloud", "vm_api_key"):
            return jsonify({"error": "Unauthorized"}), 401
        return view_function(*args, **kwargs)
    return decorated_function


@app.route('/recruiting_sync', methods=['POST'])
@require_api_key
def recruiting_sync():
    from recruiting_flow import recruiting_meetings_sync
    print("Starting Fireflies Sync for recruiting team...")
    trigger_date = datetime.now()
    thread = threading.Thread(target=recruiting_meetings_sync)
    thread.start()
    return jsonify({'status': "Fireflies sync has been triggered for recruiting team", 'trigger_date': trigger_date})


@app.route('/cdm_sync', methods=['POST'])
@require_api_key
def individual_sync():
    from cdm_am_flow import cdm_meeting_sync
    print("Request Received from Zoho CRM...")
    trigger_date = datetime.now()
    payload_data = json.loads(request.stream.read().decode())
    crm_meeting_id = payload_data["meeting_id"]
    thread = threading.Thread(target=cdm_meeting_sync, args=(crm_meeting_id,))
    thread.start()
    return jsonify({
        'status': f"Fireflies sync has been triggered for CDM Meeting Record: {crm_meeting_id}",
        'trigger_date': trigger_date
    })


app.run(host='0.0.0.0', port=7565)
# app.run(host='0.0.0.0', port=7261)
