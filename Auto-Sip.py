from datetime import datetime
import time
import openpyxl
import os
import json
import warnings
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
import itertools, sys
import logging


class TooManyRetries(Exception):
    pass

retry_count = 0

#Set up webdriver
driver = webdriver.Chrome()
driver.maximize_window()
#driver.implicitly_wait(10)
driver.wait = WebDriverWait(driver, 120)


def handle_logout(page_title, step_url, sip_id=None):
        #driver.get(f"{site}{step_url}")
        try:
            assert page_title in driver.title, f"Wrong web page: Not {page_title}"
        except AssertionError as error:
            if 'Log in' in driver.title:
                SIP_tool_login(site, user, password, do_get=True)
                if page_title == "SAMI Search":
                    driver.get(f"{site}{step_url}")
                else:
                    r = requests.get(f"{site}/api/SIP/{sip_id}", verify=False)
                    # Take the requests response 'r' and convert to a Python dictionary
                    j = json.loads(r.text)
                    if "StepStates" not in j:
                        # DEBUG print("Got something funny back for sip_id", sip_id)
                        # DEBUG print(j)
                        raise Exception()
                    for item in j["StepStates"]:
                        if item["StepTitle"] == page_title:
                            step_id = item["StepStateId"]
                    driver.get(f"{site}{step_url}{sip_id}/{step_id}")
            else:
                print("I think this is wrong", error)
        except UnexpectedAlertPresentException:
            driver.switch_to.alert.accept()
        
         


def SIP_tool_login(site, user, password, do_get=True):
    # Login into the website
    if do_get:
        driver.get(f"{site}/Account/LoginAD")
    username_elem = driver.find_element_by_id("ADUserName")
    password_elem = driver.find_element_by_id("Password")

    username_elem.send_keys(user)
    password_elem.send_keys(password)
    password_elem.submit()

def saveContinue():
    driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "nav-save-button"))).click()
    driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "step-complete-checkbox"))).click()
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='page-content-wrapper']/div[2]/div[2]/nav/button[3]"))).click()

def createNewsip(shelfmark, grouping="None"):
    # Search SAMI for shelfmark
    driver.get(f"{site}/Steps/Search")
    handle_logout("SAMI Search", "/Steps/Search/")
    
    sip = driver.wait.until(EC.visibility_of_element_located((By.ID, "searchBox")))
    sip.click()
    sip.send_keys(shelfmark)
    driver.find_element_by_xpath("//*[@id='main-content']/div[1]/div[1]/button").click()
    # Wait until the 1st result is found before continuing
    driver.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "list-group-item")))
    # Select 1st found result
    # GROUPING How to deal with??
    SAMI_results = driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "list-group")))
    SAMI_items = SAMI_results.find_elements_by_tag_name("li")
    if len(SAMI_items) > 1:
        #driver.save_screenshot(f'{shelfmark}.png');
        # log list of SAMI results
        # Do something if more than one result
        for i, item in enumerate(SAMI_items):
            sami_item_text = item.text
            if sami_item_text.startswith(shelfmark):
                SAMI_items[i].click()
                break
            elif sami_item_text.startswith(grouping):
                SAMI_items[i].click()
    else:
        sami_item_text = SAMI_items[0].text
        SAMI_items[0].click()
    print("\n******************************************************************************************")
    print("\nSAMI Search")
    print(sami_item_text)
    

    # Create pSIP button
    driver.wait.until(EC.element_to_be_clickable((By.ID, "nav-create-button"))).click()
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[2]/nav/button[3]"))).click()
    # Return the sip_id
    url = driver.current_url
    return url.split('/')[-2]



def date_tally(filenames):
    """Strips modified date from list of file information strings and returns the most common date as a datetime object"""
    
    list_of_dates = []
    for file in filenames:
        filedate = datetime.strptime((file.partition("Modified: ")[2]), "%a, %d %b %Y %H:%M:%S %Z")
        list_of_dates.append(filedate.date())
    tally_dates = [[x, list_of_dates.count(x)] for x in set(list_of_dates)]
    tally_dates = sorted(tally_dates, key = lambda date: date[1])
    return tally_dates[-1][0]


def source_files(directory, file_pattern, sip_id):
    # First check this is the right page
    # Arrive here by clicking "Complete" in previous page
    handle_logout("Select Files", "/Steps/Select/", sip_id)

    path =f"\\{directory}"
    #path = f"\\Wildlife\\{directory}"

    # Choose the Source directory drop down and choose SOS_HLF
    # https://stackoverflow.com/questions/46988143/select-option-in-list-with-selenium-python
    s1 = ui.Select(driver.wait.until(EC.element_to_be_clickable((By.ID, 'currentSourceBox'))))
    #s1 = ui.Select(driver.find_element_by_id('currentSourceBox'))
    # Select another directory before the one you want to allow KnockoutJS to populate search box with the path.

    s1.select_by_index(0)
    time.sleep(1)
    s1.select_by_visible_text("\\\\p12l-nas6\\SOS_HLF")
    time.sleep(1)

    # click the "Current directory Box" dues to how KnockoutJS handles focus and clicks
    directory_box = driver.find_element_by_id("currentDirectoryBox")
    # focus on the box
    directory_box.click()
    # actually click the box
    directory_box.click()
    time.sleep(2)
    # directory_box.send_keys(Keys.CONTROL + "a");
    # directory_box.send_keys(Keys.DELETE);
    # time.sleep(2)
    # directory_box.send_keys(Keys.TAB)
    # directory_box.click()
    directory_box.send_keys(path)
    directory_box.send_keys(Keys.TAB)
    time.sleep(2)
    # if directory_box.value ==
        #else
        # Add some code to handle if the directory box doesn't clear and is a garbled 
    file_pattern_box = driver.find_element_by_xpath("//*[@id='filePatternBox']")
    file_pattern_box.click()
    # file_pattern will be differnt depending on old or new file name schema
    file_pattern_box.send_keys(file_pattern)
    file_pattern_box.send_keys(Keys.TAB)
    driver.find_element_by_xpath("//*[@id='main-content']/div[3]/div/button").click()
    try:
        driver.wait.until(EC.presence_of_element_located((By.ID, "accordion")))
    except:
        # Throw an exception if there are no files?
        print("Cannot find any files")
        # Could check the file path if no files are displayed.




    # The files are displayed in a <ul>
    # There are two elements with class "list-group sami-container"
    fileResults = driver.find_elements_by_class_name("sami-container")
    files = fileResults[1].find_elements_by_tag_name("li")
    global file_names
    file_names = []

    # Select all the files
    # Can use the "Add All" button in the new SIP tool
    # but this way we get file creation date to use in date_tally()
    file_text = []
    for item in files:
        file_text.append(item.text)
        text = item.text
        #print(text)
        text = text.splitlines()
        path_fields = text[0].split("\\")
        for field in path_fields:
            if field.endswith(".wav"):
                filename = field
                #print(filename)
        file_names.append(filename)
        item.click()
    
    print("\n******************************************************************************************")
    print("\nSelect Source Files")
    print("Found", len(file_names), "files")
    print("Here is the list of files", file_names)
    process_metadata_date = date_tally(file_text)
    print("The date for the Process Metadata will be", process_metadata_date)


    time.sleep(1)
    saveContinue()
    url = driver.current_url
    return process_metadata_date


def analysis(sip_id):
    # File Analysis, Validation, and Transformation
    # Script Timesout here due to the unknown lenght of time the analysis takes
    # Sometimes you are dumped at the login screen
    handle_logout("File Analysis", "/Steps/Analyze/", sip_id)
     
    # Copy All Files (Overwrite)
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='copy-files-buttons']/div/div/div/button[1]"))).click()
    analysis_url = driver.current_url
    print("\n******************************************************************************************")
    print("\nFile Analysis, Validation, and Transformation")
    print(f"Current analysis page is: {analysis_url}")
    time.sleep(2)

    print("\nProcessing files")
    
    # Return to the home page to avoid any issues with stale UI elements on the File Analysis, Validation, and Transformation page.
    driver.get(site)

    def retry_analysis(failure, page, sip_id):
        global retry_count
        if retry_count > 2:
            raise TooManyRetries()
        retry_count += 1
        driver.get(page)
        handle_logout("File Analysis", "/Steps/Analyze/", sip_id)
        if failure == "Analysis":
            # NEED to check if the DIV is collapesed or not otherwise script hangs.
            elem = driver.find_element_by_xpath("//a[@href='#analysis-failed-collapse']")
            if elem.get_attribute("aria-expanded") is None:
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#analysis-failed-collapse']"))).click()
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='analysis-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]"))).click()
            elif elem.get_attribute("aria-expanded") == 'false':
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#analysis-failed-collapse']"))).click()
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='analysis-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]"))).click()
            else:
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='analysis-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]"))).click()
            print("Retrying File Analysis.")
        elif failure == "Transform":
            # Unlike "Copy" or "Analysis click a single button doesn't restart the process for all files.
            # Therefore need to iterate over every button in the DIV
            elem = driver.find_element_by_xpath("//a[@href='#failed-transformation-files-collapse']")
            if elem.get_attribute("aria-expanded") is None:
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#failed-transformation-files-collapse']"))).click()
            else: 
                # elem.get_attribute("aria-expanded") == 'false'
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#failed-transformation-files-collapse']"))).click()
            # elem = driver.find_element_by_xpath('//*[@id="failed-transformation-files-collapse"]/div')
            failed_files = elem.find_elements_by_xpath("//*[@id='failed-transformation-files-collapse']/div")
            # //*[@id="failed-transformation-files-collapse"]/div/div[1]/button
            print(f"DEBUG: number of failed files {len(failed_files)}")
            for div in failed_files:
                print(div)
                button.click()
                time.sleep(1)
            print("Retrying Transformation.")
        else: 
            # failure == "Copy":
            elem = driver.find_element_by_xpath("//a[@href='#copy-failed-collapse']")
            if elem.get_attribute("aria-expanded") is None:
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#copy-failed-collapse']"))).click()
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='copy-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]"))).click()
            elif elem.get_attribute("aria-expanded") == 'false':
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#copy-failed-collapse']"))).click()
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='copy-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]"))).click()
            else:
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='copy-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]"))).click()
            print("Retrying copying file(s) to the server.")
        time.sleep(5)
        driver.get(site)

    while True:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = requests.get(f"{site}/api/SIP/" + sip_id, verify=False)
        j = r.json()
        if j["HasCompletedAllTransformations"]:
            print("\n Analysis Page has finished. We can continue")
            break

        # Search the JSON for failed Analysis/Copy or transforms and retry
        elif j["NavigationState"]["NavigationSteps"][2]["Complete"] == False:
            for i, item in enumerate(j["Files"]):
                if j["Files"][i]["HasAnalysisFailed"]:
                    print(j["Files"][i]["Name"], "has failed analysis")
                    retry_analysis("Analysis", analysis_url, sip_id)
                elif j["Files"][i]["HasCopyToServerFailed"]:
                    print(j["Files"][i]["Name"], "has failed to copy to the server")
                    retry_analysis("Copy", analysis_url, sip_id)
                elif j["Files"][i]["HasTransformationFailed"]:
                    print(j["Files"][i]["Name"], "has failed transformation")
                    retry_analysis("Transform", analysis_url, sip_id)

        # If the SIP tool cannot connect to the SQL server it returns a JSON with an error message
        else: 
            if "An error has occurred." in j["Message"]:
                print("There is problem connecting to the SIP database")
        wait_with_spinner(30)
        
      
    
    analysis_json_update = j['StepStates'][2]
    analysis_json_update['ModifiedBy'] = j['UserId']
    analysis_json_update['ModifiedByUsername'] = j['UserName']
    analysis_json_update['Status'] = 1
    analysis_json_update['Complete'] = True
    analysis_json_update['Modified'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    user_id = j['UserId']

    patch_url = "{0}/api/SIPs/SIP/State/{1}".format(
        site,
        user_id
    )
    # DEBUG print('patching', patch_url)
    # DEBUG print(analysis_json_update)
    
    r = requests.patch(
        patch_url,
        data=json.dumps(analysis_json_update),
        headers={'Content-Type': 'application/json'},
        verify=False
    )
    #print(r.content)
    # DEBUG print("This is what's returned from analysis", j['NavigationState']['NavigationSteps'][2]['NextStepPath'])
    return j['NavigationState']['NavigationSteps'][2]['NextStepPath']


def wait_with_spinner(seconds):
    seconds *= 10
    spinner = itertools.cycle(['-', '\\', '|', '/'])
    for _ in range(seconds):
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')
    sys.stdout.write(" ")
    sys.stdout.write('\b')
    

    

def physical_structure(physical_structure_url, sip_id):
    # Haven't arrived via clicking "Continue" from last step
    # so...
    driver.get(site + "/" + physical_structure_url)
    handle_logout("Physical Structure", "/Steps/Physical/", sip_id)

    s1 = ui.Select(driver.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="demo1"]/div/div[1]/div[1]/select'))))
    # s1 = ui.Select(driver.find_element_by_xpath('//*[@id="demo1"]/div/div[1]/div[1]/select'))
    # select disc from the dropdown
    # The physical structure is curently hardcoded for CDRs only. Need to read the format from the XL sheet.
    s1.select_by_index(2)
    time.sleep(1)

    for i in range((len(file_names)) - 1):
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

    print("\n******************************************************************************************")
    print("\nPhysical Structure")
    print("Complete.")
    

    time.sleep(5)


def copy_processmetadata(src_sip_id, dest_sip_id, notes, process_metadata_date):
    # get information for the src
    src_url = "{0}/api/SIP/{1}".format(site, src_sip_id)
    #DEBUG print("getting information for sip", src_sip_id)
    src_req = requests.get(src_url, verify=False)
    src_json = src_req.json()
    
    # get information for the dest
    dest_url = "{0}/api/SIP/{1}".format(site, dest_sip_id)
    # DEBUG print("getting information for sip", dest_sip_id)
    dest_req = requests.get(dest_url, verify=False)
    dest_json = dest_req.json()
    
    # get title of dest
    dest_title = dest_json['Title']
    
    # update title for the process metadata
    # DEBUG print("setting dest_title to", dest_title)
    d = json.loads(src_json['ProcessMetadata'])
    d['processMetadata'][0]['text'] = dest_title

    # Updates all the dates in the Process MD to datetime.now()
    # and adds a note/comment on the last device
    for c in d['processMetadata'][0]['children']:
        c['date'] = process_metadata_date.strftime("%Y-%m-%dT%H:%M:%S")
    last_proc = d['processMetadata'][0]['children'][-1]
    last_proc['devices'][-1]['notes'] = notes

    dest_process_metadata = json.dumps(d)
    
    # get the dest user id
    dest_user_id = dest_json['UserId']
    # DEBUG print('dest user_id is', dest_user_id)
    
    # get the dest step state id for processmetadata
    for x in dest_json['StepStates']:
        if x['StepTitle'] == "Process Metadata":
            dest_step_id = x['StepStateId']
            break
    else:
        raise KeyError
    # DEBUG print('dest step id is', dest_step_id)
    
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

    print("\n******************************************************************************************")
    print("\nProcess Metadata")
    print("\n")
    print(f"Process Metadata complete for {site}/Steps/Process/{dest_sip_id}/{dest_step_id}")
    
    # Wait for the search box on the Search SAMI Recordings page
    # before starting next function otherwise you get an error modal dialog
    driver.wait.until(EC.visibility_of_element_located((By.ID, "searchBox")))
    time.sleep(1)
    
   

def getSIPStobuild():
    desktop = os.path.join(os.path.expanduser('~'), 'Documents', 'siptool')
    print(f"Reading the SIPS.xlsx spreadsheet from {desktop}")
    os.chdir(desktop)

    wb = openpyxl.load_workbook('SIPS.xlsx')
    ws = wb.active
    rows = ws.rows
    #print(rows)
    SIPS = []
    next(rows)
    # Skip first row
    for row in rows:
        shelfmark, grouping, directory, item_format, reference_sip, notes = row
        if shelfmark.value == None:
            break
        #print(row)
        #print("This is the current shelfmark", shelfmark.value)
        # Filemask for old filename schema
        # Should probably do this later?
        # NEED To write something proper here!!!
        #filemask = shelfmark.value[-4:] + "X"
        # Need removed zero padding from shelfmark
        filemask = (shelfmark.value).replace("/", "-")
        filemask = filemask.replace(" ", "-")
        l = [shelfmark.value, grouping, directory.value, filemask, item_format.value, reference_sip.value, notes.value]
        SIPS.append(l)
    return SIPS

def main():
    SIP_tool_login(site, user, password)
    SIPS = getSIPStobuild()
    print()
    # DEBUG print(SIPS)
    global retry_count
    for sip in SIPS:
        retry_count = 0
        shelfmark, grouping, directory, filemask, item_format, reference_sip, notes = sip
        print(f"Procesing current shelfmark {shelfmark}")

    # shelfmark = "W1CDR0000211"
    # directory = "dir_52"
    # filemask = "0211X"
        try:
            sip_id = createNewsip(shelfmark)
            print(f"SIP ID for shelfmark {shelfmark} is {sip_id}")
            process_metadata_date = source_files(directory, filemask, sip_id)
            physical_structure_url = analysis(sip_id)
            physical_structure(physical_structure_url, sip_id) #pass the physical structure??
            copy_processmetadata(reference_sip, sip_id, notes, process_metadata_date)
        except Exception as e:
            print("An exception occurred processing", shelfmark, e)
            continue
        


    # COMMON ERROR
    # selenium.common.exceptions.UnexpectedAlertPresentException: Alert Text: None
    # Message: unexpected alert open: {Alert text : Unable to update SIP current step state}
    #   (Session info: chrome=70.0.3538.77)
    #   (Driver info: chromedriver=2.42.591088 (7b2b2dca23cca0862f674758c9a3933e685c27d5),platform=Windows NT 6.1.7601 SP1 x86_64)

if __name__ == '__main__':
    main()