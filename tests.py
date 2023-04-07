from data.functions import *
from data.db_session import global_init, create_session
from data.models import *
import json

global_init("db/data.sqlite3")


def f1():
    print(json.dumps({
        "inheritance": 5,
        "allowed": [],
        "banned": [7]
    }))


def f2():
    print(all_status_permissions(3))


db_sess = create_session()
print(list(map(lambda school: school.to_dict(), db_sess.query(User).all())))
