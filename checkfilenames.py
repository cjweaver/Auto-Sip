# Check the directory for filename errors

# import pywin32
import os
import pathlib
import re

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

# List of filename field rules. Taken from the document: "Blah Blah"
filename_hints = {
                    'orignator': "First part of filename should be ‘originator’ i.e 'BL_\n", 
                    'shelf mark': "Please check the shelf mark section of the filename\n", 
                    'item': "Precede the item number with an ‘i’ character. Do not pad with zeros\n", 
                    'side': "Precede the side number with an ‘s’ character. For born-digital files use ‘s0’.\n", 
                    'file': "This field requires two digits, so files under ten should be padded with a single zero (e.g. 01, 02, and 09)\n", 
                    'version': "Record the version number of the file. Do not pad with zeros\n"
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
        # filepaths.append(pathlib.Path.cwd().glob(('*' + f + '*.wav')))
        for result in pathlib.Path.cwd().glob('*' + f + '*.wav'):
            filepaths.append(result)
        
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
            filename_errors.append((f"{f} has {f.name.count(' ')} space(s) in the filename"))
        elif f.name.count('.') > 1:
            errors = True
            filename_errors.append(f"{f} has {f.name.count('.')} extra periods in the filename")
    if errors:
        return (True, filename_errors)
    else:
        return (False, None)


def check_reg_ex(filepaths, bl_regex, bl_regex_segments):

    """Check filenames against RegEx"""
    
    filename_errors = []
    errors = False

    # Need to differentiate between a field missing and a field being wrong.

    for fpath in filepaths:
        if not re.match(bl_regex, fpath.stem):
            # True if filename contains an "i" item field
            if len(fpath.stem.split("_")) != 6:
                regex_segs = bl_regex_segments.copy()
                del regex_segs['item']
            else:
                regex_segs = bl_regex_segments
            
            for regex, fname_seg in zip(regex_segs.items(), fpath.stem.split("_")):
                if not re.match(regex[1], fname_seg):
                    errors = True
                    error = f"There is a problem with the field '{fname_seg}' in file: {fpath.name}"
                    hint = filename_hints.get(regex[0])
                    filename_errors.append(f"{error}\n{hint}")
    if errors:
        return (True, filename_errors)
    else:
        return (False, None)


# def check_filename(filename, bl_regex, bl_regex_segments):
#     result = [x for x in check_reg_ex(filename, bl_regex, bl_regex_segments)]
#     print(result)
#     print("finished Checking")



# fnames = ["BL_C203-359/1_i1_ s1_f12_v.wav", "BL_C203-3591_s01_f1_v1.wav", "BL_C203-359_s100_f12_v1.wav", "BL_C203-359_s1_f12_v1.wav"]

# for fname in fnames:
#     print(check_filename(fname, bl_regex, bl_regex_segments))






