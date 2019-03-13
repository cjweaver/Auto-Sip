import datetime
import time
import openpyxl
import os
import json
import sys
from tkinter import *
from tkinter import filedialog
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
#from login import site, user, password
import getpass
import itertools, sys
import logging

# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
import urllib3
urllib3.disable_warnings()

#site="https://avsip.ad.bl.uk"
site="https://v12l-avsip.ad.bl.uk:8445"

log_name = "Auto-SIP " + datetime.datetime.today().strftime("%B %d %Y__%H-%M-%S") +".log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(message)-12s', datefmt='%m-%d %H:%M')
file_handler = logging.FileHandler(log_name)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)




# #Set up webdriver
# driver = webdriver.Chrome()
# driver.maximize_window()
# #driver.implicitly_wait(10)
# driver.wait = WebDriverWait(driver, 120)


class TooManyRetries(Exception):
    pass

retry_count = 0

   


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
                logger.warning("Unable to navigate to correct web page %s", error, exc_info=1)
        except UnexpectedAlertPresentException:
            driver.switch_to.alert.accept()

# Cmdline argument to switch to storing these in a textfile??       
def ADloginDetails():
    global user
    global password
    print("\n********************************************************************************")
    print("\nLogin\n")
    user = input("Please enter your AD Username: ")
    password = getpass.getpass(prompt="Please enter your password: ")
    print("\n********************************************************************************\n")
    return user, password


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
    # catch the modal here
    #
    #
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
    print("\n********************************************************************************")
    print("\nSAMI Search")
    logger.info(sami_item_text)
    

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
        filedate = datetime.datetime.strptime((file.partition("Modified: ")[2]), "%a, %d %b %Y %H:%M:%S %Z")
        list_of_dates.append(filedate.date())
    tally_dates = [[x, list_of_dates.count(x)] for x in set(list_of_dates)]
    tally_dates = sorted(tally_dates, key = lambda date: date[1])
    return tally_dates[-1][0]


def source_files(directory, file_patterns, sip_id, pm_date):
    # First check this is the right page
    # Arrive here by clicking "Complete" in previous page
    handle_logout("Select Files", "/Steps/Select/", sip_id)

    print("\n********************************************************************************")
    print("\nSelect Source Files")

    path =f"\\{directory}"
    logger.debug("Loading files from %s", directory)

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
    global file_names
    file_names = []
    for file_pattern in file_patterns:
        file_pattern_box.clear()
        file_pattern_box.send_keys(file_pattern)
        file_pattern_box.send_keys(Keys.TAB)
        driver.find_element_by_xpath("//*[@id='main-content']/div[3]/div/button").click()
        if len(file_patterns) != 1:
            time.sleep(4)
        driver.wait.until(EC.presence_of_element_located((By.ID, "accordion")))
    
        # Throw an AssertionError if no files are found
        any_files = driver.find_element_by_xpath('//*[contains(text(), "dirs")]')
        assert (not "0 files" in any_files.text), f"Sorry no files found with filename {file_pattern} at {path}"

        # The files are displayed in a <ul>
        # There are two elements with class "list-group sami-container"
        fileResults = driver.find_elements_by_class_name("sami-container")
        files = fileResults[1].find_elements_by_tag_name("li")
    
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
                if field.endswith(".wav") or field.endswith(".WAV"):
                    filename = field
                    #print(filename)
                    file_names.append(filename)
            item.click()
        logger.info(f"Found {len(file_names)} file(s)")
  
    #logger.info("Here is the list of files: %s", *file_names) doesn't work with *var
    # https://stackoverflow.com/questions/51477200/how-to-use-logger-to-print-a-list-in-just-one-line-in-python
    logger.info("Here is the list of files: {}".format(' '.join(map(str, file_names))))
    
    # These need to sanitised a bit - strip whitespace, captalise etc
    # As they are coming from the spreadsheet.
    if pm_date == "No":
        # Use the date specified in the reference SIP
        process_metadata_date = False
        print("\nUsing the date from the reference SIP")

    elif pm_date == "Yes":
        # use file creation date
        process_metadata_date = date_tally(file_text)
        print("\nusing the date taken from the file's modification date")
    else:
        if isinstance(pm_date, datetime.datetime):
            process_metadata_date = pm_date
        else:
            logger.debug(f"{pm_date} is not a valid date. Defaulting to file creation date")
            process_metadata_date = date_tally(file_text)
    
    logger.info(f"The date for the Process Metadata will be {process_metadata_date}")
    
    print("If you wish to specifiy another date, use the 'Date' column in the SIPS.xlsx")


    time.sleep(1)
    saveContinue()
    #url = driver.current_url
    return process_metadata_date


def analysis(sip_id):
    # File Analysis, Validation, and Transformation
    # Script Timesout here due to the unknown lenght of time the analysis takes
    # Sometimes you are dumped at the login screen
    handle_logout("File Analysis", "/Steps/Analyze/", sip_id)
     
    # Copy All Files (Overwrite)
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='copy-files-buttons']/div/div/div/button[1]"))).click()
    analysis_url = driver.current_url
    print("\n********************************************************************************")
    print("\nFile Analysis, Validation, and Transformation")
    logging.debug(f"Current analysis page is: {analysis_url}")
    time.sleep(2)

    print("\nProcessing files")
    
    # Return to the home page to avoid any issues with stale UI elements on the File Analysis, Validation, and Transformation page.
    driver.get(site)

    def retry_analysis(failure, page, sip_id):
        global retry_count
        if retry_count > 2:
            raise TooManyRetries(f"A file keeps failing the {failure} process")
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
            # THIS is not finsished!!!
            logger.debug(f"Number of failed files {len(failed_files)}")
            for failure in failed_files:
                button = failure.find_element_by_tag_name('button')
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
                    logger.debug(f'{j["Files"][i]["Name"]} has failed analysis')
                    retry_analysis("Analysis", analysis_url, sip_id)
                elif j["Files"][i]["HasCopyToServerFailed"]:
                    logger.debug(f'{j["Files"][i]["Name"]} has failed to copy to the server')
                    retry_analysis("Copy", analysis_url, sip_id)
                elif j["Files"][i]["HasTransformationFailed"]:
                    print(f'{j["Files"][i]["Name"]} has failed transformation')
                    retry_analysis("Transform", analysis_url, sip_id)

        # If the SIP tool cannot connect to the SQL server it returns a JSON with an error message
        else: 
            if "An error has occurred." in j["Message"]:
                logger.debug("There is problem connecting to the SIP database")
        wait_with_spinner(30)
        
      
    
    analysis_json_update = j['StepStates'][2]
    analysis_json_update['ModifiedBy'] = j['UserId']
    analysis_json_update['ModifiedByUsername'] = j['UserName']
    analysis_json_update['Status'] = 1
    analysis_json_update['Complete'] = True
    analysis_json_update['Modified'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

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
    

    

def physical_structure(physical_structure_url, sip_id, item_format):
    # Haven't arrived via clicking "Continue" from last step
    # so...
    driver.get(site + "/" + physical_structure_url)
    handle_logout("Physical Structure", "/Steps/Physical/", sip_id)

    print("\n********************************************************************************")
    print("\nPhysical Structure")

    s1 = ui.Select(driver.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="demo1"]/div/div[1]/div[1]/select'))))
    # s1 = ui.Select(driver.find_element_by_xpath('//*[@id="demo1"]/div/div[1]/div[1]/select'))
    # select disc from the dropdown
    # The physical structure is curently hardcoded for CDRs only. Need to read the format from the XL sheet.
    print(f"\nPhysical structure: {item_format}")
    s1.select_by_visible_text(item_format)
    #s1.select_by_index(2)
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
    
    # Save and mark as step complete but don't click continue to avoid next page modal
    driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "nav-save-button"))).click()
    driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "step-complete-checkbox"))).click()

    print("Complete.")
    

    time.sleep(5)


def copy_processmetadata(src_sip_id, dest_sip_id, speed, eq, notes, process_metadata_date):
    # get information for the src
    src_url = "{0}/api/SIP/{1}".format(site, src_sip_id)
    #DEBUG print("getting information for sip", src_sip_id)
    src_req = requests.get(src_url, verify=False)
    src_req.encoding = src_req.apparent_encoding
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

    # Updates all the dates in the Process MD 
    # to datetime from datetally()
    if process_metadata_date == False:
        print("Using dates specified in reference SIP process metadata")
    else:
        for c in d['processMetadata'][0]['children']:
            c['date'] = process_metadata_date.strftime("%Y-%m-%d")
            #c['date'] = process_metadata_date.strftime("%Y-%m-%dT%H:%M:%S")
        
    # and adds a note/comment on the last device
    last_proc = d['processMetadata'][0]['children'][-1]
    last_proc['devices'][-1]['notes'] = notes

    # The use of else in a for loop is unusual! 
    # See https://stackoverflow.com/questions/9979970/why-does-python-use-else-after-for-and-while-loops
    # Sets the speed of the Tape Recorder
    if speed != None:
        for node in d['processMetadata'][0]['children']:
            if node['processType'] == "Migration":
                    for _ in node['devices']:
                            if _['deviceType'] == "Tape recorder":
                                _['parameters']['Tape recorder']['replaySpeed']['value'] = speed
                                # break
                            # else:
                            #     raise KeyError(f"Process Metadata doesn't appear to have a tape recorder to set the speed of {speed}")
    # Set the EQ type of the tape Recorder
    if eq != None:
        for node in d['processMetadata'][0]['children']:
            if node['processType'] == "Migration":
                    for _ in node['devices']:
                            if _['deviceType'] == "Tape recorder":
                                _['parameters']['Tape recorder']['equalisation']['value'] = eq
                                # break
                            # else:
                            #     raise KeyError(f"Process Metadata doesn't appear to have a tape recorder to set the equalisation type of {eq}")


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
    # visit the page and step complete & continue
    # this checks the process metadata

    driver.get(f"{site}/Steps/Process/{dest_sip_id}/{dest_step_id}")
    handle_logout("Process Metadata", "/Steps/Process/", dest_sip_id)
    
   # Page is ready when this dropdown for custom SIP metadata is available
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='process-metadata-form']/div[3]/button")))
    driver.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "step-complete-checkbox"))).click()
    driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='page-content-wrapper']/div[2]/div[2]/nav/button[3]"))).click()



    print("\n********************************************************************************")
    print("\nProcess Metadata")
    print("\n")
    logger.info(f"Process Metadata complete for {site}/Steps/Process/{dest_sip_id}/{dest_step_id}")
    
    # Wait for the search box on the Search SAMI Recordings page
    # before starting next function otherwise you get an error modal dialog
    driver.wait.until(EC.visibility_of_element_located((By.ID, "searchBox")))
    time.sleep(1)
    
   

def getSIPStobuild():
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
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
        shelfmark, grouping, filename, directory, item_format, pm_date, reference_sip, speed, eq, notes = row
        if shelfmark.value == None:
            break
        if filename.value == None:
            #print(row)
            #print("This is the current shelfmark", shelfmark.value)
            # Filemask for old filename schema
            # Should probably do this later?
            # NEED To write something proper here!!!
            #filemask = shelfmark.value[-4:] + "X"
            # Need removed zero padding from shelfmark
            filemask = (shelfmark.value).replace("/", "-")
            filemask = [filemask.replace(" ", "-")]
        else:
            filemask = filename.value.split(";")
        l = [shelfmark.value, grouping, directory.value, filemask, item_format.value, pm_date.value, reference_sip.value, speed.value, eq.value, notes.value]
        SIPS.append(l)
    return SIPS

def main():
    #root = Tk()
    #root.filename = filedialog.askopenfilename(initialdir="c:\\", title="Select SIP list")
    #print(root.filename)
    user, password = ADloginDetails()

    #Set up webdriver
    global driver
    if getattr( sys, 'frozen', False ) :
        driver = webdriver.Chrome(os.path.join(sys._MEIPASS, "bin", "chromedriver.exe"))
    else:
        driver = webdriver.Chrome()
    driver.maximize_window()
    #driver.implicitly_wait(10)
    driver.wait = WebDriverWait(driver, 120)


    SIP_tool_login(site, user, password)
    SIPS = getSIPStobuild()
    failed_sips = []
    print()
    # DEBUG print(SIPS)
    global retry_count
    for sip in SIPS:
        retry_count = 0
        shelfmark, grouping, directory, filemasks, item_format, pm_date, reference_sip, speed, eq, notes = sip
        print("\n\n\n\n\n")
        print("\n********************************************************************************")
        print("Creating SIP")
        logger.info(f"Procesing current shelfmark {shelfmark}")

        try:
            sip_id = createNewsip(shelfmark)
            logger.info(f"SIP ID for shelfmark {shelfmark} is {sip_id}")

            process_metadata_date = source_files(directory, filemasks, sip_id, pm_date)
            
            # elif pm_date == datetime take from the spreadsheet use that date for process metadata
            # else use tallydate() 

            physical_structure_url = analysis(sip_id)
            physical_structure(physical_structure_url, sip_id, item_format) #pass the physical structure??
            copy_processmetadata(reference_sip, sip_id, speed, eq, notes, process_metadata_date)
        except Exception as e:
            failed_sips.append((shelfmark + ":  " + str(e)))
            continue

    if len(failed_sips) == 0:
        print("\n********************************************************************************")
        logger.info("All SIPs completed.")
    else:
        print("\n********************************************************************************")
        print("The following SIPs did not complete sucessfully:\n", )
        print(*failed_sips, sep="\n")
        logger.debug("Failures: %s", failed_sips)
            


   
if __name__ == '__main__':
    main()