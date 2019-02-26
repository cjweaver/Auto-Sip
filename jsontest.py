import requests
import json
import time
from datetime import datetime
from login import site, user, password

r = requests.get("https://v12l-avsip.ad.bl.uk:8445/api/SIP/192", verify=False)
# Take the requests response 'r' and convert to a Python dictionary
j = r.json()
k = json.loads(j['ProcessMetadata'])

for node in k['processMetadata'][0]['children']:
        if node['processType'] == "Migration":
                for _ in node['devices']:
                        if _['deviceType'] == "Tape recorder":
                                print(_['parameters']['Tape recorder']['replaySpeed']['value'])

        



    


