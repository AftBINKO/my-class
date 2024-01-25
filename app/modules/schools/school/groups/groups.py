from json import loads

from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.modules.schools.school.groups.group.forms import EditGroupForm
from app.data.models import Group, Permission, School
from app.modules.schools.school.groups import bp
from app.data.functions import check_permission
from app.data.db_session import create_session


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_group(school_id):
    db_sess = create_session()

    school = db_sess.query(School).get(school_id)

    permission1 = db_sess.query(Permission).filter_by(title="adding_groups").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not (check_permission(current_user, permission1) and (
            current_user.school_id == school_id or check_permission(current_user, permission2))):
        db_sess.close()
        abort(403)

    types = [(0, "Выбрать...")] + [(i, t) for i, t in enumerate(loads(school.types), start=1)]

    form = EditGroupForm()
    form.t.choices = types

    data = {
        'form': form,
        'school': school,
        'message': None
    }

    if form.validate_on_submit():
        i = int(form.t.data)
        if i:
            group = Group()

            group.name = form.name.data
            group.school_id = school_id
            group.type = i - 1

            db_sess.add(group)
            db_sess.commit()

            group_id = group.id

            db_sess.close()

            return redirect(url_for(
                ".group.group_info", school_id=school_id, group_id=group_id
            ))
        data['message'] = "Вы не выбрали категорию группы"

    db_sess.close()

    return render_template('add_group.html', **data)  # noqa
