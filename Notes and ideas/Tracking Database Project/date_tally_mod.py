import datetime
from collections import Counter

def date_tally(filenames, part="Modified ", datetime_format="%d %b %Y %H:%M:%S %Z"):
    
    """Strip date from list of file property strings and returns the most common date as a datetime object
        can be used without paritioning the string in the case if simply a list of dates as a string.
    """
    
    list_of_dates = []
    for file in filenames:
        part = file.partition("Modified: ")[2]
        filedate = datetime.datetime.strptime(part, datetime_format)
    
    
    
        list_of_dates.append(filedate.date())
    
    
    tally_dates = [[x, list_of_dates.count(x)] for x in set(list_of_dates)]
    tally_dates = sorted(tally_dates, key = lambda date: date[1])
    return tally_dates[-1][0]


transfer_dates = ['2019-02-27', '2019-02-27', '1900-01-01']


format = "%Y-%m-%d"
date_tally(transfer_dates)