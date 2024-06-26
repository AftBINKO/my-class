from flask import redirect, url_for, abort, render_template, current_app, send_from_directory, session, request
from flask_login import login_required, current_user

from os import path

from app.data.functions import admit as let_it, get_titles_roles
from app.data.db_session import create_session
from app.data.functions import generate_qrs
from app.data.models import User, School
from app.modules.qr import bp
from app import app


@bp.route('/admit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admit(user_id):
    session['url'] = request.base_url

    if not current_user.is_registered:
        abort(401)

    if request.method == 'POST':
        result = let_it(user_id, current_user)
        match result:
            case 403:
                abort(403)
            case 404:
                abort(404)
            case None:
                return redirect(url_for(".enter_error"))

        return redirect(url_for(".enter_success"))

    result = let_it(user_id, current_user, only_check_permission=True)
    match result:
        case 403:
            abort(403)
        case 404:
            abort(404)
        case None:
            return redirect(url_for(".enter_error"))
        case True:
            db_sess = create_session()

            user = db_sess.query(User).get(user_id)
            roles_titles = get_titles_roles(user)

            data = {
                "user": user,
                "roles_titles": roles_titles,
            }
            if user.school_id:
                data["school"] = db_sess.query(School).get(user.school_id)

            db_sess.close()

            return render_template("admit.html", **data)


@bp.route('/admit/success')
def enter_success():
    return render_template("alert.html", title="Успешно",
                           message="Пользователь теперь отмечен как присутствующий"), {
        "Refresh": f"3; url={url_for('admit.admit')}"}


@bp.route('/admit/error')
def enter_error():
    return render_template("alert.html", title="Пользователь уже отмечен",
                           message="Всё в порядке! Пользователь уже был отмечен ранее"), {
        "Refresh": f"3; url={url_for('admit.admit')}"}


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

    result = generate_qrs(user, current_user, qrcodes_path, ignore_exists=False)
    if result == 403:
        abort(403)

    return redirect(session.pop('url', url_for("profile.profile", user_id=user_id)))
