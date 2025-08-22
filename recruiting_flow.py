
import time
import os
from api import api_request
from fireflies import Fireflies
from help_functions import push_note, download_file, gdrive_upload, crm_add_attachment, mark_as_synced
from gcalendar import find_event_attendees
from bq import insert_to_bigquery, get_data_from_bq, run_query
from queries import synced_events_q, delete_logs_q
from datetime import datetime, timedelta
from secret_manager import access_secret
import json
from google.cloud import bigquery
from google.oauth2 import service_account

skip_ids = ["1721122200000"]
folder_id = "1WiB5EqCrQ2eJlKsHuNNKfly6-8jbfSRf"


def launch():
    daycount = 30
    start_date = datetime.now() - timedelta(days=daycount)
    start_date = str(start_date)[0:10]
    transcript_query = '{"query": "query Transcripts($limit: Int $fromDate: DateTime) { transcripts(limit: $limit fromDate: $fromDate) { title id calendar_id date duration host_email transcript_url audio_url video_url participants  meeting_attendees { email } calendar_id summary { action_items keywords outline overview shorthand_bullet } } }", "variables": {"limit": 50, "fromDate": "'+ start_date +'"}}'

    print(f"Fetching meetings after: {start_date}")
    kitrum_bq_json = json.loads(access_secret("kitrum-cloud", "kitrum_bq"))
    credentials = service_account.Credentials.from_service_account_info(kitrum_bq_json)
    bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    synced_events_response = get_data_from_bq(bq_client, synced_events_q)
    print(f"Total Synced Events Fetched: {len(synced_events_response)}")
    synced_events = [x['transcript_id'] for x in synced_events_response]

    RECRUITING_TOKENS = json.loads(access_secret("kitrum-cloud", "fireflies_recruiting"))
    calendar_json = json.loads(access_secret("kitrum-cloud", "google_calendar_artem"))
    drive_json = json.loads(access_secret("kitrum-cloud", "google_drive_artem"))


    all_results = []
    for user_email, user_data in RECRUITING_TOKENS.items():
        if user_email == 'artem.iakovenko@kitrum.com':
            continue
        print(f"\n\nCurrently Syncing Email: {user_email}")
        fireflies_handler = Fireflies(user_data['token'])
        # print(fireflies_handler.get_users())
        transcripts = fireflies_handler.get_meetings(transcript_query)
        transcripts.reverse()
        print(f"{len(transcripts)} transcripts available")
        sync_results = []
        for meeting_details in transcripts:
            print("------------" * 10)
            file_name = f"{meeting_details['title']}-{meeting_details['date']}"
            print(file_name)
            transcript_id = meeting_details['id']
            if str(transcript_id) in skip_ids:
                continue
            print(f"\n\t{meeting_details['title']}, {transcript_id}")
            print(f"\tCall Owner: {user_email}")
            # continue
            if transcript_id in synced_events:
                print("\tThis event is already Synced")
                continue
            else:
                synced_events.append(transcript_id)
                run_query(bq_client, delete_logs_q.replace("<tid>", transcript_id))
            meeting_name = meeting_details['title']
            meeting_date_unix = meeting_details['date']
            print(meeting_date_unix)
            print(f"\t1. Getting Event Attendees")
            event_gcal = find_event_attendees(calendar_json, user_email, meeting_date_unix, meeting_name)
            if not event_gcal:
                print("NOT GCAL")
                continue
            event_attendees = event_gcal['attendees']

            if not event_attendees:
                sync_results.append({"transcript_id": transcript_id, "user": user_email,"status": "error", "reason": "Event not found in Google Calendar"})
                continue

            print(f"\t\tEvent Attendees: {', '.join(event_attendees)}")
            if len(event_attendees) > 5:
                continue
            print("\t2. Searching for Candidates in Zoho CRM")
            zcrm_candidate_ids = []
            for event_attendee in event_attendees:
                if 'kitrum.com' in event_attendee:
                    continue
                crm_candidate_response = api_request(
                    f"https://www.zohoapis.com/crm/v2/Candidates/search?criteria=((Email:equals:{event_attendee})or(Secondary_Email:equals:{event_attendee}))",
                    "zoho_crm",
                    "get",
                    None
                )['data']
                if crm_candidate_response:
                    zcrm_candidate_ids.append(crm_candidate_response[0]['id'])
            print(f"\t\tRelevant Candidate Ids: {', '.join(zcrm_candidate_ids)}")

            if not zcrm_candidate_ids:
                sync_results.append({"transcript_id": transcript_id, "meeting_name": meeting_name, "user": user_email,"status": "error", "reason": "No appropriate records found in Zoho CRM"})
                continue

            print("\t3. Downloading Audio from FireFlies")
            audio_url = meeting_details['audio_url']
            audio_path = download_file(audio_url, file_name,'audio')
            if not audio_path:
                sync_results.append({"transcript_id": transcript_id, "meeting_name": meeting_name, "user": user_email, "status": "error", "reason": "Error Occured While downloading Audio Record"})
                continue
            time.sleep(2)
            print("\t4. Uploading Audio to Google Drive")
            gdrive_audio_url = gdrive_upload(drive_json, audio_path, 'audio', folder_id)
            if not gdrive_audio_url:
                sync_results.append({"transcript_id": transcript_id, "meeting_name": meeting_name, "user": user_email, "status": "error", "reason": "Error Occured While uploading Audio Record to Google Drive"})
                continue
            print("\t5. Pushing data to Zoho CRM")

            candidate_update_statuses = []
            for zcrm_candidate_id in zcrm_candidate_ids:
                attachment_status = crm_add_attachment(gdrive_audio_url, zcrm_candidate_id, audio_path)
                note_status = push_note(zcrm_candidate_id, meeting_details, event_attendees, gdrive_audio_url)
                synced_status = mark_as_synced(zcrm_candidate_id)
                candidate_update_statuses.append(attachment_status)
                candidate_update_statuses.append(note_status)
                candidate_update_statuses.append(synced_status)
                time.sleep(2)

            os.remove(audio_path)
            unique_statuses = list(set(candidate_update_statuses))
            if len(unique_statuses) > 1:
                sync_results.append({"transcript_id": transcript_id, "meeting_name": meeting_name, "user": user_email, "status": "partial success", "reason": "Some candidates haven't been updated"})
            else:
                if unique_statuses[0] == 'success':
                    sync_results.append({"transcript_id": transcript_id, "meeting_name": meeting_name, "user": user_email, "status": "success", "reason": ""})
                else:
                    sync_results.append({"transcript_id": transcript_id, "meeting_name": meeting_name, "user": user_email, "status": "error", "reason": "Error Occured while updating Candidates in Zoho CRM"})
        if sync_results:
            insert_to_bigquery(bq_client, sync_results, "kitrum-cloud.logging.crm_fireflies_integration")
            all_results.extend(sync_results)
    return all_results


def recruiting_meetings_sync():
    try:
        results = launch()
        print(results)
    except Exception as e:
        print(e)
        return None

# recruiting_meetings_sync()