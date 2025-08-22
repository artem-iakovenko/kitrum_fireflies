import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
from secret_manager import access_secret


def find_event_attendees(calendar_json, calendar_id, search_date_unix, event_name):
    search_date = datetime.utcfromtimestamp(search_date_unix / 1000).strftime('%Y-%m-%d')
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    creds = Credentials.from_authorized_user_info(calendar_json, scopes)
    service = build("calendar", "v3", credentials=creds)

    events = service.events().list(
        calendarId=calendar_id,
        maxResults=2500,
        timeMin=f'{search_date}T00:00:00+01:00',
        timeMax=f'{search_date}T23:59:00+01:00',
        singleEvents=True
    ).execute()
    for event in events['items']:
        if 'summary' in event and event_name.lower() in event['summary'].lower():
            start_date = event['start']['dateTime']
            end_date = event['end']['dateTime']
            try:
                attds = [x['email'] for x in event['attendees']] if event['attendees'] else []
            except:
                attds = []
            return {
                "start_date": start_date,
                "end_date": end_date,
                "attendees": attds
            }
            # return [x['email'] for x in event['attendees']] if event['attendees'] else []
    return {}

