import os

def get_cd_log(shelfmark, log_directory):
    os.chdir(log_directory)
    for f in os.listdir():
        if f == shelfmark + ".txt":
            print(f"found {shelfmark} shelfmark log")
            with open(os.path.realpath(f), encoding='utf-16') as log_text:
                return log_text.read()


cdlog = get_cd_log('C1238-8', 'N:\\SOS_HLF\\TEST\\GLASTO_TEST')
print(cdlog.decode('string_escape'))

# 'N:\\SOS_HLF\\Popular Music\\C1238_Glastonbury New Bands Competition collection'