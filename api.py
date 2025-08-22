import json
import requests
from auth import ZohoAuth
from new_config import oauth_credentials, success_status_codes

zoho_people_auth = ZohoAuth("zoho_people")
zoho_crm_auth = ZohoAuth("zoho_crm")


def api_request(url, source, method, post_data):
    if source == 'zoho_people':
        zoho_people_auth.get_or_refresh_access_token()
        access_headers = {
            'Authorization': f'Zoho-oauthtoken {zoho_people_auth.access_token}'
        }
    elif source == 'zoho_crm':
        zoho_crm_auth.get_or_refresh_access_token()
        access_headers = {
            'Authorization': f'Zoho-oauthtoken {zoho_crm_auth.access_token}'
        }
    else:
        print("Unknown source")
        return None
    if access_headers:
        print(access_headers)
        response = None
        if method == 'get':
            response = requests.get(url, headers=access_headers)
        elif method == 'put':
            response = requests.put(url, headers=access_headers, data=json.dumps(post_data))
            print(response.json())
        elif method == 'post':
            response = requests.post(url, headers=access_headers, data=json.dumps(post_data))
            print(response.json())
        elif method == 'patch':
            response = requests.patch(url, headers=access_headers, data=json.dumps(post_data))
        elif method == 'crm_attachment':
            response = requests.post(url, headers=access_headers)
        else:
            print("Unknown method")
        if response and response.status_code in success_status_codes:
            return response.json()
        elif response.status_code == 204:
            return {"data": []}
        else:
            return None
    else:
        return None





