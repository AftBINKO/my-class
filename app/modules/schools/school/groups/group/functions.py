from app.data.models import School, Group, Permission, User
from app.data.functions import check_permission as cp
from app.data.db_session import create_session


def delete_groups(school, groups, user=None, check_permission=True):
    if not (isinstance(school, (School, int)) and isinstance(groups, (Group, int, list))):
        raise TypeError

    db_sess = create_session()
    if isinstance(school, School):
        school = school.id

    if isinstance(groups, (Group, int)):  # noqa
        if isinstance(groups, Group):
            groups = groups.id

        groups = [groups]
    elif isinstance(groups, list):
        cs = []
        for c in groups:
            if isinstance(c, int):
                cs.append(c)
            elif isinstance(c, Group):
                cs.append(c.id)

        groups = cs

    if check_permission and user is not None:
        permission1 = db_sess.query(Permission).filter_by(title="deleting_self_group").first()
        permission2 = db_sess.query(Permission).filter_by(title="deleting_groups").first()
        permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

        if not ((cp(user, permission2) or (cp(user, permission1) and user.group_id in groups)) and (
                user.school_id == school or cp(user, permission3))):
            db_sess.close()
            return 403

    users = db_sess.query(User).filter(User.group_id.in_(groups)).all()  # noqa
    for user in users:
        user.group_id = None
        user.school_id = None
    db_sess.query(Group).filter(Group.id.in_(groups)).delete()  # noqa
    db_sess.commit()
    db_sess.close()

    return True
