from os import path

from flask import abort, render_template, redirect, url_for, current_app, session, request
from flask_login import login_required, current_user

from app.data.functions import check_permission, check_role, generate_qrs
from app.data.models import User, Permission, School, Group
from app.modules.schools.school.groups.group.qr import bp
from app.data.db_session import create_session
from app import app


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
def view_qrs(school_id, group_id):
    session['url'] = request.base_url

    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)
    group = db_sess.query(Group).get(group_id)

    students = list(sorted([user for user in db_sess.query(User).filter_by(group_id=group_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    db_sess.close()

    data = {
        'group': group,
        'school': school,
        'students': students
    }

    return render_template("view.html", **data)  # noqa


@bp.route('/generate')
@login_required
def generate_qrcodes(school_id, group_id):
    db_sess = create_session()  # noqa

    students = list(sorted([user for user in db_sess.query(User).filter_by(group_id=group_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    db_sess.close()

    qrcodes_path = path.join(current_app.root_path,
                             path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "users")))

    result = generate_qrs(students, current_user, qrcodes_path)
    if result == 403:
        abort(403)

    return redirect(session.pop('url', url_for(".view_qrs", school_id=school_id, group_id=group_id)))
