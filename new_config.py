from secret_manager import access_secret
import json

request_url = 'https://api.fireflies.ai/graphql'
lead_stages = ["Client", "Exclient", "Potential", "Project has started"]
success_status_codes = [200, 201]

zcrm_oauth = json.loads(access_secret("kitrum-cloud", "zoho_crm"))
zp_oauth = json.loads(access_secret("kitrum-cloud", "zoho_people"))

oauth_credentials = {
    "zoho_crm": zcrm_oauth,
    "zoho_people": zp_oauth
}
TEAM_TOKENS = json.loads(access_secret("kitrum-cloud", "fireflies_cdm"))
RECRUITING_TOKENS = json.loads(access_secret("kitrum-cloud", "fireflies_recruiting"))
calendar_json = json.loads(access_secret("kitrum-cloud", "google_calendar_artem"))
drive_json = json.loads(access_secret("kitrum-cloud", "google_drive_artem"))
kitrum_bq_json = json.loads(access_secret("kitrum-cloud", "kitrum_bq"))


CALL_FOLDERS = {
    "sales": {
        "default": "1sq1StsgNlkzkM110rgolC8OKBTwdOhLG",
        "restricted": "1sq1StsgNlkzkM110rgolC8OKBTwdOhLG"
    },
    "delivery": {
        "default": "",
        "restricted": ""
    }
}

TRANSCRIPT_FOLDERS = {
    "sales": {
        "default": "1a4M_Lh32h8Ku_4MBRgDcClexdQ_QtGwy",
        "restricted": "1a4M_Lh32h8Ku_4MBRgDcClexdQ_QtGwy"
    },
    "delivery": {
        "default": "",
        "restricted": ""
    }
}



AM_KEYWORDS = ['qbr', 'plan/fact' ,'status update','interview', 'sharktank']

SALES_KEYWORDS = {
    "Intro": ['intro'],
    "Sync up": [],
    "Tech Discussion": ['tech discussion'],
    "Proposal": ['proposal'],
    "Interview": ['interview'],
    "Offline meeting": ['offline meeting'],
    "Conference meeting": ['conference meeting']
}
SALES_RESTRICTED = []
AM_KEYWORDS = {
    "QBR": ["qbr"],
    "Internal": ['plan/fact kpi'],
    "Status update": ['status update'],
    "SharkTank": ['sharktank']
}
AM_RESTRICTED = ["Internal"]

TEAM_OWNERS = {
    "sales": "Sales Managers",
    "delivery": "Account Managers"
}


COLORS_BY_INDEX = {
    "0": {"r": 0, "g": 102, "b": 0}, #dark green
    "1": {"r": 51, "g": 51, "b": 153}, # dark blue
    "2": {"r": 102, "g": 51, "b": 0},  #brown
    "3": {"r": 128, "g": 0, "b": 0}, #dark red
    "4": {"r": 102, "g": 0, "b": 102}, #dark purple
    "5": {"r": 102, "g": 102, "b": 51}, #khaki
    "6": {"r": 204, "g": 102, "b": 0}, #orange
    "7": {"r": 204, "g": 0, "b": 102}, #pink
    "8": {"r": 0, "g": 153, "b": 153}, #tqieuqw
    "9": {"r": 94, "g": 94, "b": 94}, #grey
    "10": {"r": 0, "g": 0, "b": 0}, #black
}