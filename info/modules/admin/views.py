from . import admin_blue
from flask import current_app, render_template, redirect, url_for, request, session, g
from info.models import User
from info.utils.common import user_login_data
import time, datetime


@admin_blue.route('/user_count')
@user_login_data
def user_count():
    '''
    
    :return: 
    '''
    # # 1.判断是否是登录用户，若是登录用户
    # user = g.user
    # if not user:
    #     return redirect(url_for('admin/login'))

    #2查询总用户数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    #查询每月新增数
    mouth_count = 0
    # 计算每月开始时间 比如：2018-06-01 00：00：00
    t = time.localtime()
    # 计算每月开始时间字符串
    month_begin = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 计算每月开始时间对象
    month_begin_date = datetime.datetime.strptime(month_begin, '%Y-%m-%d')
    try:
        mouth_count = User.query.filter(User.is_admin == False, User.create_time>month_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    #日新增量
    day_count = 0
    t = time.localtime()
    day_begin = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    day_begin_date = datetime.datetime.strptime(day_begin, '%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    context = {
        'total_count':total_count,
        'mouth_count':mouth_count,
        'day_count':day_count
    }

    return render_template('admin/user_count.html', context=context)

@admin_blue.route('/')
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