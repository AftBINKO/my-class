# import json
# print(json.dumps({
#     "allowed": [
#         "*"
#     ],
#     "banned": [4]
# }))
fullname = input()
RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"


if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in fullname]):
    print("Поле заполнено неверно. Используйте только буквы русского алфавита")

print(True)