import requests
from new_config import request_url


class Fireflies:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

    def get_users(self):
        users_query = '{"query": "{ users { name user_id, email ,integrations } }"}'
        return (requests.post(
            request_url,
            headers=self.headers,
            data=users_query)
        ).json()

    def get_meetings(self, query):
        return (requests.post(
            request_url,
            headers=self.headers,
            data=query)
        ).json()['data']['transcripts']

    def get_meeting_by_id(self, meeting_id):
        get_meeting_details_q = '{"query": "query Transcript($transcriptId: String!) { transcript(id: $transcriptId) { title speakers { id name } sentences { index speaker_name speaker_id text raw_text start_time end_time } id calendar_id date duration host_email transcript_url audio_url video_url participants  meeting_attendees { email } calendar_id summary { gist action_items keywords outline overview shorthand_bullet }  }  }", "variables": {"transcriptId": "__tid__"}}'
        get_meeting_details_q = get_meeting_details_q.replace("__tid__", meeting_id)
        return (requests.post(
            request_url,
            headers=self.headers,
            data=get_meeting_details_q)
        ).json()['data']['transcript']