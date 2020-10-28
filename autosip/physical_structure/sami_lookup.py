import requests
import xml.etree.ElementTree as ET
import autosip.helpers.config as config

ns = {'default':'http://schemas.sirsidynix.com/symws/standard'}


def get_title_id(sip_id):

    r = requests.get(f"{config.site}/api/SIP/{sip_id}", verify=False)
    if r.reason == 'Not Found':
        raise Exception(f'Error Cannot find a SIP with ID number {sip_id}')
    title_id = r.json()['SamiTitleId']
    return title_id


def get_SAMI_xml(titleID):

    url = config.SAMI_API.format(CLIENT_ID = config.CLIENT_ID, titleID = titleID)
    r = requests.get(url, verify=False)
    if r.reason == 'Not Found':
        raise Exception(f'Error Cannot find a SAMI record with title ID {titleID}')
    return r.text


def multiple_callnumbers(SAMI_XML):
    root = ET.fromstring(SAMI_XML)
    if len(root.findall("default:TitleInfo/default:CallInfo", ns)) > 1:
        return True
    return False   


def shelfmark_order(SAMI_XML):
    root = ET.fromstring(SAMI_XML)
    return [shelfmark.text for shelfmark in root.findall("default:TitleInfo/default:BibliographicInfo/default:MarcEntryInfo/[default:entryID='087']/default:text", ns)]


def contains_subshelfmarks(shelfmark_order):

    sub_shelfmarks = False

    for shelfmark in shelfmark_order:
        if len(shelfmark.split("-")) > 1:
            sub_shelfmarks = True
    return sub_shelfmarks



# titleID = get_title_id(897)
# # titleID = 4015467
# SAMI_XML = get_SAMI_xml(titleID)
# print(multiple_callnumbers(SAMI_XML))
# print(shelfmark_order(SAMI_XML))
# print(titleID)




