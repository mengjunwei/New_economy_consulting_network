from flask import Blueprint, session, request, redirect, url_for


admin_blue = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


@admin_blue.before_request
def check_admin():
    is_admin = session.get('is_admin', False)
    if not request.url.endswith('/admin/login') and not is_admin:
        return redirect(url_for('index.index'))