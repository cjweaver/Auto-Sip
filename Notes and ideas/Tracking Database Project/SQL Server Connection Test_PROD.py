# SQL Server Connection Test
# Imports JSON for whole pSIP, locates SamicallNumber (shelfmark) from filenames 
# and queries Tracking Database with this shelfmark
# Also extracts the ProcessMetadata JSON string


import json
import pyodbc
import os
import re
import datetime
from collections import Counter
# from config

LOCAL_TEST_DB = ('Driver={SQL Server};'
                 'Server=DESKTOP-BTL44HD\SQLEXPRESS;'
                 'Database=UOSH_TrackingDB;'
                 'Trusted_Connection=yes;')


LIVE_TDB = ('Driver={SQL Server};'
            'Server=V16B-SQL16DEV,9433;'
            'Database=UOSH_TrackingDB;'
            'Trusted_Connection=yes;')                

HOME = "C:\\Users\\chris\\Desktop\\Tracking Database Project\\JSON"
WORK = "C:\\Users\\cweaver\\Desktop\\Tracking Database Project\\Tracking Database Project"

## THESE VALUES SHOULD GO INTO A GLOBAL CONFIG FILE
# OR COULD BE READ FROM THE TRACKING DATABASE
# Lkup_Engineer
ENGINEERS = [
    "Andrea Zarza",
    "Chris Weaver",
    "Gavin Bardon",
    "Gosha Shtasel",
    "Kevin Lemonnier",
    "Russell Gould",
    "Tom Ruane",
    "Tony Harris",
    "Yadley Day",
    "Adam Tovell",
    "Robert Cowlin",
    "Katie Tavini",
    "Thea Cochrane",
    "zzz_",
    "British Library",
    "N/A",
    "Other",
    "Abby Thomas",
    "Will Prentice",
    "Memnon Archiving Services",
    "Simon Wilson",
    "John Davies",
    "Christos Parmenidis",
    "Joshua Kean-Hammerson"
    ]
# These are devices where the speed can be changed and is recorded in 
# ['replaySpeed']['value']
PLAYBACK_DEVICES = ['Tape recorder', 'Turntable', 'Cylinder player', 'Wire recorder']



def device_specs(process_md_as_json):
    process_md = json.loads(process_md_as_json)
    for i in process_md['processMetadata'][0]['children']: 
        if i['processType'] == 'Migration' and (i['devices'][0]['deviceType'] in PLAYBACK_DEVICES):
            Tech_Speed = i['devices'][0]['parameters'][(i['devices'][0]['deviceType'])]['replaySpeed']['value'].replace("^^"," ")
            device_name = f"{i['devices'][0]['manufacturer']} {i['devices'][0]['model']}"
            device_serial = f"Serial Number: {i['devices'][0]['serial']}"
            eq = i['devices'][0]['parameters'][(i['devices'][0]['deviceType'])]['equalisation']['value'].replace("^","")
    return Tech_Speed, device_name, device_serial, eq


def create_sip_files(sipJSON):

    sip_files = {}
    
    for file in sipJSON['Files']:
        # Get all the shelfmarks from the files names contained in the pSIP
        shelfmark = re.search(r"BL_[A-Za-z0-9-]+", file['Name']).group().split("_")[1]
        # Format the shelfmarks correctly i.e 'C604-100' should be 'C604/100'
        shelfmark = shelfmark.replace("-", "/")
        # This works for collection items at a sub-shelfmark i.e BL_C604-100-1
        # but not in the case of wildlife where the hypen merely replaces a space 
        # i.e BL_WA-2008-015 shelfmark is not WA/2008/015 it's WA<SPACE>2008/015 
        # Hack to fix spaces issue in Wildlife filenames.
        if shelfmark.startswith("WA-"):
            shelfmark = shelfmark.replace("WA-", "WA ")
        elif shelfmark.startswith("WA"):
            shelfmark = shelfmark.replace("WA", "WA ")

        if not sip_files.get(shelfmark):
            sip_files[shelfmark] = {}
            sip_files[shelfmark]['files'] = {}
        
        if bool(file['ProcessMetadata']):
                sip_files[shelfmark]["Custom_ProcessMetadata"] = True
                sip_files[shelfmark]["Tech_Speed"] = "See Other Tech Notes"
        
        if not sip_files[shelfmark]['files'].get(file['FileId']):
            sip_files[shelfmark]['files'][file['FileId']] = {}
            # The name is the filename. Is this a list if the pSIP has more than one file in it? No, multiple items in the File list.
            sip_files[shelfmark]['files'][file['FileId']]["Name"] = file['Name']
            sip_files[shelfmark]['files'][file['FileId']]['shelfmark'] = re.search(r"BL_[A-Za-z0-9-]+", file['Name']).group().split("_")[1]
        
    for shelfmark in sip_files:
        sip_files[shelfmark]['PSIP_Date'] = sipJSON['StepStates'][0]['Created']
        sip_files[shelfmark]['PSIP_Engineer'] = sipJSON['StepStates'][0]['CreatedByUserName'].split('@')[0].replace('.', ' ').title()
        Tech_OtherNote = ""

        transfer_dates = []
        transfer_engineers = []
        TechTrack_Config = []
        
        for file in sip_files[shelfmark]['files']:

        # if not sip_files[shelfmark]['files'].get(file['FileId']):
        #     sip_files[shelfmark]['files'][file['FileId']] = {}
        #     # The name is the filename. Is this a list if the pSIP has more than one file in it? No, multiple items in the File list.
        #     sip_files[shelfmark]['files'][file['FileId']]["Name"] = file['Name']
        #     sip_files[shelfmark]['files'][file['FileId']]['shelfmark'] = re.search(r"BL_[A-Za-z0-9-]+", file['Name']).group().split("_")[1]
            
            # Extract Transfer Engineer from the JSON
            # First try JHOVE XML, then MediaInfo before falling back on SIP UserName
            for i in sipJSON['Files']:
                if i['FileId'] == file:
                    JHOVEXml = i['JHOVEXml']
                    # Get number audio channels 1 for mono, 2 for stereo or dual mono.
                    sip_files[shelfmark]['files'][file]["audio_channels"] = int(i['AudioInfo']['ChannelOutput'].split(" channel")[0])
                    TechTrack_Config.append(sip_files[shelfmark]['files'][file]["audio_channels"])

                    

                    try:
                        sip_files[shelfmark]['files'][file]['transfer_engineer'] = re.search(r"Engineer\s(\w+\s\w+)", JHOVEXml).group(1)
                    except AttributeError:
                        for engineer_name in ENGINEERS:
                            transfer_engineer = re.search(engineer_name, i['MediaInfoXml'])
                        if transfer_engineer == None:
                            transfer_engineer = sipJSON['UserName'].replace('.', ' ').split('@')[0].title()
                            print(f"No Transfer Engineer in WAV file metadata.\nDefaulting to pSIP username: {transfer_engineer}.")
                        sip_files[shelfmark]['files'][file]['transfer_engineer'] = transfer_engineer
                    transfer_engineers.append(sip_files[shelfmark]['files'][file]['transfer_engineer'])

                    # get the WAV File Creation Date Metadata (stored in the BWF INFO header) from the JHOVE report XML
                    try:
                        Transfer_Date = re.search(r"CreationDate\s(\d\d\d\d-\d\d-\d\d)", JHOVEXml).group(1)
                        Transfer_Date = datetime.datetime.strptime(Transfer_Date, "%Y-%m-%d")
                        transfer_dates.append(Transfer_Date)
                        sip_files[shelfmark]['files'][file]['Transfer_Date'] = Transfer_Date
                    except AttributeError:
                        # Need to get the value from "File Select Page"
                        sip_files[shelfmark]['files'][file]['Transfer_Date'] = '1900-01-01'
                        print(f"No Transfer Date in WAV file metadata.\nDefaulting to file creation date WHICH IS??. Correct Tracking Database")

                    #This is for tapes with multiple speeds on them (custom process metadata)
                    # Need to search for "Migration"
                    if sip_files[shelfmark].get("Custom_ProcessMetadata"): 
                        #if Custom_ProcessMetadata = True - Speed 310 field in Tracking Database is set to "See Other Tech Notes"
                        sip_files[shelfmark]['files'][file]['custom_process'] = {}
                        if bool(i['ProcessMetadata']) == True:
                            Tech_Speed, device_name, device_serial, eq = device_specs(i['ProcessMetadata'])
                        else:
                            Tech_Speed, device_name, device_serial, eq = device_specs(sipJSON['ProcessMetadata'])
                        
                        sip_files[shelfmark]['files'][file]['custom_process']['Tech_Speed'] = Tech_Speed
                        sip_files[shelfmark]['files'][file]['custom_process']['device_name'] = device_name
                        sip_files[shelfmark]['files'][file]['custom_process']['device_serial'] = device_serial
                        sip_files[shelfmark]['files'][file]['custom_process']['eq'] = eq
                        Tech_OtherNote += f"{sip_files[shelfmark]['files'][file]['Name']} replay speed: {sip_files[shelfmark]['files'][file]['custom_process']['Tech_Speed']}\n"
                        sip_files[shelfmark]['Tech_OtherNote'] = Tech_OtherNote

                    else:
                        Tech_Speed, device_name, device_serial, eq = device_specs(sipJSON['ProcessMetadata'])
                        sip_files[shelfmark]['Tech_Speed'] = Tech_Speed
                        sip_files[shelfmark]['device_name'] = device_name
                        sip_files[shelfmark]['device_serial'] = device_serial
                        sip_files[shelfmark]['eq'] = eq
                        sip_files[shelfmark]['Tech_OtherNote'] = Tech_OtherNote

        # Try to get the most common date or transfer engineer in the case of an item being digitised on different days and/or by different people
        # The Tracking Database can only handle one engineer and one date per item
        # sometimes (very rarely) engineers put in a comment.
        sip_files[shelfmark]['Transfer_Engineer'], _ = Counter(transfer_engineers).most_common(1)[0]
        sip_files[shelfmark]['Transfer_Date'], _ = Counter(transfer_dates).most_common(1)[0]
            
        # Track Config
        # All files are are mono(1), stereo(2) or stereo / mono(1 & 2s)
        if min(TechTrack_Config) != max(TechTrack_Config):
            sip_files[shelfmark]['TechTrack_Config'] = "stereo / mono"
        elif min(TechTrack_Config) == 2:
            sip_files[shelfmark]['TechTrack_Config'] = "stereo"
        else:
            sip_files[shelfmark]['TechTrack_Config'] = "mono"
            
            
    return sip_files



# def speed_310(sip_files, shelfmark):
#     Tech_OtherNote = ""
#     # for shelfmark in sip_files.keys():
#     if sip_files[shelfmark].get('Custom_ProcessMetadata'):
#         for file in sip_files[shelfmark]['files']:
#             if sip_files[shelfmark]['files'][file].get('custom_process'):
#                 Tech_OtherNote += f"{sip_files[shelfmark]['files'][file]['Name']} replay speed: {sip_files[shelfmark]['files'][file]['custom_process']['Tech_Speed']}\n"
#             else:
#                 Tech_OtherNote += f"{sip_files[shelfmark]['files'][file]['Name']} replay speed: {sip_files[shelfmark]['Tech_Speed']}\n"
#     return (sip_files[shelfmark]['Tech_Speed'], Tech_OtherNote)
#             # return 310 field and msg

# for shelfmark in sip_files.keys():
#     speed = speed_310(sip_files, shelfmark)
#     print(speed[0], speed[1])


# #pyodbc Exceptions:
# 
# Exception has occurred: OperationalError
# ('08001', '[08001] [Microsoft][ODBC SQL Server Driver][DBMSLPCN]SQL Server does not exist or access denied. (17) (SQLDriverConnect); [08001] [Microsoft][ODBC SQL Server Driver][DBMSLPCN]ConnectionOpen (Connect()). (2)')
#   File "C:\Users\chris\Desktop\Tracking Database Project\SQL Server Connection Test.py", line 198, in <module>
#     connection = pyodbc.connect(LOCAL_TEST_DB)

def update_tracking_db(sip_files):

    # Set up connection

    try:
        connection = pyodbc.connect(LIVE_TDB)
        cursor = connection.cursor()
    except pyodbc.OperationalError as e:
        print('Unable to open database connection\n', e.args[1])

    for shelfmark in sip_files:
        
        # Transfer Equipment where there is custom process metadata
        # Count the devices?
        # Put the first one?
        if sip_files[shelfmark].get('Custom_ProcessMetadata'):
            transfer_machines = []
            for file in sip_files[shelfmark]['files']:
                 transfer_machines.append(f"{sip_files[shelfmark]['files'][file]['custom_process']['device_name']}\n" \
                                          f"{sip_files[shelfmark]['files'][file]['custom_process']['device_serial']}\n" \
                                          f"{sip_files[shelfmark]['files'][file]['custom_process']['eq']}"
                                        )
                #  eqs.append(sip_files[shelfmark]['files'][file]['custom_process']['eq'])

                 

            custom_device = ' '.join(f'{device}\n' for device in set(transfer_machines))


            Transfer_Equipment = f"Custom Process Metadata - See ADD URL LINK\n{custom_device}\n{custom_eq}"
        else:
            Transfer_Equipment = f"{sip_files[shelfmark]['device_name']}\n{sip_files[shelfmark]['device_serial']}\n{sip_files[shelfmark]['eq']}"


        # Get the Transfer Engineer and P-SIP Engineer ID 
        #  PPYODBC allows accessing values by column name, rather than tuple position.
        # https://github.com/mkleehammer/pyodbc/wiki/Row

        def engineer_lookup(engineer_name):
            row = cursor.execute("""
                        SELECT [dbo].[Lkup_Engineer].[ID] FROM [dbo].[Lkup_Engineer] WHERE [dbo].[Lkup_Engineer].[LkF_Engineer]=?;
                        """, 
                        engineer_name
                        ).fetchone()
            return row.ID
        
        Engineer_Lookup = engineer_lookup(sip_files[shelfmark]['Transfer_Engineer'])
        PSIP_Engineer_Lookup = engineer_lookup(sip_files[shelfmark]['PSIP_Engineer'])


        # Get the Tech_Speed ID
        Tech_Speed_Lookup = cursor.execute("""
                                        SELECT [dbo].[Lkup_Tech_Speed].[ID] FROM [dbo].[Lkup_Tech_Speed] WHERE [dbo].[Lkup_Tech_Speed].[LkF_Speed]=?;
                                        """, 
                                        sip_files[shelfmark]['Tech_Speed']
                                        ).fetchone().ID
        
        
        
        # This has been split into three SQl statements now.
        # 
        # cursor.execute("""
        #     UPDATE [dbo].[Main]
        #     SET [dbo].[Main].[Transfer_Date] =?,
        #         [dbo].[Main].[Transfer_Engineer] = (SELECT [dbo].[Lkup_Engineer].[ID] FROM [dbo].[Lkup_Engineer] WHERE [dbo].[Lkup_Engineer].[LkF_Engineer]=?),
        #         [dbo].[Main].[Transfer_Equipment] =?,
        #         [dbo].[Main].[PSIP_Engineer] = (SELECT [dbo].[Lkup_Engineer].[ID] FROM [dbo].[Lkup_Engineer] WHERE [dbo].[Lkup_Engineer].[LkF_Engineer]=?),
        #         [dbo].[Main].[PSIP_Date] =?,
        #         [dbo].[Main].[Tech_Speed] =(SELECT [dbo].[Lkup_Tech_Speed].[ID] FROM [dbo].[Lkup_Tech_Speed] WHERE [dbo].[Lkup_Tech_Speed].[LkF_Speed]=?),
        #         [dbo].[Main].[Tech_OtherNote] =?
        #     FROM [dbo].[Main] 
        #     WHERE [dbo].[Main].[Shelfmark] =?;
        #     """,
        #     sip_files[shelfmark]['Transfer_Date'], 
        #     sip_files[shelfmark]['Transfer_Engineer'],
        #     Transfer_Equipment,
        #     sip_files[shelfmark]['PSIP_Engineer'],
        #     sip_files[shelfmark]['PSIP_Date'],
        #     sip_files[shelfmark]['Tech_Speed'],
        #     sip_files[shelfmark]['Tech_OtherNote'],
        #     shelfmark
        #     )
        # cursor.commit()
        


        



       
        cursor.execute("""
            UPDATE [dbo].[Main]
            SET [dbo].[Main].[Transfer_Date] =?,
                [dbo].[Main].[Transfer_Engineer] =?,
                [dbo].[Main].[Transfer_Equipment] =?,
                [dbo].[Main].[PSIP_Engineer] =?,
                [dbo].[Main].[PSIP_Date] =?,
                [dbo].[Main].[Tech_Speed] =?,
                [dbo].[Main].[Tech_OtherNote] =?
            FROM [dbo].[Main] 
            WHERE [dbo].[Main].[Shelfmark] =?;
            """,
            sip_files[shelfmark]['Transfer_Date'], 
            Engineer_Lookup,
            Transfer_Equipment,
            PSIP_Engineer_Lookup,
            sip_files[shelfmark]['PSIP_Date'],
            Tech_Speed_Lookup,
            sip_files[shelfmark]['Tech_OtherNote'],
            shelfmark
            )
        cursor.commit()


        print(f"Updating {shelfmark} in the Tracking Database...")

# Test using JOSN files
os.chdir(HOME)
json_files = os.listdir()
json_files.remove("OLD FILENAMES")
for json_file in json_files:
    with open(json_file, 'r') as f:
    # with open('C1163-54.json', 'r') as f:
        print(f)
        sip_files = create_sip_files(json.load(f))
        update_tracking_db(sip_files)
# print(sip_files)

# Transfer_Date
# Transfer_Engineer
# Transfer_Engineer
# P-SIP Date
# P-SIP Engineer
# Tech_Speed
# Tech_OtherNote

#  (SELECT [dbo].[Lkup_Engineer].[ID] FROM [dbo].[Lkup_Engineer] WHERE [dbo].[Lkup_Engineer].[LkF_Engineer]=?)

# [dbo].[Main].[Tech_Speed] =(SELECT ID FROM [dbo].[Lkup_Tech_Speed] WHERE [dbo].[Lkup_Tech_Speed].[LkF_Speed]=?)


# 