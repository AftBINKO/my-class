from json import loads

from flask import redirect, url_for, abort, render_template, send_file, session, request
from flask_login import login_required, current_user

from app.data.functions import check_permission, check_role, all_permissions, get_titles_roles
from app.modules.schools.school.groups.group.functions import delete_groups
from app.modules.schools.school.groups.group.forms import EditGroupForm
from app.data.models import User, Permission, School, Group
from app.modules.schools.school.groups.group import bp
from app.data.db_session import create_session


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    group_id = values['group_id']

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_details_group").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_details_groups").first()  # noqa

    if not (check_permission(current_user, permission2) or (  # noqa
            check_permission(current_user, permission1) and current_user.group_id == group_id)):
        db_sess.close()
        abort(403)

    group = db_sess.query(Group).get(group_id)
    if not group:
        db_sess.close()
        abort(404)

    db_sess.close()


@bp.route('/', methods=['GET', 'POST'])
@login_required
def group_info(school_id, group_id):
    session['url'] = request.base_url

    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))

    school = db_sess.query(School).get(school_id)
    group = db_sess.query(Group).get(group_id)

    students = []
    leader = None
    leader_roles = None

    for user in db_sess.query(User).filter_by(group_id=group_id).all():
        if check_role(user, "Ученик"):
            students.append(user)
        elif check_role(user, "Лидер"):
            leader = user
            leader_roles = get_titles_roles(leader)

    students.sort(key=lambda st: st.fullname.split()[0])

    data = {
        "school": school,
        "permissions": permissions,
        "students": students,
        "leader": leader,
        "leader_roles": leader_roles,
        "group": group,
        "type": loads(school.types)[group.type]
    }

    db_sess.close()
    return render_template("group_info.html", **data)  # noqa


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_group(school_id, group_id):
    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_group").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_groups").first()
    permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()
    permission4 = db_sess.query(Permission).filter_by(title="deleting_groups").first()
    permission5 = db_sess.query(Permission).filter_by(title="deleting_self_group").first()

    is_deleting_group = check_permission(current_user, permission4) or (
            check_permission(current_user, permission5) and current_user.group_id == group_id)

    if not ((check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.group_id == group_id)) and (
                    current_user.school_id == school_id or check_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).get(school_id)
    # types = [(i, t) for i, t in enumerate(loads(school.types), start=1)]
    types = loads(school.types)
    group = db_sess.query(Group).get(group_id)

    form = EditGroupForm()
    if not form.name.data:
        form.name.data = group.name

    ts = [(0, "Выбрать...")]
    if not form.t.data:
        ts = [(group.type + 1, types[group.type])]
    ts += [(i, t) for i, t in enumerate(loads(school.types), start=1) if (i, t) not in ts]
    print(ts)

    form.t.choices = ts

    data = {
        'form': form,
        'school': school,
        'group': group,
        'is_deleting_group': is_deleting_group
    }

    if form.validate_on_submit():
        group.name = form.name.data
        group.type = int(form.t.data) - 1

        db_sess.commit()
        db_sess.close()

        return redirect(session.pop('url', url_for(
            ".group_info", school_id=school_id, group_id=group_id
        )))

    db_sess.close()

    return render_template('edit_group.html', **data)  # noqa


@bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_group(school_id, group_id):
    if delete_groups(school_id, group_id, current_user) == 405:
        abort(403)

    return redirect(url_for("schools.school.groups_list", school_id=school_id))
