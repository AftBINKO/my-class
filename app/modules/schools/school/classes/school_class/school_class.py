from flask import redirect, url_for, abort, render_template, send_file, session, request
from flask_login import login_required, current_user

from app.modules.schools.school.classes.school_class.functions import delete_classes
from app.data.functions import check_permission, check_role, all_permissions, get_titles_roles
from app.modules.schools.school.classes.school_class.forms import EditClassForm
from app.data.models import User, Permission, School, Class, Role
from app.modules.schools.school.classes.school_class import bp
from app.data.db_session import create_session


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    class_id = values['class_id']

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_details_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_details_classes").first()  # noqa

    if not (check_permission(current_user, permission2) or (  # noqa
            check_permission(current_user, permission1) and current_user.class_id == class_id)):
        db_sess.close()
        abort(403)

    school_class = db_sess.query(Class).get(class_id)
    if not school_class:
        db_sess.close()
        abort(404)

    db_sess.close()


@bp.route('/', methods=['GET', 'POST'])
@login_required
def class_info(school_id, class_id):
    session['url'] = request.base_url

    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    students = []
    class_teacher = None
    class_teacher_roles = None

    for user in db_sess.query(User).filter_by(class_id=class_id).all():
        if check_role(user, "Ученик"):
            students.append(user)
        elif check_role(user, "Классный руководитель"):
            class_teacher = user
            class_teacher_roles = get_titles_roles(class_teacher)

    students.sort(key=lambda st: st.fullname.split()[0])

    data = {
        "school": school,
        "permissions": permissions,
        "students": students,
        "class_teacher": class_teacher,
        "class_teacher_roles": class_teacher_roles,
        "class": school_class,
    }

    db_sess.close()
    return render_template("class_info.html", **data)  # noqa


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_class(school_id, class_id):
    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_class").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_classes").first()
    permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()
    permission4 = db_sess.query(Permission).filter_by(title="deleting_classes").first()
    permission5 = db_sess.query(Permission).filter_by(title="deleting_self_class").first()

    is_deleting_class = check_permission(current_user, permission4) or (
            check_permission(current_user, permission5) and current_user.class_id == class_id)

    if not ((check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or check_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    form = EditClassForm()
    if not form.class_number.data:
        form.class_number.data = school_class.class_number
    if not form.letter.data:
        form.letter.data = school_class.letter

    data = {
        'form': form,
        'school': school,
        'class': school_class,
        'is_deleting_class': is_deleting_class
    }

    if form.validate_on_submit():
        school_class.class_number = form.class_number.data
        school_class.letter = form.letter.data

        db_sess.commit()
        db_sess.close()

        return redirect(session.pop('url', url_for(
            ".class_info", school_id=school_id, class_id=class_id
        )))

    db_sess.close()

    return render_template('edit_class.html', **data)  # noqa


@bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_class(school_id, class_id):
    if delete_classes(school_id, class_id, current_user) == 405:
        abort(403)

    return redirect(session.pop('url', url_for("schools.school.classes_list", school_id=school_id)))
