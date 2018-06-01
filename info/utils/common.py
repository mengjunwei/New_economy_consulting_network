from flask import session, jsonify, g, current_app
from info import response_code
from info.models import User
from functools import wraps


#过滤器
def do_rank(value):
    if value == 1:
        return 'first'
    elif value == 2:
        return "second"
    elif value == 3:
        return "third"
    else:
        return ""


def user_login_data(view_func):
    wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id', None)
        if not user_id:
            return jsonify(errno=response_code.RET.NODATA, errmsg='用户未登录')
        user = None
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
        g.user = user
        return view_func(*args, **kwargs)
    return wrapper