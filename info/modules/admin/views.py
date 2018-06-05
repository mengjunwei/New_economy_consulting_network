from . import admin_blue
from flask import current_app, render_template, redirect, url_for, request, session, g
from info.models import User
from info.utils.common import user_login_data

@admin_blue.route('/index')
@user_login_data
def index():
    '''
    
    :return: 
    '''
    #1.判断是否是登录用户，若是登录用户
    user = g.user
    if not user:
        return redirect(url_for('admin/login'))

    context = {
        'user':user.to_dict() if user else None
    }
    return render_template('admin/index.html', context=context)


@admin_blue.route('/login', methods=['POST', 'GET'])
def login():
    '''
    #1.若为get请求，则渲染界面
    2.若为post请求，则接受参数
    3,校验参数
    4.校验用户是否存在
    5校验用户名和面是否正确
    6.写入状态保持
    :return: 跳转到登录页面
    '''
    #1.若为get请求，则渲染界面
    if request.method == 'GET':
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)
        if user_id and is_admin:
            return render_template(url_for('admin.index'))
        return render_template('admin/login.html')

    #2.若为post请求，则接受参数
    if request.method == 'POST':
        password = request.form.get('password')
        nick_name = request.form.get('username')

        #3,校验参数
        if not all([password, nick_name]):
            return render_template('admin/login.html', errmsg='缺少参数')

        #4.校验用户是否存在
        try:
            user = User.query.filter(User.nick_name == nick_name).first()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/login.html', errmsg='查询用户失败')

        #5校验用户名和面是否正确
        if not user:
            return render_template('admin/login.html', errmsg='用户名或密码错误')
        if not user.check_passowrd(password):
            return render_template('admin/login.html', errmsg='用户名或密码错误')

        #6.写入状态保持
        session['user_id'] = user.id
        session['nick_name'] = user.nick_name
        session['mobile'] = user.mobile
        session['is_admin'] = user.is_admin

        #7.跳转到首页
        return redirect(url_for('admin.index'))