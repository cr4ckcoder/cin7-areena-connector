import requests
import json

url = "https://api.arenasolutions.com/v1/login"

payload = json.dumps({
  "email": "development@jobinandjismi.com",
  "password": "AJILsiva007@",
  "workspaceId": "901439761"
})
headers = {
  'Content-Type': 'application/json',
  'Cookie': 'arena_session_id=LABS-X6NcEmiYJOhGFa5LXLDtHWRNiFDws3Fy%7C; arena_ul_ev=1'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
