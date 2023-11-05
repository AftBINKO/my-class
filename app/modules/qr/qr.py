from flask import redirect, url_for, abort, render_template, current_app, send_from_directory, session, request
from flask_login import login_required, current_user

from qrcode import make as make_qr
from datetime import datetime
from pytz import timezone
from os import path

from app.data.functions import check_role, check_permission, get_roles, get_max_role, get_min_role, generate_qrs
from app.data.functions import admit as let_it
from app.data.models import User, Permission, Class
from app.data.db_session import create_session
from app.modules.qr import bp
from app import app


@bp.route('/admit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admit(user_id):
    session['url'] = request.base_url

    if not current_user.is_registered:
        abort(401)

    result = let_it(user_id, current_user)
    match result:
        case 403:
            abort(403)
        case None:
            return redirect(url_for(".enter_error"))

    return redirect(url_for(".enter_success"))


@bp.route('/admit/success')
def enter_success():
    return render_template("alert.html", title="Успешно",
                           message="Пользователь теперь отмечен как присутствующий"), {
        "Refresh": f"3; url={url_for('home')}"}


@bp.route('/admit/error')
def enter_error():
    return render_template("alert.html", title="Пользователь уже отмечен",
                           message="Всё в порядке! Пользователь уже был отмечен ранее"), {
        "Refresh": f"3; url={url_for('home')}"}


@bp.route('/generate_qr/<int:user_id>', methods=['GET', 'POST'])
@login_required
def generate_qrcode(user_id):
    if not current_user.is_registered:
        abort(401)

    db_sess = create_session()  # noqa

    user = db_sess.query(User).get(user_id)
    if not user:
        abort(404)

    qrcodes_path = path.join(current_app.root_path,
                             path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "users")))

    result = generate_qrs(user, current_user, qrcodes_path)
    if result == 403:
        abort(403)

    return redirect(session.pop('url', url_for("profile.profile", user_id=user_id)))
