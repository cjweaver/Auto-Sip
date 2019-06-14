import re

# https://v12l-avsip.ad.bl.uk:8447/Steps/Search



# Derive structure from call number then check against MARC 087 fields

def list_products(shelfmark, callnumber):
    shelfmark = re.search(r'[a-zA-Z0-9]*/', shelfmark).group()
    # Should be everything before and up to the \ e.g C604\
    callnumber = callnumber.replace(shelfmark, '').replace(' ', '').replace('/', '')
    callnumber = callnumber.split(';')
    print(callnumber)
    pattern = re.compile(r'\d+-\d+')
    for i, item in enumerate(callnumber):
        if pattern.match(item):
            print(f"storing {item} at position {i}")
            num_range = list(map(int, item.split('-')))
            num_range = list(range(num_range[0], num_range[1] + 1))
            del callnumber[i]
            for num in reversed(num_range):
                callnumber.insert(i, str(num))
    return callnumber

products = list_products("C604/543", "C604/543-544; /542; /532; /530-531")
print(products)


