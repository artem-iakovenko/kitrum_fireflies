import time
from datetime import datetime
import urllib.request
import requests
import ssl
from api import api_request
import emoji
from slugify import slugify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
ssl._create_default_https_context = ssl._create_unverified_context

drive_scopes = ["https://www.googleapis.com/auth/drive"]


def get_note_body(meeting_details, event_attendees, audio_url, video_url):
    # print(meeting_details)
    m_title = f"{meeting_details['title']}"
    m_date = datetime.utcfromtimestamp(meeting_details['date'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    m_duration = meeting_details['duration']
    w_errors = False
    try:
        m_overview = meeting_details['summary']['overview'].replace("**", "")
    except:
        w_errors = True
        m_overview = ""
    try:
        m_action_items = meeting_details['summary']['action_items'].replace("**", "")
    except:
        w_errors = True
        m_action_items = ""
    try:
        m_notes = meeting_details['summary']['shorthand_bullet'].replace("**", "")
        m_notes = emoji.replace_emoji(m_notes, replace='• ')
    except:
        w_errors = True
        m_notes = ""
    print(f"WITH ERRORS: {w_errors}")
    note_body = f"""Date: {m_date}
Duration: {m_duration} mins
Participants: {", ".join(event_attendees)}
Transcript URL: {meeting_details['transcript_url']}
Audio URL: {audio_url or ""}
Video URL: {video_url or ""}

➔ㅤOverview:
{m_overview}

➔ㅤAction Items:
{m_action_items}

➔ㅤNotes:
{m_notes}
"""
    return note_body


def push_note(parent_id, meeting_details, event_attendees, audio_url):
    # print(meeting_details)
    m_title = f"{meeting_details['title']}"
    m_date = datetime.utcfromtimestamp(meeting_details['date'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    m_duration = meeting_details['duration']
    w_errors = False
    try:
        m_overview = meeting_details['summary']['overview'].replace("**", "")
    except:
        w_errors = True
        m_overview = ""
    try:
        m_action_items = meeting_details['summary']['action_items'].replace("**", "")
    except:
        w_errors = True
        m_action_items = ""
    try:
        m_notes = meeting_details['summary']['shorthand_bullet'].replace("**", "")
        m_notes = emoji.replace_emoji(m_notes, replace='• ')
    except:
        w_errors = True
        m_notes = ""
    print(f"WITH ERRORS: {w_errors}")
    note_body = f"""Date: {m_date}
Duration: {m_duration} mins
Participants: {", ".join(event_attendees)}
Transcript URL: {meeting_details['transcript_url']}
Audio URL: {audio_url}

➔ㅤOverview:
{m_overview}

➔ㅤAction Items:
{m_action_items}

➔ㅤNotes:
{m_notes}
"""

    note_data = {
        "data": [
           {
                "Note_Title": m_title,
                "Note_Content": note_body,
                "Parent_Id": parent_id,
                "se_module": "Candidates"
            }
        ]
    }

    add_note = api_request(
        f"https://www.zohoapis.com/crm/v2/Candidates/{parent_id}/Notes",
        "zoho_crm",
        "post",
        note_data
    )
    return add_note['data'][0]['status']


def mark_as_synced(candidate_id):
    response = api_request(
        "https://www.zohoapis.com/crm/v2/Candidates",
        "zoho_crm",
        "put",
        {"data": [{"id": candidate_id, "Fireflies_Synced": True}]}
    )
    return response['data'][0]['status']


def download_file(file_url, file_name, folder_name):
    try:
        if folder_name == "audio":
            file_format = "mp3"
        elif folder_name == "video":
            file_format = "mp4"
        #file_url = meeting_details['audio_url']
        #file_name = f"{meeting_details['title']}-{meeting_details['date']}"
        slugified_name = slugify(file_name)
        urllib.request.urlretrieve(file_url, f'{folder_name}/{slugified_name}.{file_format}')
        return f'{folder_name}/{slugified_name}.{file_format}'
    except Exception as e:
        print(e)
        return None


def gdrive_upload(drive_json, file_path, file_type, parent_folder_id):
    try:
        # if file_type == 'video':
        #     parent_folder_id = "1WiB5EqCrQ2eJlKsHuNNKfly6-8jbfSRf"
        # elif file_type == 'audio':
        #     parent_folder_id = "1VTEbFJKjJSeyRHsh9jHIXBNpvp1Tv8Ro"
        file_name = file_path.replace("audio/", "").replace("video/", "").replace("transcriptsPdf/", "")
        creds = Credentials.from_authorized_user_info(drive_json, drive_scopes)
        creds.refresh(Request())
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": file_name,
            "parents": [parent_folder_id]
        }
        media = MediaFileUpload(file_path)
        create_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()
        file_url = f"https://drive.google.com/file/d/{create_file['id']}"
        return file_url
    except Exception as e:
        print(e)
        return None


def crm_add_attachment(file_url, candidate_id, audio_path):
    filename_splitted = audio_path.split("/")
    filename = filename_splitted[len(filename_splitted) - 1]
    add_attachment = api_request(
        f"https://www.zohoapis.com/crm/v2.1/Candidates/{candidate_id}/Attachments?title={filename}&attachmentUrl={file_url}",
        "zoho_crm",
        "crm_attachment",
        None
    )
    return add_attachment['data'][0]['status']
