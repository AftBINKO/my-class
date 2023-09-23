from flask import redirect, url_for, render_template

from app.modules.errors import bp


@bp.app_errorhandler(401)
def unauthorized(error):
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
