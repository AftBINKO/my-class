from data.functions import *
from data.db_session import global_init
import json


def f1():
    print(json.dumps({
        "inheritance": 5,
        "allowed": [],
        "banned": [7]
    }))


def f2():
    global_init("db/data.sqlite3")
    print(all_status_permissions(3))


f1()
