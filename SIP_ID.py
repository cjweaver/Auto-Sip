import requests
import json
import re
from urllib.parse import urlparse
from urllib.parse import quote_plus
from login import site as sip_website


EASY_TEST_SHELFMARK = 'C125 / 13'
HARD_TEST_SHELFMARK = 'C102 / 239'

def search_request(shelfmark):
    # First strip any whitespace
    sip_to_look_up = shelfmark.replace(' ', '')
    shelfmark_no_ws = shelfmark.replace(' ', '')
    print('Stripped whitespace', sip_to_look_up)

    # Convert backslash('/') to !2F. this is the AJAX '!' separator with an escaped backslash '2F'
    sip_to_look_up = sip_to_look_up.replace('/', '!2F')

    # Pre and Append !22 double quote marks (") to search for the extact search terms
    sip_to_look_up = '!22' + sip_to_look_up + '!22'

    # Create the request
    # Not quite sure about the 0/10 this is the number of rows to search i.e you get 10 results
    start = 0
    n_rows = 10
    while True:
        r = requests.get(f'{sip_website}/api/SearchSIPs/null/{sip_to_look_up}/{start}/{n_rows}', verify = False)

        print("Requesting", r.url)
        print("Return code was", r.status_code)

        if r.status_code != 200:
            print(f"Unable to connect to the SIP tool. r.status_code = {r.status_code}")
            break
        elif len(r.json()) == 0:
            print(f"Unable to find a SIP using the shelfmark {shelfmark}")
            break
        print("r.text =", r.text)
        sip_results = json.loads(r.text)
        for sip in sip_results:
            print("sip is", sip)
            if sip["Title"].startswith(shelfmark_no_ws + ","):
                print("FOUND IT")
                print("\t", sip["Title"])
                return sip['Id']
        start += 10
    return None
        

# sip_id = search_request(EASY_TEST_SHELFMARK) 
# print("Easy test got sip_id", sip_id)
sip_id = search_request(HARD_TEST_SHELFMARK) 
print("Hard test got sip_id", sip_id)