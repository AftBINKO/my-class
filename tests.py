from datetime import datetime

print((datetime.now() - datetime.strptime("07.09.2022", "%d.%m.%Y")).days)