from app.modules.schools.school.classes.school_class.functions import delete_classes
from app.data.models import School, Permission, Class, User
from app.data.functions import allowed_permission
from app.data.db_session import create_session


def delete_schools(schools, user=None, check_permission=True):
    if not isinstance(schools, (School, int, list)):
        raise TypeError

    db_sess = create_session()

    if isinstance(schools, (School, int)):  # noqa
        if isinstance(schools, School):
            schools = schools.id

        schools = [schools]

    elif isinstance(schools, list):
        ss = []
        for c in schools:
            if isinstance(c, int):
                ss.append(c)
            elif isinstance(c, School):
                ss.append(c.id)

        schools = ss

    if check_permission and user is not None:
        permission1 = db_sess.query(Permission).filter_by(title="deleting_self_school").first()
        permission2 = db_sess.query(Permission).filter_by(title="deleting_school").first()
        if not (allowed_permission(user, permission2) or (
                allowed_permission(user, permission1) and user.school_id in schools)):
            db_sess.close()
            return 403

    schools = db_sess.query(School).filter(School.id.in_(schools)).all()  # noqa
    for school in schools:
        classes = db_sess.query(Class).filter_by(school_id=school.id).all()
        delete_classes(school, classes, check_permission=False)

        users = db_sess.query(User).filter_by(school_id=school.id).all()
        for user in users:
            user.school_id = None

        db_sess.delete(school)

    db_sess.commit()
    db_sess.close()

    return True
