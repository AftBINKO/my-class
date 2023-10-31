from os import path

from flask_login import login_required, current_user
from flask import abort, render_template, redirect, url_for, current_app

from app import app
from app.modules.schools.school.classes.school_class.qr import bp
from app.data.functions import check_permission, check_role, generate_qrs
from app.data.models import User, Permission, School, Class
from app.data.db_session import create_session


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    school_id = values['school_id']  # noqa

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not (check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)


@bp.route('/')
@login_required
def view_qrs(school_id, class_id):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    students = list(sorted([user for user in db_sess.query(User).filter_by(class_id=class_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    db_sess.close()

    data = {
        'class': school_class,
        'school': school,
        'students': students
    }

    return render_template("view.html", **data)  # noqa


@bp.route('/generate')
@login_required
def generate_qrcodes(school_id, class_id):
    db_sess = create_session()  # noqa

    students = list(sorted([user for user in db_sess.query(User).filter_by(class_id=class_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    db_sess.close()

    qrcodes_path = path.join(current_app.root_path,
                             path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "users")))

    result = generate_qrs(students, current_user, qrcodes_path)
    if result == 403:
        abort(403)

    return redirect(url_for(".view_qrs", school_id=school_id, class_id=class_id))
