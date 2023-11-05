from flask import redirect, url_for, abort, render_template, session
from flask_login import login_required, current_user

from app.modules.schools.school.classes.school_class.forms import EditClassForm
from app.data.models import Class, Permission, School
from app.modules.schools.school.classes import bp
from app.data.functions import check_permission
from app.data.db_session import create_session


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_class(school_id):
    db_sess = create_session()

    school = db_sess.query(School).get(school_id)

    permission1 = db_sess.query(Permission).filter_by(title="adding_classes").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not (check_permission(current_user, permission1) and (
            current_user.school_id == school_id or check_permission(current_user, permission2))):
        db_sess.close()
        abort(403)

    form = EditClassForm()
    data = {
        'form': form,
        'school': school
    }

    if form.validate_on_submit():
        school_class = Class()

        school_class.class_number = form.class_number.data
        if form.letter.data:
            school_class.letter = form.letter.data
        school_class.school_id = school_id

        db_sess.add(school_class)
        db_sess.commit()

        class_id = school_class.id

        db_sess.close()

        return redirect(session.pop('url', url_for(
            ".school_class.class_info", school_id=school_id, class_id=class_id
        )))

    db_sess.close()

    return render_template('add_class.html', **data)  # noqa
