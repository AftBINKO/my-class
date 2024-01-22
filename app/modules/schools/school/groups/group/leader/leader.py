from flask import redirect, url_for, abort, render_template, session
from flask_login import login_required, current_user

from app.data.functions import check_permission, add_role, get_roles, get_max_role, check_role, del_role
from app.modules.schools.school.groups.group.leader import bp
from app.data.models import User, Permission, School, Group
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.db_session import create_session
from app import RUSSIAN_ALPHABET


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    school_id = values['school_id']  # noqa

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()
    permission3 = db_sess.query(Permission).filter_by(title="editing_groups").first()

    if not (check_permission(current_user, permission3) and (check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.school_id == school_id))):
        db_sess.close()
        abort(403)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_leader(school_id, group_id):
    db_sess = create_session()

    school = db_sess.query(School).get(school_id)
    group = db_sess.query(Group).get(group_id)

    form = ChangeFullnameForm()

    title = f'Создать лидера группы "{group.name}" {school.name}'

    data = {
        'form': form,
        'title': title,
        'school': school,
        'class': group,
        'message': None
    }

    if form.validate_on_submit():
        leader = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            leader.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            leader.school_id = school_id
            leader.group_id = group_id
            leader.roles = '[3]'
            leader.generate_key()

            db_sess.add(leader)
            db_sess.commit()
            db_sess.close()

            return redirect(session.pop('url', url_for("schools.school.groups.group.group_info",
                                                       school_id=school_id, group_id=group_id)))

    db_sess.close()

    return render_template('add_leader.html', **data)  # noqa


@bp.route('/add_existing', methods=['GET', 'POST'])
@login_required
def add_existing_leader(school_id, group_id):
    db_sess = create_session()

    school = db_sess.query(School).get(school_id)
    group = db_sess.query(Group).get(group_id)

    form = SelectUser()  # noqa

    school_users = db_sess.query(User).filter_by(school_id=school_id).all()
    users = [(0, "Выбрать...")]
    for us in school_users:
        roles = get_roles(us)
        role = get_max_role(us)
        if role.title in ["Модератор", "Учитель"] and "Лидер" not in list(
                map(lambda s: s.title, roles)):
            users.append((us.id, us.fullname))

    form.select.choices = users

    title = f'Выбрать лидера группы "{group.name}" {school.name}'

    data = {
        'form': form,
        'school': school,
        'title': title,
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            user = db_sess.query(User).get(user_id)
            add_role(user, "Лидер")
            user.group_id = group_id

            db_sess.commit()
            db_sess.close()

            return redirect(
                url_for("schools.school.groups.group.group_info", school_id=school_id, group_id=group_id)
            )
        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing.html', **data)


@bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete(school_id, group_id):
    db_sess = create_session()

    users = db_sess.query(User).filter_by(group_id=group_id).all()
    leader = None
    for user in users:
        if check_role(user, "Лидер"):
            leader = user
            break

    if leader is None:
        abort(404)

    del_role(leader.id, "Лидер")
    db_sess.close()

    return redirect(url_for("schools.school.groups.group.group_info", school_id=school_id, group_id=group_id))
