import json
 
# Data to be written
json_obj = [{
        "name": "JSOD",
        "number": 123
    },
    {
        "abc": "def"
    }
]

print(json_obj)
 
with open("file.json", "w") as outfile:
    json.dump(json_obj, outfile)


with open('file.json', 'r') as openfile:
 
    # Reading from json file
    json_object = json.load(openfile)
 
print(json_object)
print(type(json_object))