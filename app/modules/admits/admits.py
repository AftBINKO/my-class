from flask import abort, render_template
from flask_login import login_required, current_user

from app.data.functions import check_permission
from app.data.functions import admit as let_it
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
        result = let_it(int(form.id.data), current_user)
        match result:
            case 403:
                data['type'] = 'danger'
                data['message'] = 'Вы не имеете права отмечать данного пользователя.'
            case None:
                data['type'] = 'warning'
                data['message'] = 'Пользователь уже был отмечен как присутствующий, всё в порядке.'
            case True:
                data['type'] = 'success'
                data['message'] = 'Пользователь теперь отмечен как присутствующий.'

    return render_template('admit.html', **data)  # noqa
