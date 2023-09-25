from app.data.models import School, Class, Permission, User
from app.data.functions import allowed_permission
from app.data.db_session import create_session


def delete_classes(school, classes, user=None, check_permission=True):
    if not (isinstance(school, (School, int)) and isinstance(classes, (Class, int, list))):
        raise TypeError

    db_sess = create_session()
    if isinstance(school, School):
        school = school.id

    if isinstance(classes, (Class, int)):  # noqa
        if isinstance(classes, Class):
            classes = classes.id

        classes = [classes]
    elif isinstance(classes, list):
        cs = []
        for c in classes:
            if isinstance(c, int):
                cs.append(c)
            elif isinstance(c, Class):
                cs.append(c.id)

        classes = cs

    if check_permission and user is not None:
        permission1 = db_sess.query(Permission).filter_by(title="deleting_self_class").first()
        permission2 = db_sess.query(Permission).filter_by(title="deleting_classes").first()
        permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

        if not ((allowed_permission(user, permission2) or (
                allowed_permission(user, permission1) and user.class_id in classes)) and (
                        user.school_id == school or allowed_permission(user, permission3))):
            db_sess.close()
            return 403

    users = db_sess.query(User).filter(User.class_id.in_(classes)).all()  # noqa
    for user in users:
        user.class_id = None
        user.school_id = None
    db_sess.query(Class).filter(Class.id.in_(classes)).delete()  # noqa
    db_sess.commit()
    db_sess.close()

    return True
