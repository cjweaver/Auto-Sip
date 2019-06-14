import re

shelfmark = input("Shelfmark: ")
structure = input("Structure: ")
# print("Structure = 'C604/640-C604/649; C604/64'")
# structure = 'C604/640-C604/649; C604/64'
print(structure)
structure = structure.replace(shelfmark, '').replace(' ', '')
structure = structure.split(';')
print(structure)
pattern = re.compile(r'\d+-\d+')
results = []
for i, item in enumerate(structure):
    if pattern.match(item):
        print(f"storing {item} at position {i}")
    
        num_range = list(map(int, item.split('-')))
        num_range = list(range(num_range[0], num_range[1] + 1))
        #num_range = num_range.res
        del structure[i]
        for num in reversed(num_range):
            structure.insert(i, str(num))
print(structure)
        
