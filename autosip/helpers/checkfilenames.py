# checkfilenames.py
# Check the files in a given directory against the new BL filename schema
# import pywin32
import os
import pathlib
import re
import itertools
from colorama import Fore, Back, Style, init

# Insert the BL filename regex here. Ensure that the leading r is kept for "raw" string
bl_regex = r"[A-Z]{2,5}_[A-Za-z0-9-]{1,}(_i\d{1,3})?_s([0-9]{1}|[1-9]{1,2})_f\d{2}_v\d{1,2}"

# Same regex as above split into named filename fields. 
bl_regex_segments = {
                    'orignator': r"^[A-Z]{2,5}$", 
                    'shelf mark': r"^[A-Za-z0-9-]{1,}$", 
                    'item': r"^i([1-9]{1}|[0-9]{1,3})$", 
                    'side': r"^s([0-9]{1}|[1-9]{1,2})$", 
                    'file': r"^f\d{2}$", 
                    'version': r"^v\d{1,2}$"
                    }

# List of filename field rules. Taken from the document: "How to Create Filenames for Unlocking our Sound Heritage v0.4"
filename_hints = {
                    'orignator': "First part of filename should be ‘originator’ e.g. 'BL_ or TWAM_\n", 
                    'shelf mark': """Please check the shelf mark section of the filename. 
                                     Replace any existing separators in your shelf mark (e.g. ‘/’, ‘.’, ‘ ‘, &c.) with a hyphen (‘-‘)\n""", 
                    'item': """Precede the item number with an ‘i’ character. Do not pad with zeros
                               N.B. Items numbers are non-mandatory for a single item with a single shelf mark.\n""", 
                    'side': """Precede the side number with an ‘s’ character. For born-digital files use ‘s0’.
                               Sides are not zero padded.\n""", 
                    'file': "The 'file' field requires two digits, so files under ten should be padded with a single zero (e.g. 01, 02, and 09)\n", 
                    'version': """Record the version number of the file in cases where subjective choices have been made
                                  (alternate stylus choice, playback speed &c.). Do not pad with zeros\n"""
                    }



# def network_to_local(directory):

#     """Switch the mapped (local) SOS HLF Drive"""

#     resume = 0
#     while True:
#         (_drives, total, resume) = win32net.NetUseEnum (None, 0, resume)
#         for drive in _drives:
#             if drive['local'] and drive['remote'] == '\\\\p12l-nas6\\SOS_HLF':
#                 os.chdir(os.path.join(drive['local'], directory))
#         if not resume: 
#             break


def connect_to_sos(unc, directory):

    """Connects to the SOS_HLF directory for the collection. 
       Specify UNC path as two raw strings
    """
    
    path = pathlib.Path(unc)
    os.chdir(pathlib.Path.joinpath(path, directory))
    
def get_file_paths(filemask):

    """Returns a list of pathlib objects matching the filemask
       i.e C203-359_ will match 'BL_C203-359_s1_f01_v1.wav' etc"""

    filepaths = []
    for f in filemask:
        # Need to check and strip.wav file people have specified a full file name
        # filepaths.append(pathlib.Path.cwd().glob(('*' + f + '*.wav')))
        for result in pathlib.Path.cwd().glob('*' + f + '*.wav'):
            filepaths.append(result)
    if not filepaths:
        print(Back.RED + f"\nUnable to find any files matching {filemask}.")
        raise FileNotFoundError         
    else:    
        return filepaths



def check_filenames(filepaths):

    """check filenames for common errors - spaces, extra dots"""

    filename_errors = []
    errors = False

    # for i, _ in enumerate(filemask):
    #     for f in pathlib.Path.cwd().glob(('*' + filemask[i] + '*.wav')):
    for f in filepaths:
        if f.name.count(' '):
            errors = True 
            filename_errors.append((f"{f.name} has {f.name.count(' ')} space(s) in the filename"))
        elif f.name.count('.') > 1:
            errors = True
            filename_errors.append(f"{f.name} has {f.name.count('.')} extra periods in the filename")
    if errors:
        return (True, filename_errors)
    else:
        return (False, None)


def check_reg_ex(filepaths, bl_regex, bl_regex_segments):

    """Check filenames against RegEx"""
    
    filename_errors = []
    errors = False

    for fpath in filepaths:
        if not re.match(bl_regex, fpath.stem):
            if len(fpath.stem.split("_")) == 5:
                regex_segs = bl_regex_segments.copy()
                del regex_segs['item']
            # True if filename contains an "i" item field
            elif len(fpath.stem.split("_")) == 6:
                regex_segs = bl_regex_segments
            else:
                # Check for the missing field in the filename
                # Bit of a hack...
                errors = True
                missing_field = [prefix for prefix in ['f', 's', 'v'] if prefix not in [seg[0] for seg in fpath.stem.split("_")]][0]
                filename_errors.append(f"The file {fpath.name} is missing the '{missing_field}' field.")
                return (True, filename_errors)
            
            for regex, fname_seg in zip(regex_segs.items(), fpath.stem.split("_")):
                if not re.match(regex[1], fname_seg):
                    errors = True
                    error = f"There is a problem with the field '{fname_seg}' in file: {fpath.name}"
                    hint = filename_hints.get(regex[0])
                    filename_errors.append(f"{error}\n{hint}")
        
        # Check for a item field accidently in the shelfmark e.g. C516-01-11-i1_s1_f01_v1
        if list(filter(None, map(re.search, itertools.repeat(r'-i\d', len(fpath.stem.split("_"))), fpath.stem.split("_")))):
            errors = True
            filename_errors.append(f"An item field appears in the shelfmark in file {fpath.name}.\nPerhaps a hypen instead of an underscore")

    if errors:
        return (True, filename_errors)
    else:
        return (False, None)

