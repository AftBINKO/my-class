from flask import redirect, url_for, render_template
from flask_login import current_user

from app.modules.errors import bp


@bp.app_errorhandler(401)
def unauthorized(error):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            return redirect(url_for("auth.finish_register"))
    else:
        return redirect(url_for('auth.login'))


@bp.app_errorhandler(403)
def forbidden(error):
    return render_template("alert.html", title="Недостаточно прав",
                           message="Вам сюда нельзя"), {"Refresh": f"3; url={url_for('home')}"}


@bp.app_errorhandler(404)
def not_found(error):
    return render_template("alert.html", title="Страницы не существует",
                           message="Вы перешли на несуществующую страницу"), {
        "Refresh": f"3; url={url_for('home')}"}


@bp.app_errorhandler(500)
def crash(error):
    return render_template("alert.html", title="Ошибка сервера",
                           message="На сервере произошла ошибка"), {
        "Refresh": f"3; url={url_for('home')}"}


@bp.app_errorhandler(503)
def service_mode(error):
    return render_template("service_mode.html", title="Сервер недоступен", message="Попробуйте вернуться позднее",
                           without_header=True)
