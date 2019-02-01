import requests
import json
import time
from datetime import datetime
from login import site, user, password

r = requests.get("https://v12l-avsip.ad.bl.uk:8445/api/SIP/153", verify=False)
# Take the requests response 'r' and convert to a Python dictionary
j = json.loads(r.text)
print(j)




find_me = "Logical"
for item in j["StepStates"]:
    if item["StepTitle"] == find_me:
        print(item["StepStateId"])
    
    


