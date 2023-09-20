from flask_login import current_user, login_required
from flask import redirect, url_for, abort

from app import app

from .data.functions import allowed_permission
from .data.db_session import create_session
from .data.models import *


@app.route('/')
@login_required
def home():
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()
    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    status = max(list(map(int, current_user.statuses.split(", "))))
    db_sess.close()

    if allowed_permission(current_user, permission):
        return redirect(url_for("admin_tools.admin_panel"))

    if not current_user.school_id:
        abort(403)

    if status in [1, 3]:
        if current_user.class_id:
            return redirect(url_for("schools.school.classes.school_class.class_info",
                                    school_id=current_user.school_id, class_id=current_user.class_id))

    return redirect(url_for("schools.school.school_info", school_id=current_user.school_id))
