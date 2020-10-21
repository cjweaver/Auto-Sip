import copy
from itertools import groupby 
import json
import re
import requests
import autosip.helpers.config as config



# This is a list of Originators ("The first field in the filename must record the ‘originator’ 
# – a record of where the digital file was digitised; in this case, the relevant institution. ")
#  Ideally this should be pulled from an external config file
originators = [
    "HOYFM", 
    "BL",
    "AP",
    "NRO",
    "NLS",
    "UOL",
    "TK",
    "TWA",
    "NLW",
    "LMA",
    "BC",
    "TK",
    "LMA"
]

phys_structure = {
    "_MDARK": None,
    "_deleted": None,
    "nodeId": 0,
    "text": None,
    "type": "node",
    "desc": "PhysicalResource",
    "invalid": None,
    "rights": "UNASSIGNED^^Unassigned Copyright Status",
    "rightsHolder": "The British Library",
    "_deletedNodes": [],
    "_deletedRanges": [],
    "children": [],
    "recordingSurfaces": None,
    "files": None,
    "counterRange": 0,
    "counterFile": 0,
    "counterNode": 0
}

phys_item = {
    "_MDARK": None,
    "_deleted": None,
    "nodeId": 0,
    "text": "",
    "type": "node",
    "desc": None,
    "invalid": None,
    "rights": None,
    "children": [],
    "recordingSurfaces": [],
    "files": []
}

phys_side = {
    "_MDARK": None,
    "_deleted": None,
    "nodeId": 0,
    "text": "",
    "type": "recording-surface",
    "desc": "Side",
    "invalid": None,
    "rights": None,
    "children": None,
    "recordingSurfaces": None,
    "files": []
}

phys_file = {
    "nodeId": 0,
    "type": "file",
    "desc": "File",
    "text": None,
    "fileId": None,
    "fId": None,
    "ranges": [],
    "invalid": None
}



def get_pSIP_files_json(sip_id):
    """GET a JSON object representing the audio stored in the pSIP from
    api/SIP/Files/{sip_id}.

    Args:
        sip_id (int): pSIP ID number

    Raises:
        Exception: "Not Found" HTTP Error 404. The requested resource is not found

    Returns:
        dict: The JSON encoded response from the SIP tool
    """

    url = f"{config.site}/api/SIP/Files/{sip_id}"

    r = requests.get(url, verify=False)
    if r.reason == 'Not Found':
        raise Exception(f'Physical Structure: Error Cannot find a SIP with ID number {sip_id}')
    elif r.text == '[]':
        raise Exception(f'Physical Structure: Error. No files have been added to this pSIP ID {sip_id}')
    return r.json()


def get_pSIP_json(sip_id):
    """GET a JSON object representing the pSIP from
    api/SIP/{sip_id}.

    Args:
        sip_id (int): pSIP ID number

    Raises:
        Exception: "Not Found" HTTP Error 404. The requested resource is not found

    Returns:
        dict: The JSON encoded response from the SIP tool
    """

    url = f"{config.site}/api/SIP/{sip_id}"

    r = requests.get(url, verify=False)
    if r.reason == 'Not Found':
        raise Exception(f'Error Cannot find a SIP with ID number {sip_id}')
    return r.json()


def shelfmark_from_file_json(file_json):
    """Get the shelfmark from the filename stored at file_json['Name']

    Args:
        file_json (dict): A dict object representing a single 'File' JSON 
        from the collection of File JSON objects retreived 
        by GET api/SIP/Files/{sip_id}

    Returns:
        str: A single shelfmark that the file name represents e.g. 'C604-1' from 'BL_C604-1_s1_f01_v1.wav'
    """
    filename_parts = [fn_part for fn_part in file_json['Name'].split('_') if fn_part not in originators]
    shelfmark = list(filter(lambda filename: re.search("^(?![isfvISFV]{1}[0-9]+)[a-zA-Z0-9-]{1,}", filename), filename_parts))[0]
    return shelfmark


def filter_sub_shelfmarks(shelfmark, shelfmark_order):
    """Check the shelfmark against the list of 087 fields from SAMI for sub-shelfmarks

    Args:
        shelfmark (str): Single shelfmark e.g. "C609/2"
        shelfmark_order (list): list of shelfmarks as strings e.g. ['C609-01', 'C609-09', 'C609-25']

    Returns:
        str: main shelfmark with only one slash e.g. WA 2000/021 as opposed to WA 2000/021/023
    """

    if len(shelfmark.split("-")) > 1:
        for mark in shelfmark_order:
            if shelfmark.startswith(mark):
                return mark
    else:
        return shelfmark




def physical_items_from(files_json, sip_id, item_format, sip_text, shelfmark_order):
    """Create the physical structure

    Args:
        files_json (dict)
        sip_id (int): The ID for the pSIP
        item_format (str): The physical format of the item. Must be "Cylinder", "Disc", "Sheet", "Solid State" or "Tape"
        sip_text (str): The text from the SAMI title. Stored in SIP['Text'] e.g 'C604/170; 169; 172; 171, Minehead Hobby Horse'
        shelfmark_order (list): The correct order of shelfmarks as a list of strings e.g. ['C604-170', 'C604-169', 'C604-172', 'C604-171']

    Returns:
        physical_struct (dict): Representing the physical arrangement of all items in the pSIP (carriers, sides and files)

    """

    physical_items = {key:{key: list(group) for key, group in groupby(group, lambda sub_group: shelfmark_from_file_json(sub_group))} for key, group in groupby(files_json, lambda file_json: filter_sub_shelfmarks(shelfmark_from_file_json(file_json), shelfmark_order))}


    


    # # Match SAMi shelfmarks with filename shelfmarks
    # shelfmark_order = [i.replace('/', '-') for i in shelfmark_order]

    # # grouby key is either proper shelfmark match or partial due to subshelfmark
    # groupby_key = shelfmark_from_file_json

    # # Create a dict grouping the JSON objects by shelfmark e.g. 'C8-1': [{'AVTransformationMos...uccessful': {...}
    # physical_items = {key:list(group) for key, group in groupby(files_json, lambda file_json: groupby_key(file_json))}
    
    counterNode = 0
    counterFile = 0

    current_structure = copy.deepcopy(phys_structure)
    current_structure['text'] = sip_text

    for shelfmark in shelfmark_order:
        print("\n", shelfmark)

        for item in list(physical_items[shelfmark]): 
            print(item)
            sides = {key:list(group) for key, group in groupby(physical_items[shelfmark][item], lambda file_json: re.findall(r's\d', file_json["Name"])[0])}
        
            counterNode += 1
            current_item = copy.deepcopy(phys_item)
            current_item['nodeId'] = counterNode
            current_item['desc'] = item_format
            # # Create a dict grouping the current shelfmark by sides e.g. sides: {'s1': [{'AVTransformations...}], 's2': [{'AVTransformations...}]}
            # sides = {key:list(group) for key, group in groupby(physical_items[shelfmark], lambda file_json: re.findall(r's\d', file_json["Name"])[0])}
            for side in sides:
                print("\t", side)
                counterNode += 1
                current_side = copy.deepcopy(phys_side)
                current_side['nodeId'] = counterNode
                for file in sides[side]:
                    print(f"\t\t{file['Name']}")
                    counterNode += 1
                    counterFile += 1
                    current_file = copy.deepcopy(phys_file)
                    current_file['nodeId'] = counterNode
                    current_file['fId'] = f'file{str(counterFile).zfill(3)}'
                    current_file['fileId'] = file['FileId']
                    current_file['text'] = f"{file['Name']} {file['Duration']}"
                    current_side['files'].append(current_file)
                current_item['recordingSurfaces'].append(current_side)
            current_structure['children'].append(current_item)
            current_structure['counterFile'] = counterFile
            current_structure['counterNode'] = counterNode
    return current_structure


def patch_physical_structure(sip_id, physical_structure, step_state_id, user_id):
    """PATCH the pSIP with the physical structure created by physical_items_from()
     at the endpoint: PATCH api/SIP/physicalstructure/{sip_id}/{step_state_id}/{user_id}      

    Args:
        sip_id (int): The ID for the pSIP
        physical_structure (dict): The physical structure of the pSIP in JSON format
        step_state_id (int): The stepStateId where 'StepTitle' == 'Physical Structure'
        user_id (str): The hex string stored in the pSIP under: 'UserId'

    Raises:
        Exception: [description]

    Returns:
        [type]: [description]
    """

    url = f'{config.site}/api/SIP/physicalstructure/{sip_id}/{step_state_id}/{user_id}'
    phys_array = []
    phys_array.append(physical_structure)
    body = {"Id": sip_id, "PhysicalStructure": json.dumps(phys_array)}
    r = requests.patch(url, json=body, verify=False)
    

def order_of_items(shelfmark_order, files_json):
    # Do the files
    pass


def shelfmarks_to_filename_standard(shelfmark_order):
    """Remove any characters in the shelfmarks not found in the filename standard

    Args:
        shelfmark_order (list): list of str representing the shelfmarks in SAMI

    Returns:
        list: List of str stripped of whitespace and '/' replaced with '-'
    """
    return [shelfmark.replace(" ", "").replace("/", "-") for shelfmark in shelfmark_order]





#  Patch the physical structure of the pSIP         

#     Args:
#         sip_id (int): The ID for the pSIP
#         physical_structure (dict): The physical structure of the pSIP in JSON format

#########################################     
# C609/11, Labour Oral History Project  #
# BL_C609-11-1_s1_f01_v1.wav
# BL_C609-11-1_s2_f01_v1.wav
# BL_C609-11-2_s1_f01_v1.wav
# BL_C609-11-1_s1_f01_v1.wav
########################################
# shelfmark_order = ['C609-11']
# pSIP_json = get_pSIP_json(44618)



sip_id = 66908
shelfmark_order = shelfmarks_to_filename_standard(['WA 2010/017/154'])
pSIP_json = get_pSIP_json(sip_id)

sip_text = pSIP_json['Title']
files_json = pSIP_json['Files']
user_id = pSIP_json['UserId']
physical_step_state_id = [i['StepStateId'] for i in pSIP_json['StepStates'] if i['StepTitle'] == 'Physical Structure'][0]


# # # # # pSIP_json = get_pSIP_json(66839)
# # # # shelfmark_order = ['C604-170', 'C604-169', 'C604-172', 'C604-171']
# shelfmark_order = ['C609-09', 'C609-25', 'C609-01']
# # # # shelfmark_order = shelfmarks_to_filename_standard(['WA 2000/021/023'])
# files_json = [
#             {'Name': 'BL_C609-01-01_s1_f01_v1.wav'},
#             {'Name': 'BL_C609-01-01_s1_f02_v1.wav'},
#             {'Name': 'BL_C609-01-01_s1_f03_v1.wav'}, 
#             {'Name': 'BL_C609-01-01_s2_f01_v1.wav'},
#             {'Name': 'BL_C609-01-02_s1_f01_v1.wav'},
#             {'Name': 'BL_C609-01-02_s2_f01_v1.wav'},
#             {'Name': 'BL_C609-01-03_s1_f01_v1.wav'},
#             {'Name': 'BL_C609-09_s1_f01_v1.wav'},
#             {'Name': 'BL_C609-25_s1_f01_v1.wav'}
#             ]

# physical_items = {key:{key: list(group) for key, group in groupby(group, lambda sub_group: shelfmark_from_file_json(sub_group))} for key, group in groupby(files_json, lambda file_json: filter_sub_shelfmarks(shelfmark_from_file_json(file_json), shelfmark_order))}

# for shelfmark in shelfmark_order:
#     for item in list(physical_items[shelfmark]): 
#         print(item)
#         sides = {key:list(group) for key, group in groupby(physical_items[shelfmark][item], lambda file_json: re.findall(r's\d', file_json["Name"])[0])}
#         for file in physical_items[shelfmark][item]:
#             print(file['Name'])

        

# my_group = groupby(files_json, lambda file_json: filter_sub_shelfmarks(shelfmark_from_file_json(file_json), shelfmark_order))
# new_items = 


# groupby(group, lambda sub_group: shelfmark_from_file_json(sub_group)))

sip_physical_structure = physical_items_from(files_json, sip_id, "Tape", sip_text, shelfmark_order)

# with open("sip_test.json", "w") as f:
#     f.write(json.dumps(sip_physical_structure))


# patch_physical_structure(44618, sip_physical_structure, physical_step_state_id, user_id)
print()

# need to mark the physical structure step complete.




#  https://avsip.ad.bl.uk/api/SIP/physicalstructure/63563/508388/8550dbf2-352f-4bc3-bc8e-76383adb2bfa
#  {"Id":63563,"PhysicalStructure":"[{
    #  PATCH api/SIP/physicalstructure/{sip_id}/{step_state_id}/{user_id}

# def physical(object):

#     def __init__(self, SIP_ID):
#         pass
    

#     def get_pSIP_json(self, sip_id=None):
#     """GET a JSON object representing the pSIP from
#     api/SIP/{sip_id}.

#     Args:
#         sip_id (int): pSIP ID number

#     Raises:
#         Exception: "Not Found" HTTP Error 404. The requested resource is not found

#     Returns:
#         dict: The JSON encoded response from the SIP tool
#     """

#     if sip_id is None:
#         sip_id = self.sip_id

#     url = f"{site}/api/SIP/{sip_id}"

#     r = requests.get(url, verify=False)
#     if r.reason == 'Not Found':
#         raise Exception(f'Error Cannot find a SIP with ID number {sip_id}')
#     return r.json()





