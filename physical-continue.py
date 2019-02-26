# Completing the Physical Structure and Process Metadata
# after the main script has failed (normally due to being logged out)

from datetime import datetime
import time
import openpyxl
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import ui
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from login import site, user, password

# Change these variables for the SIP that got stuck
# Leave notes as "" if there are none.
# reference_sip to copy process metadata from is taken from the XL spreadsheet 

notes = ""
sip_id = 422
reference_sip = 192




#Set up webdriver
driver = webdriver.Chrome()
driver.maximize_window()
#driver.implicitly_wait(10)
driver.wait = WebDriverWait(driver, 120)

sip_url = "{0}/api/SIP/{1}".format(site, sip_id)
print("Getting details for ", sip_id)
sip_req = requests.get(sip_url, verify=False)
sip_json = sip_req.json()
physical_structure_url = f'{site}/{sip_json["NavigationState"]["NavigationSteps"][3]["Path"]}'
sip_files = len(sip_json["Files"])
print("The Physical Structure URL is: ", physical_structure_url)
print(f"SIP id {sip_id} {sip_json['Title']}\n The number of files is {sip_files}")

driver.get(f"{site}/Account/LoginAD")
username_elem = driver.find_element_by_id("ADUserName")
password_elem = driver.find_element_by_id("Password")
username_elem.send_keys(user)
password_elem.send_keys(password)
password_elem.submit()


# Haven't arrived via clicking "Continue" from last step
# so...
driver.get(physical_structure_url)

s1 = ui.Select(driver.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="demo1"]/div/div[1]/div[1]/select'))))
# s1 = ui.Select(driver.find_element_by_xpath('//*[@id="demo1"]/div/div[1]/div[1]/select'))
# select disc from the dropdown
# The physical structure is curently hardcoded for CDRs only. Need to read the format from the XL sheet.
s1.select_by_index(2)
time.sleep(1)



for i in range(sip_files - 1):
# Clicking the dropdown above automatically adds a file select, hence len(file_names) - 1
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='demo2']/div/div[1]/div[3]/button[2]"))).click()
    # driver.wait.until(EC.presence_of_element_located((By.ID, "structure-heading")))
select_div = driver.find_element_by_xpath('//*[@id="demo2"]/div/div[2]/ul')
selects = select_div.find_elements_by_tag_name("select")
i = 1
for elem in selects:
    s1 = ui.Select(elem)
    s1.select_by_index(i)
    #time.sleep(1)
    i += 1

# Save and mark as step complete but don't continue to avoid next page modal
driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "nav-save-button"))).click()
driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "step-complete-checkbox"))).click()
time.sleep(5)


src_sip_id = reference_sip
dest_sip_id = sip_id
# get information for the src
src_url = "{0}/api/SIP/{1}".format(site, src_sip_id)
print("getting information for sip", src_sip_id)
src_req = requests.get(src_url, verify=False)
src_json = src_req.json()

# get information for the dest
dest_url = "{0}/api/SIP/{1}".format(site, dest_sip_id)
print("getting information for sip", dest_sip_id)
dest_req = requests.get(dest_url, verify=False)
dest_json = dest_req.json()

# get title of dest
dest_title = dest_json['Title']

# update title for the process metadata
print("setting dest_title to", dest_title)
d = json.loads(src_json['ProcessMetadata'])
d['processMetadata'][0]['text'] = dest_title

# Updates all the dates in the Process MD to datetime.now()
# and adds a note/comment on the last device
for c in d['processMetadata'][0]['children']:
    c['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
last_proc = d['processMetadata'][0]['children'][-1]
last_proc['devices'][-1]['notes'] = notes

dest_process_metadata = json.dumps(d)

# get the dest user id
dest_user_id = dest_json['UserId']
print('dest user_id is', dest_user_id)

# get the dest step state id for processmetadata
for x in dest_json['StepStates']:
    if x['StepTitle'] == "Process Metadata":
        dest_step_id = x['StepStateId']
        break
else:
    raise KeyError
print('dest step id is', dest_step_id)

# make the patch request
patch_url = "{0}/api/SIP/processmetadata/{1}/{2}/{3}".format(
    site,
    dest_sip_id,
    dest_step_id,
    dest_user_id
)
print('patching', patch_url)
r = requests.patch(
    patch_url,
    json=dest_process_metadata,
    verify=False
)
#print(r)

# Once the Process Metadata has been copied from the JSON
# visit the page and saveContinue()
# this checks the process metadata

driver.get(f"{site}/Steps/Process/{dest_sip_id}/{dest_step_id}")
# wait for this button to appear
driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='process-metadata-form']/div[3]/button")))

driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "step-complete-checkbox"))).click()
driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='page-content-wrapper']/div[2]/div[2]/nav/button[3]"))).click()
print(f"Process Metadata complete for {site}/Steps/Process/{dest_sip_id}/{dest_step_id}")

# Wait for the search box on the Search SAMI Recordings page
# before starting next function otherwise you get an error modal dialog
driver.wait.until(EC.visibility_of_element_located((By.ID, "searchBox")))
time.sleep(1)