import os
from api import api_request
from fireflies import Fireflies
from help_functions import download_file, gdrive_upload, get_note_body
from gcalendar import find_event_attendees
from datetime import datetime, timedelta
from new_config import TEAM_OWNERS, CALL_FOLDERS, TRANSCRIPT_FOLDERS, COLORS_BY_INDEX
from fpdf import FPDF
import re
from fpdf.enums import XPos, YPos
import json
from secret_manager import access_secret

class FirefliesCrmIntegration:
    def __init__(self, user_email, user_token, user_team, crm_event_id, crm_main_contact_id,transcript_full_data, synced_events, visibility):
        self.user_email = user_email
        self.user_token = user_token
        self.user_team = user_team
        self.user_transcripts = []
        self.transcript = transcript_full_data
        self.event_name = transcript_full_data['title']
        self.formatted_sentences = []
        self.transcript_note = ""
        self.synced_events = synced_events
        self.visibility = visibility
        self.crm_event_id = crm_event_id
        self.crm_main_contact_id = crm_main_contact_id

    def split_attendees(self, event_attendees):
        kitrum_attendees_ids = []
        other_attendees_ids = []
        kitrum_attendees_emails = []
        other_attendees_emails = []
        potential_stages = []
        for event_attendee in event_attendees:
            crm_contacts_response = api_request(
                f"https://www.zohoapis.com/crm/v2/Contacts/search?criteria=((Email:equals:{event_attendee})or(Secondary_Email:equals:{event_attendee}))",
                "zoho_crm",
                "get",
                None
            )['data']
            if crm_contacts_response:
                contact_info = crm_contacts_response[0]
                cid = contact_info['id']
                layout = contact_info['Layout']['name']
                if "kitrum.com" not in event_attendee:
                    other_attendees_ids.append(cid)
                    related_deals = api_request(
                        f"https://www.zohoapis.com/crm/v2/Contacts/{cid}/Deals",
                        "zoho_crm",
                        "get",
                        None
                    )['data']
                    for related_deal in related_deals:
                        if related_deal['Stage'] not in potential_stages:
                            potential_stages.append(related_deal['Stage'])
                else:
                    kitrum_attendees_ids.append(cid)
            else:
                if "kitrum.com" not in event_attendee:
                    other_attendees_emails.append(event_attendee)
                else:
                    kitrum_attendees_emails.append(event_attendee)
        if self.crm_main_contact_id and self.crm_main_contact_id not in other_attendees_ids:
            other_attendees_ids.append(self.crm_main_contact_id)
        return {
            "kitrum_ids": kitrum_attendees_ids,
            "other_ids": other_attendees_ids,
            "kitrum_emails": kitrum_attendees_emails,
            "other_emails": other_attendees_emails,
            "potential_stages": potential_stages
        }

    def parce_sentences(self):
        sentences = self.transcript['sentences']
        results = []
        speaker = ""
        speaker_id = ""
        text = []
        start_time = ""
        for sentence in sentences:
            current_speaker = sentence['speaker_name']
            current_speaker_id = str(sentence['speaker_id'])
            current_text = sentence['text']
            current_start_time = sentence['start_time']
            if not speaker or current_speaker == speaker:
                speaker = current_speaker
                speaker_id = current_speaker_id
                text.append(current_text)
                if not start_time:
                    start_time = current_start_time
            else:
                results.append({"speaker": speaker, "speaker_id": speaker_id, "text": text, "start": start_time,
                                "formatted_time": self.convert_time(start_time)})
                speaker = current_speaker
                speaker_id = current_speaker_id
                text = [current_text]
                start_time = current_start_time
        results.append({"speaker": speaker, "speaker_id": speaker_id, "text": text, "start": start_time,
                        "formatted_time": self.convert_time(start_time)})
        self.formatted_sentences = results
        transcript_note = ""
        for formatted_sentence in self.formatted_sentences:
            transcript_note += f'<br><b>{formatted_sentence["speaker"]} - {formatted_sentence["formatted_time"]}</b><br>'
            transcript_note += f'<p style="margin-inline-start:20px;"><i>{". ".join(formatted_sentence["text"])}</i></p>'
        self.transcript_note = transcript_note

    def convert_time(self, time_sec):
        time_min = time_sec / 60
        minutes = int(time_min)
        seconds = (time_min - minutes) * 60
        time_str = f"{minutes}:{seconds:.0f}"
        hours, minutes = time_str.split(":")
        return f"{int(hours):02}:{int(minutes):02}"

    def convert_to_valid_filename(self, s):
        s = str(s)
        s = re.sub(r"[^\w\.-]", "_", s)
        return s.strip("_") or "untitled"

    # def convert_to_valid_filename(self, s, replacement_char='_'):
    #     s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement_char, s)
    #     max_length = 255
    #     return s[:max_length].strip()

    def save_transcripts_to_pdf(self, file_name):
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('djv', '', 'fonts/DejaVuSans.ttf')
        pdf.add_font('djv', 'B', 'fonts/DejaVuSans-Bold.ttf')
        pdf.add_font('djv', 'I', 'fonts/DejaVuSans-Oblique.ttf')
        pdf.set_font("djv", style='B', size=12)
        pdf.cell(200, 10, text=f"Transcript ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("djv", style='I', size=8)
        pdf.cell(200, 10, text=f"Event Name: {self.event_name} ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for sentence in self.formatted_sentences:
            speaker_name, speaker_id, text = sentence['speaker'], sentence['speaker_id'], ' '.join(sentence['text'])
            formatted_time = sentence['formatted_time']

            pdf.cell(200, 5, text="", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("djv", style='B', size=10)
            if speaker_id in COLORS_BY_INDEX:
                color = COLORS_BY_INDEX[speaker_id]
                pdf.set_text_color(color["r"], color["g"], color["b"])
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.set_font("djv", style='', size=8)
            pdf.cell(200, 6, text=f"{sentence['speaker']} - {formatted_time}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("djv", style='I', size=8)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 3, text=f"      {' '.join(sentence['text'])}")
        # file_name = f"{self.convert_to_valid_filename(self.event_name)}.pdf"
        file_path = f"transcriptsPdf/{file_name}.pdf"
        pdf.output(file_path)
        return file_path

    def create_kitrum_participants_crm(self, kitrum_participants_emails):
        created_ids = []
        for kitrum_participant_email in kitrum_participants_emails:
            try:
                people_response = api_request(
                    "https://people.zoho.com/people/api/forms/employee/getRecords?searchParams={searchField: 'EmailID', searchOperator: 'Is', searchText : " + kitrum_participant_email + "}",
                    "zoho_people",
                    "get",
                    None
                )['response']['result'][0]
                people_employee_id = list(people_response.keys())[0]
                people_employee = people_response[people_employee_id][0]
            except:
                people_employee = {}

            type_of_participant = "Contractor"
            if people_employee:
                participant_first_name = people_employee['FirstName'] if 'FirstName' in people_employee else ''
                participant_last_name = people_employee['LastName'] if 'LastName' in people_employee else ''
                type_of_participant = "Contractor" if "Contractor" in people_employee['Department'] else 'KITRUM Member'
            else:
                name_from_email = kitrum_participant_email.split("@")[0]
                if "." in name_from_email:
                    participant_first_name = name_from_email.split(".")[0].capitalize()
                    participant_last_name = name_from_email.split(".")[1].capitalize()
                else:
                    participant_first_name = name_from_email.capitalize()
                    participant_last_name = ""

            crm_map = {
                "First_Name": participant_first_name,
                "Last_Name": participant_last_name or 'Unknown',
                "Type_of_Participant": type_of_participant,
                "Email": kitrum_participant_email,
                "Layout": {"id": "1576533000327608471"}
            }
            new_contact = api_request(
                "https://www.zohoapis.com/crm/v2/Contacts",
                "zoho_crm",
                "post",
                {"data": [crm_map]}
            )
            new_contact_id = new_contact['data'][0]['details']['id']
            created_ids.append(new_contact_id)
        return created_ids

    def form_participants(self, kitrum_ids, other_ids, kitrum_emails, other_emails):
        participants = []
        merged_ids = kitrum_ids + other_ids
        merged_emails = other_emails
        for merged_id in merged_ids:
            participants.append({
                "invited": False,
                "type": "contact",
                "participant": {
                    "id": merged_id
                }
            })
        for merged_email in merged_emails:
            participants.append({
                "invited": False,
                "type": "email",
                "participant": merged_email
            })
        return participants

    def get_potential_stages(self, potential_stages):
        if not potential_stages:
            return "Lead"
        elif 'Closed Won. Working together.' in potential_stages:
            return "Client"
        elif 'Closed Won. Ex-client.' in potential_stages:
            return "Exclient"
        elif 'Project has started' in potential_stages:
            return "Project has started"
        else:
            return "Potential"

    def push_media_to_drive(self, drive_json, file_name, video_url, audio_url, visibility):
        media_url = video_url if video_url else audio_url
        media_type = "video" if video_url else "audio"
        main_folder_id = CALL_FOLDERS[self.user_team][visibility]
        gdrive_media_url = None
        if media_url:
            try:
                media_path = download_file(media_url, file_name, media_type)
                gdrive_media_url = gdrive_upload(drive_json, media_path, media_type, main_folder_id)
                os.remove(media_path)
            except Exception as e:
                print(e)
                pass
        return gdrive_media_url

    def update_crm_meeting(self, event_map):
        create_meeting = api_request(
            f"https://www.zohoapis.com/crm/v2/Events/{self.crm_event_id}",
            "zoho_crm",
            "put",
            {'data': [event_map]}
        )
        try:
            crm_meeting_id = create_meeting['data'][0]['details']['id']
        except Exception as e:
            print(e)
            crm_meeting_id = ""
        if crm_meeting_id:
            print(f"\tCRM Meeting {self.crm_event_id} has been successfully Updated")
        return f"https://crm.zoho.com/crm/org55415226/tab/Events/{crm_meeting_id}" if crm_meeting_id else None

    def attach_transcript_note_to_contact(self, meeting_name, contact_id):
        print("Attaching Note to Contact")
        if not self.transcript_note or not contact_id:
            return
        note_data = {
            "data": [
                {
                    "Note_Title": f"AI Transcript - {meeting_name}",
                    "Note_Content": self.transcript_note
                }
            ]
        }
        note_response = api_request(
            f"https://www.zohoapis.com/crm/v8/Contacts/{contact_id}/Notes",
            "zoho_crm",
            "post",
            note_data
        )

    def transcript_handler(self, transcript):
        calendar_json = json.loads(access_secret("kitrum-cloud", "google_calendar_artem"))
        drive_json = json.loads(access_secret("kitrum-cloud", "google_drive_artem"))
        event_date = transcript['date']
        default_datetime_start = datetime.fromtimestamp(event_date / 1000)
        default_datetime_end = default_datetime_start + timedelta(hours=1)
        default_datetime_start_iso = default_datetime_start.isoformat()
        default_datetime_end_iso = default_datetime_end.isoformat()

        transcript_id, meeting_name, meeting_date_unix = transcript['id'], transcript['title'], transcript['date']

        file_name = f"{self.convert_to_valid_filename(self.event_name)}-{meeting_date_unix}".lower()
        if file_name in self.synced_events:
            return "Event is already synced"
        transcript_sentences = transcript['sentences']
        try:
            self.parce_sentences()
            transcript_path = self.save_transcripts_to_pdf(file_name)
        except Exception as e:
            print(e)
            transcript_path = None

        print(f"Transcript Path: {transcript_path}")

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        transcript_result = {
            'transcript_id': transcript_id,
            'fireflies_owner': self.user_email,
            'fireflies_owner_team': self.user_team,
            'name': meeting_name,
            'file_name': file_name,
            'calendar_event_found': False,
            'drive_media_url': None,
            'crm_meeting_url': None,
            'action_datetime': formatted_datetime
        }

        # host_email = transcript['host_email'] or self.user_email
        host_email = self.user_email
        team_owner = TEAM_OWNERS[self.user_team]
        # GET GOOGLE CALENDAR EVENT
        google_calendar_found = False
        try:
            event_gcal = find_event_attendees(calendar_json, host_email, meeting_date_unix, meeting_name)
        except Exception as e:
            print(e)
            event_gcal = {}
        event_attendees = event_gcal['attendees'] if 'attendees' in event_gcal else {}
        start_date, end_date = event_gcal['start_date'] if 'start_date' in event_gcal else None, event_gcal[
            'end_date'] if 'end_date' in event_gcal else None
        if not event_attendees or not start_date or not end_date:
            pass
        else:
            google_calendar_found = True
        print(f"\tSearching event {meeting_name} on Google Calendar: {google_calendar_found}")
        transcript_result['calendar_event_found'] = google_calendar_found
        splitted_attendees = self.split_attendees(event_attendees)
        created_participants_ids = self.create_kitrum_participants_crm(splitted_attendees['kitrum_emails'])
        splitted_attendees['kitrum_ids'].extend(created_participants_ids)
        participants = self.form_participants(
            splitted_attendees['kitrum_ids'],
            splitted_attendees['other_ids'],
            splitted_attendees['kitrum_emails'],
            splitted_attendees['other_emails']
        )
        lead_stage = self.get_potential_stages(splitted_attendees['potential_stages'])

        # PUSH CALL TO GOOGLE DRIVE
        audio_url, video_url = transcript['audio_url'], transcript['video_url']
        try:
            drive_url = self.push_media_to_drive(drive_json, file_name, audio_url, video_url, self.visibility)
        except Exception as e:
            print(e)
            drive_url = None
        transcript_result['drive_media_url'] = drive_url
        # PUSH TRANSCRIPT TO GOOGLE DRIVE
        gdrive_transcript_url = None
        if transcript_path:
            try:
                transcript_folder_id = TRANSCRIPT_FOLDERS[self.user_team][self.visibility]
                gdrive_transcript_url = gdrive_upload(drive_json, transcript_path, "transcript", transcript_folder_id)
                os.remove(transcript_path)
            except Exception as e:
                print(e)
        transcript_result['drive_transcript_url'] = gdrive_transcript_url

        # PUSH NOTE
        note_content = get_note_body(transcript, event_attendees, audio_url, video_url)

        try:
            event_map = {
                "$se_module": "Contacts",
                "Who_Id": self.crm_main_contact_id or splitted_attendees['other_ids'][0] if splitted_attendees['other_ids'] else "",
                "Event_Title": meeting_name,
                "Start_DateTime": start_date or default_datetime_start_iso,
                "End_DateTime": end_date or default_datetime_end_iso,
                "Meeting_mode": "Online",
                "Lead_stage": lead_stage,
                "Description": note_content,
                "Department": team_owner,
                "Participants": participants,
                "Recording_link": drive_url,
                "Transcript_link": gdrive_transcript_url,
                "Fireflies_Sync": True
            }
            crm_meeting_url = self.update_crm_meeting(event_map)
        except Exception as e:
            print("error while creating crm note")
            print(e)
            crm_meeting_url = None

        try:
            self.attach_transcript_note_to_contact(meeting_name, self.crm_main_contact_id or splitted_attendees['other_ids'][0] if splitted_attendees['other_ids'] else "")
        except:
            pass

        transcript_result['crm_meeting_url'] = crm_meeting_url
        return transcript_result

    def integrator(self):
        print(f"Transcript: {self.transcript['id']} - {self.transcript['title']} - {self.transcript['date']}")
        transcript_sync_results = self.transcript_handler(self.transcript)
        return transcript_sync_results


def individual_meeting_sync(crm_meeting_id):
    TEAM_TOKENS = json.loads(access_secret("kitrum-cloud", "fireflies_cdm"))

    crm_meeting_details = api_request(
        f"https://www.zohoapis.com/crm/v2/Events/{crm_meeting_id}",
        "zoho_crm",
        "get",
        None
    )['data'][0]

    main_contact = crm_meeting_details['Who_Id']
    main_contact_id = main_contact['id'] if main_contact else None
    # GET THIS DATA FROM CRM MEETING (IS RESTRICTED / TRANSCRIPT URL / USER EMAIL)
    is_restricted = crm_meeting_details['Is_Restricted']
    visibility = "restricted" if is_restricted else "default"
    transcript_url = crm_meeting_details['Fireflies_Meeting_URL']
    transcript_id = transcript_url.split("::")[1].split("?")[0]
    user_email = crm_meeting_details['Owner']['email']
    user_data = TEAM_TOKENS[user_email]
    synced_events = []
    fireflies_handler = Fireflies(user_data['token'])
    transcript = fireflies_handler.get_meeting_by_id(transcript_id)
    fireflies_handler = FirefliesCrmIntegration(
        user_email,
        user_data['token'],
        user_data['team'],
        crm_meeting_id,
        main_contact_id,
        transcript,
        synced_events,
        visibility
    )
    return fireflies_handler.integrator()


def cdm_meeting_sync(crm_meeting_id):
    # cdm_sync_result = individual_meeting_sync(crm_meeting_id)
    # return None
    try:
        cdm_sync_result = individual_meeting_sync(crm_meeting_id)
        print(cdm_sync_result)
    except Exception as e:
        print(e)
        return None


# cdm_meeting_sync("1576533000439947179")
