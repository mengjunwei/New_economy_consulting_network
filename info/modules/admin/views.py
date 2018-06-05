from . import admin_blue
from info.utils.common import user_login_data
from flask import g, current_app, render_template, redirect, url_for, request


@admin_blue.route('/login', methods=['POST', 'GET'])
@user_login_data
def login():
    '''
    
    :return: 
    '''
    #1.判断用户是否处于登录状态
    user = g.user
    if not user:
        return redirect(url_for('admin.login'))

    #2.若为get请求，则渲染界面
    if request.method == 'GET':
        return render_template('admin/login.html')
