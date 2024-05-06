from flask import abort, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.data.functions import check_permission
from app.data.db_session import create_session
from app.modules.admits.forms import AdmitForm
from app.data.models import Permission
from app.modules.admits import bp


@bp.before_request
@login_required
def check_register():
    db_sess = create_session()
    permission1 = db_sess.query(Permission).filter_by(title="admit").first()
    permission2 = db_sess.query(Permission).filter_by(title="admit_school").first()
    if not (current_user.is_registered and current_user.school_id and (
            check_permission(current_user, permission1) or check_permission(current_user, permission2)
    )):
        abort(401)


@bp.route('/', methods=['GET', 'POST'])
@login_required
def admit():
    form = AdmitForm()
    data = {
        'title': 'Отметить присутствующих',
        'form': form,
    }

    if form.validate_on_submit():
        return redirect(url_for('qr.admit', user_id=form.id.data))

    return render_template('letit.html', **data)  # noqa
