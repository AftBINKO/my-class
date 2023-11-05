from flask import redirect, url_for, abort, render_template, session
from flask_login import login_required, current_user

from app.modules.schools.forms import EditSchoolForm
from app.data.functions import check_permission
from app.data.db_session import create_session
from app.data.models import School, Permission
from app.modules.schools import bp


@bp.before_request
@login_required
def check_register():
    if not current_user.is_registered:
        abort(401)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_school():
    db_sess = create_session()

    permission = db_sess.query(Permission).filter_by(title="adding_school").first()
    if not check_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = EditSchoolForm()
    data = {
        'form': form
    }

    if form.validate_on_submit():
        school = School()

        school.name = form.school.data
        school.fullname = form.fullname.data

        db_sess.add(school)
        db_sess.commit()

        school_id = school.id

        db_sess.close()

        return redirect(session.pop('url', url_for(".school.classes_list", school_id=school_id)))

    db_sess.close()

    return render_template('add_school.html', **data)  # noqa
