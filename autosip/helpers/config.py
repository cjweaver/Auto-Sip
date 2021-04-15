# Live SIP Tool Website
site="https://avsip.ad.bl.uk"

# DEV SIP Tool Website 
# site="https://v12l-avsip.ad.bl.uk:8450"


# SOS_HLF Drive
UNC = r"\\p12l-nas6\SOS_HLF"

# SAMI Connection details
SAMI_API = "http://nipper.bl.uk:8080/symws/rest/standard/lookupTitleInfo?clientID={CLIENT_ID}&marcEntryFilter=TEMPLATE&includeItemInfo=true&titleID={titleID}&libraryFilter=PRODUCT"
CLIENT_ID = "ARMADILLO"

splash_screen = """
###########################################################################################
#                                                                                         #
#                                                                                         #
#    .d888888             dP            .d88888b  dP  888888ba                            #  
#    d8'    88             88            88.    "' 88  88    `8b                          #          
#    88aaaaa88a dP    dP d8888P .d8888b. `Y88888b. 88 a88aaaa8P'                          #          
#    88     88  88    88   88   88'  `88       `8b 88  88                                 #          
#    88     88  88.  .88   88   88.  .88 d8'   .8P 88  88                                 #              
#    88     88  `88888P'   dP   `88888P'  Y88888P  dP  dP                                 #
#                                                                                         #  
#    Last update March 2nd 2021                                                           #
#                                                                                         #
#    This is for Chrome version 88.                                                       #
#                                                                                         #
#    Completes physical structure using SAMI and will check filenames against new schema. #
#    (N.B filenames with the "i" item field default to CD-style physical structure)       #  
#                                                                                         #
#    Can use any spreadsheet to read SIPS.                                                #
#                                                                                         #
#    Very much a work in progress!                                                        #
#    For support christopher.weaver@bl.uk                                                 #
#                                                                                         #
###########################################################################################
"""