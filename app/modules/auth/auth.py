from flask_login import login_required, logout_user, current_user, login_user
from flask import redirect, url_for, render_template

from string import ascii_letters, digits, punctuation

from app.data.functions import allowed_permission
from app.data.db_session import create_session
from app.data.models import User, Permission
from app import login_manager

from app.modules.auth.forms import LoginForm, LoginKeyForm, FinishRegisterForm
from app.modules.auth import bp


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()

    user = db_sess.query(User).get(user_id)
    permission = db_sess.query(Permission).filter(Permission.title == "login").first()  # noqa

    db_sess.close()

    if isinstance(user, User):
        if allowed_permission(user, permission):
            return user


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for(".login"))


@bp.route('/login', methods=['GET', 'POST'])
@bp.route('/enter_to_class/<class_id>/login', methods=['GET', 'POST'])
def login(class_id=None):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            return redirect(url_for(".finish_register"))
        return redirect(url_for("profile"))

    form = LoginForm()
    data = {
        "form": form,
        "message": None,
        "class_id": class_id
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.login == form.login.data.lower()).first()
        db_sess.close()

        if user:
            if user.check_password(form.password.data):  # noqa
                login_user(user, remember=form.remember_me.data)
                if class_id:
                    return redirect(url_for("enter_to_class", class_id=class_id))
                return redirect(url_for("home"))

            data["message"] = "Неверный пароль"

        else:
            data["message"] = "Неверный логин"
    return render_template("login.html", **data)  # noqa


@bp.route('/login_key', methods=['GET', 'POST'])
@bp.route('/enter_to_class/<class_id>/login_key', methods=['GET', 'POST'])
def login_with_key(class_id=None):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            return redirect(url_for(".finish_register"))
        return redirect(url_for("profile"))

    form = LoginKeyForm()
    data = {
        "form": form,
        "message": None,
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.key == form.key.data).first()
        db_sess.close()

        if user is not None:
            login_user(user, remember=True)
            return redirect(url_for(".finish_register", class_id=class_id))
        else:
            data["message"] = "Неверный ключ"
    return render_template("login_key.html", **data)  # noqa


@bp.route('/finish_register', methods=['GET', 'POST'])
@bp.route('/enter_to_class/<class_id>/finish_register', methods=['GET', 'POST'])
@login_required
def finish_register(class_id=None):
    form = FinishRegisterForm()
    data = {
        "form": form,
        "message": None
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

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
            user.set_password(user_password)  # noqa
            user.is_registered = True
            user.delete_key()  # noqa

            db_sess.commit()
            db_sess.close()

            if class_id:
                return redirect(url_for("enter_to_class", class_id=class_id))

            return redirect(url_for("home"))
        db_sess.close()
    return render_template("finish_register.html", **data)  # noqa
