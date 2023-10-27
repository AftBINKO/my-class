from flask_login import login_required, logout_user, current_user, login_user
from flask import redirect, url_for, render_template, abort

from string import ascii_letters, digits, punctuation

from app.data.functions import check_permission
from app.data.db_session import create_session
from app.data.models import User, Permission
from app import login_manager

from app.modules.auth.forms import LoginForm, LoginKeyForm, FinishRegisterForm
from app.modules.auth import bp


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()

    user = db_sess.query(User).get(user_id)
    permission = db_sess.query(Permission).filter_by(title="login").first()

    db_sess.close()

    if isinstance(user, User):
        if check_permission(user, permission):
            return user


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for(".login"))


@bp.route('/login', methods=['GET', 'POST'])
@bp.route('/enter_to_class/<int:user_id>/login', methods=['GET', 'POST'])
def login(user_id=None):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            abort(401)
        if user_id:
            return redirect(url_for("qr.enter_to_class", user_id=user_id))
        return redirect(url_for("home"))

    form = LoginForm()
    data = {
        "form": form,
        "message": None,
        "user_id": user_id
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter_by(login=form.login.data.lower()).first()
        db_sess.close()

        if user:
            if user.check_password(form.password.data):  # noqa
                login_user(user, remember=form.remember_me.data)
                if user_id:
                    return redirect(url_for("qr.enter_to_class", user_id=user_id))
                return redirect(url_for("home"))

            data["message"] = "Неверный пароль"

        else:
            data["message"] = "Неверный логин"
    return render_template("login.html", **data)  # noqa


@bp.route('/login_key', methods=['GET', 'POST'])
@bp.route('/enter_to_class/<int:user_id>/login_key', methods=['GET', 'POST'])
def login_with_key(user_id=None):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            abort(401)
        if user_id:
            return redirect(url_for("qr.enter_to_class", user_id=user_id))
        return redirect(url_for("home"))

    form = LoginKeyForm()
    data = {
        "form": form,
        "message": None,
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter_by(key=form.key.data).first()
        db_sess.close()

        if user is not None:
            login_user(user, remember=True)
            return redirect(url_for(".finish_register", user_id=user_id))
        else:
            data["message"] = "Неверный ключ"
    return render_template("login_key.html", **data)  # noqa


@bp.route('/finish_register', methods=['GET', 'POST'])
@bp.route('/enter_to_class/<int:user_id>/finish_register', methods=['GET', 'POST'])
@login_required
def finish_register(user_id=None):
    if current_user.is_registered:
        if user_id:
            return redirect(url_for("qr.enter_to_class", user_id=user_id))
        return redirect(url_for("home"))

    form = FinishRegisterForm()
    data = {
        "form": form,
        "message": None
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).get(current_user.id)

        user_login = form.login.data.lower()
        user_password = form.password.data
        user_password_again = form.password_again.data

        if not all([symbol in ascii_letters + digits for symbol in user_login]):
            data['message'] = "Логин содержит некорректные символы"
        elif not all(
                [symbol in ascii_letters + digits + punctuation for symbol in user_password]):
            data['message'] = "Пароль содержит некорректные символы."
        elif user_password != user_password_again:
            data['message'] = "Пароли не совпадают"
        else:
            user.login = user_login
            user.set_password(password=user_password)
            user.is_registered = True
            user.delete_key()

            db_sess.commit()
            db_sess.close()

            if user_id:
                return redirect(url_for("qr.enter_to_class", user_id=user_id))

            return redirect(url_for("home"))
        db_sess.close()
    return render_template("finish_register.html", **data)  # noqa
