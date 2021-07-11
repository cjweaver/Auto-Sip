import requests
import json
import time
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

# # r = requests.get("https://avsip.ad.bl.uk/api/SIP/19974", verify=False)
# r = requests.get("https://v12l-avsip.ad.bl.uk:8444/api/SIP/377", verify=False)
# j = r.json()

# Set up webdriver
driver = webdriver.Chrome()
driver.maximize_window()
# driver.implicitly_wait(10)
driver.wait = WebDriverWait(driver, 120)


def SIP_tool_login(site, user, password):
    # Login into the website
    driver.get(f"{site}/Account/LoginAD")
    username_elem = driver.find_element_by_id("ADUserName")
    password_elem = driver.find_element_by_id("Password")

    username_elem.send_keys(user)
    password_elem.send_keys(password)
    password_elem.submit()


def retry_analysis(failure, page):
    driver.get(page)
    if failure == "Analysis":
        # NEED to check if the DIV is collapesed or not otherwise script hangs.
        elem = driver.find_element_by_xpath("//a[@href='#analysis-failed-collapse']")
        if elem.get_attribute("aria-expanded") is None:
            driver.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@href='#analysis-failed-collapse']")
                )
            ).click()
            driver.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//*[@id='analysis-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]",
                    )
                )
            ).click()
        elif elem.get_attribute("aria-expanded") == "false":
            driver.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@href='#analysis-failed-collapse']")
                )
            ).click()
            driver.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//*[@id='analysis-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]",
                    )
                )
            ).click()
        else:
            driver.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//*[@id='analysis-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]",
                    )
                )
            ).click()
        print("Retrying File Analysis.")
    elif failure == "Transform":
        # Unlike "Copy" or "Analysis click a single button doesn't restart the process for each file.
        # Therefore need to iterate over every button in the DIV
        elem = driver.find_element_by_xpath(
            "//a[@href='#failed-transformation-files-collapse']"
        )
        if elem.get_attribute("aria-expanded") is None:
            driver.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@href='#failed-transformation-files-collapse']")
                )
            ).click()
        elif elem.get_attribute("aria-expanded") == "false":
            driver.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@href='#failed-transformation-files-collapse']")
                )
            ).click()
        else:
            elem = driver.find_element_by_xpath(
                '//*[@id="failed-transformation-files-collapse"]/div'
            )
            failed_files = elem.find_elements_by_tag_name("button")
            for button in failed_files:
                button.click()
                time.sleep(1)
            # driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='failed-transformation-files-collapse']/div/div/button"))).click()
        print("Retrying Transformation.")
    else:
        # failure == "Copy":
        elem = driver.find_element_by_xpath("//a[@href='#copy-failed-collapse']")
        if elem.get_attribute("aria-expanded") is None:
            driver.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@href='#copy-failed-collapse']")
                )
            ).click()
            driver.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//*[@id='copy-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]",
                    )
                )
            ).click()
        elif elem.get_attribute("aria-expanded") == "false":
            driver.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@href='#copy-failed-collapse']")
                )
            ).click()
            driver.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//*[@id='copy-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]",
                    )
                )
            ).click()
        else:
            driver.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//*[@id='copy-failed-collapse']/div[2]/div/div/div[1]/div/div/button[1]",
                    )
                )
            ).click()
        print("Retrying copying file(s) to the server.")


SIP_tool_login(site, user, password)
# driver.get("https://avsip.ad.bl.uk/Steps/Analyze/19974/159683")
driver.get("https://v12l-avsip.ad.bl.uk:8445/Steps/Select/208/1562")
time.sleep(10)


# for i, item in enumerate(j["Files"]):
#     if j["Files"][i]["HasAnalysisFailed"]:
#         print(j["Files"][i]["Name"], "has failed analysis")
#         retry_analysis("Analysis")
#     elif j["Files"][i]["HasCopyToServerFailed"]:
#         print(j["Files"][i]["Name"], "has failed to copy to the server")
#         retry_analysis("Copy")
#     elif j["Files"][i]["HasTransformationFailed"]:
#         print(j["Files"][i]["Name"], "has failed transformation")
#         retry_analysis("Transform")


# # Do we need to update the JSON each time we call retry_analysis?
# # //*[@id="failed-transformation-files-collapse"]/div/div[2]/button
# #failed-transformation-files-collapse

zero_files = (
    driver.find_element_by_xpath('//span[@data-bind="text: currentDirectoryText"]')
).text
print(zero_files)
