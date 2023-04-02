# import json
# print(json.dumps({
#     "allowed": [
#         "*"
#     ],
#     "banned": [4]
# }))
from random import choices
from string import digits, ascii_uppercase

key = "".join(choices(digits + ascii_uppercase, k=10))
print(key)