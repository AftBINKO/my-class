from json import loads, dumps

from flask import redirect, url_for, abort, render_template, session
from flask_login import login_required, current_user

from app.modules.schools.school.types.forms import EditTypeForm
from app.modules.schools.school.types import bp
from app.data.functions import check_permission
from app.data.db_session import create_session
from app.data.models import Permission, School


@bp.url_value_preprocessor
@login_required
def check_permissions(endpoint, values):
    school_id = values['school_id']  # noqa

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not (check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    db_sess.close()


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_type(school_id):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)

    form = EditTypeForm()
    data = {
        'form': form,
        'school': school,
    }

    if form.validate_on_submit():
        types = loads(school.types)
        types.append(form.name.data)
        school.types = dumps(types)

        db_sess.commit()
        db_sess.close()

        return redirect(url_for("schools.school.edit_school", school_id=school_id))

    db_sess.close()

    return render_template('add_type.html', **data)  # noqa


@bp.route('/edit/<int:i>', methods=['GET', 'POST'])
@login_required
def edit_type(school_id, i):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)

    form = EditTypeForm()

    types = loads(school.types)
    t = types[i]

    data = {
        'form': form,
        'school': school,
        'type': t
    }

    if not form.name.data:
        form.name.data = t

    if form.validate_on_submit():
        types[i] = form.name.data
        school.types = dumps(types)

        db_sess.commit()
        db_sess.close()

        return redirect(url_for("schools.school.edit_school", school_id=school_id))

    db_sess.close()

    return render_template('edit_type.html', **data)  # noqa
