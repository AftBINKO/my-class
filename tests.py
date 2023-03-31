# import json
# print(json.dumps({
#     "allowed": [
#         "*"
#     ],
#     "banned": [4]
# }))


from data.models import User
from data.db_session import create_session, global_init

global_init("db/data.sqlite3")
db_sess = create_session()
a = db_sess.query(User).filter(User.id == 1).first()

print(isinstance(a, User))