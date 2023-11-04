from os import path

from flask import redirect, url_for, abort, render_template, send_file
from flask_login import login_required, current_user

from xlsxwriter import Workbook

from app.data.functions import all_permissions, check_permission, check_role
from app.modules.schools.school.functions import delete_schools
from app.data.models import School, Permission, User, Class
from app.modules.schools.forms import EditSchoolForm
from app.data.db_session import create_session
from app.modules.schools.school import bp


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    school_id = values['school_id']

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="view_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="view_schools").first()
    if not (check_permission(current_user, permission2) or (  # noqa
            check_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).get(school_id)
    if not school:
        db_sess.close()
        abort(404)

    db_sess.close()


@bp.route('/')
@bp.route('/classes')
@login_required
def classes_list(school_id):
    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))

    school = db_sess.query(School).get(school_id)
    classes = db_sess.query(Class).filter_by(school_id=school_id).all()

    db_sess.close()

    data = {
        "school": school,
        "permissions": permissions,
        "classes": classes,
    }

    return render_template("classes.html", **data)  # noqa


@bp.route('/users')
@login_required
def users(school_id):
    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))

    school = db_sess.query(School).get(school_id)

    school_users = db_sess.query(User).filter_by(school_id=school_id).all()
    moderators = []
    teachers = []
    for user in school_users:
        roles = list(map(int, user.roles.split(", ")))
        if 4 in roles:
            moderators.append(user)
        if 2 in roles:
            teachers.append(user)

    moderators.sort(key=lambda moder: moder.fullname.split()[0])
    teachers.sort(key=lambda teacher: teacher.fullname.split()[0])

    db_sess.close()

    data = {
        "school": school,
        "permissions": permissions,
        "moderators": moderators,
        "teachers": teachers
    }

    return render_template("users.html", **data)  # noqa


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_school(school_id):
    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()
    permission3 = db_sess.query(Permission).filter_by(title="deleting_school").first()
    permission4 = db_sess.query(Permission).filter_by(title="deleting_self_school").first()

    if not (check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    is_deleting_school = check_permission(current_user, permission3) or (
            check_permission(current_user, permission4) and current_user.school_id == school_id)

    form = EditSchoolForm()
    school = db_sess.query(School).get(school_id)
    data = {
        'form': form,
        'school': school,
        "is_deleting_school": is_deleting_school
    }

    if form.validate_on_submit():
        school.name = form.school.data
        school.fullname = form.fullname.data

        db_sess.commit()

        school_id = school.id

        db_sess.close()

        return redirect(url_for(".classes_list", school_id=school_id))

    db_sess.close()

    return render_template('edit_school.html', **data)  # noqa


@bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_school(school_id):
    if delete_schools(school_id, current_user) == 403:
        abort(403)

    return redirect(url_for("home"))
