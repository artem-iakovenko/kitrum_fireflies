import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/artem_iakovenko/service-account/secret-manager.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tokens/secret-manager.json"
from flask import Flask, request, jsonify
from urllib.parse import unquote
import json
import threading
import time
from datetime import datetime
from recruiting_flow import recruiting_meetings_sync
from cdm_am_flow import cdm_meeting_sync


app = Flask(__name__)


@app.route('/recruiting_sync', methods=['POST'])
def recruiting_sync():
    print("Starting Fireflies Sync for recruiting team...")
    trigger_date = datetime.now()
    thread = threading.Thread(target=recruiting_meetings_sync)
    thread.start()
    return jsonify({'status': "Fireflies sync has been triggered for recruiting team", 'trigger_date': trigger_date})


@app.route('/cdm_sync', methods=['POST'])
def individual_sync():
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




