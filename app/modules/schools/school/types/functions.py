from json import loads, dumps

from app.modules.schools.school.groups.group.functions import delete_groups
from app.data.db_session import create_session
from app.data.models import School, Group


def delete_type(school, t):
    db_sess = create_session()

    if not (isinstance(school, (int, str, School)) and isinstance(t, (int, str))):
        raise TypeError

    if isinstance(school, str):
        school = db_sess.query(School).filter_by(name=school).first()
    elif isinstance(school, int):
        school = db_sess.query(School).get(school)

    types = loads(school.types)

    if isinstance(t, str):
        t = types.index(t)

    groups = db_sess.query(Group).filter_by(school_id=school.id, type=t).all()
    if groups:
        delete_groups(school, groups)

    del types[t]
    school.types = dumps(types)

    db_sess.commit()
    db_sess.close()
