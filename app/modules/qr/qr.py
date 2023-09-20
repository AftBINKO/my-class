from flask import redirect, url_for, abort, render_template, current_app, send_from_directory
from flask_login import login_required, current_user

from qrcode import make as make_qr
from datetime import datetime
from pytz import timezone
from os import path

from app.data.functions import check_status, allowed_permission
from app.data.models import User, Permission, Class
from app.data.db_session import create_session
from app.modules.qr import bp
from app import app


@bp.route('/enter_to_class/<class_id>', methods=['GET', 'POST'])
def enter_to_class(class_id):
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", class_id=class_id))

    class_id = int(class_id)

    db_sess = create_session()

    if not (current_user.class_id == class_id and check_status(current_user, "Ученик")):
        db_sess.close()
        abort(403)

    user = db_sess.query(User).filter(User.id == current_user.id).first()

    if user.is_arrived:
        return redirect(url_for("enter_error"))

    user.is_arrived = True
    arrival_time = datetime.now().astimezone(timezone("Europe/Moscow"))

    user.arrival_time = arrival_time

    list_times = []
    if user.list_times:
        list_times = user.list_times.split(', ')
    list_times.append(arrival_time.strftime("%Y-%m-%d %H:%M:%S.%f"))

    user.list_times = ", ".join(list_times)

    db_sess.commit()
    db_sess.close()

    return redirect(url_for("enter_success"))


@bp.route('/enter_to_class/success')
def enter_success():
    return render_template("alert.html", title="Успешный вход",
                           message="Можете заходить в класс, вы отмечены, как присутствующий"), {
        "Refresh": f"3; url={url_for('home')}"}


@bp.route('/enter_to_class/error')
def enter_error():
    return render_template("alert.html", title="Вы уже отмечены",
                           message="Вам сейчас не нужно отмечаться, вы уже отмечены в системе как присутствующий"), {
        "Refresh": f"3; url={url_for('home')}"}


@bp.route('/get_qr/<class_id>', methods=['GET', 'POST'])
@login_required
def generate_qrcode(class_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    class_id = int(class_id)
    school_id = db_sess.query(Class).filter(Class.id == class_id).first().school_id  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(405)

    uploads = path.join(current_app.root_path, path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "classes")))

    name = f"class_{class_id}.png"
    qr = make_qr(url_for(".enter_to_class", class_id=class_id, _external=True))
    qr.save(path.join(uploads, name))

    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa
    school_class.qr = name
    db_sess.commit()

    db_sess.close()

    return redirect(url_for("schools.school.classes.school_class.class_info",
                            school_id=school_id, class_id=class_id))


@bp.route('/<class_id>', methods=['GET', 'POST'])
@login_required
def view_qrcode(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    uploads = path.join(current_app.root_path, path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "classes")))

    db_sess = create_session()
    qr = db_sess.query(Class).filter(Class.id == class_id).first().qr  # noqa
    db_sess.close()
    if qr is None:
        abort(404)

    return send_from_directory(directory=uploads, path=qr)
