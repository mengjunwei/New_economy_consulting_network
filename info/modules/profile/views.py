from . import profile_blue
from info.utils.common import user_login_data
from flask import render_template, g, jsonify, current_app, redirect, url_for, request, session
from info import response_code, db, constants
from info.utils.file_storage import upload_file


@profile_blue.route('/pic_info', methods=['POST', 'GET'])
@user_login_data
def pic_data():
    '''
    
    :return: 
    '''
    # 1.判断是否登录，若未登录，重定向到首页
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.若请求方法是get，则渲染基本信息界面
    if request.method == 'GET':
        context = {
            'user': user.to_dict() if user else None
        }
        return render_template('news/user_pic_info.html', context=context)

    #3.若请求方法为post，接受参数
    if request.method == 'POST':
        avatar_file = request.files.get('avatar', None)

        #4.校验参数
        if not avatar_file:
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
        try:
            avatar_file_data = avatar_file.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='读取上传图片文件失败')

        #5.上传至七牛云
        try:
            avatar_url = upload_file(avatar_file_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.THIRDERR, errmsg='上传保存图片失败')

        #6.更新头像路径
        user.avatar_url = avatar_url

        #7.同步到数据库
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.DBERR, errmsg='保存图片路径失败')

        data = {
            'avatar_url': constants.QINIU_DOMIN_PREFIX + avatar_url
        }

        #8.返回响应
        return jsonify(errno=response_code.RET.OK, errmsg='头像上传成功', data=data)


@profile_blue.route('/base_info', methods=['POST', 'GET'])
@user_login_data
def base_info():
    '''
    1.判断是否登录，若未登录，重定向到首页
    2.若请求方法是get，则渲染基本信息界面
    3.接受参数
    4.校验参数
    5更改用户数据
    6.同步到数据库
    7.更改状态保持中的session
    :return: 返回响应
    '''
    # 1.判断是否登录，若未登录，重定向到首页
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.若请求方法是get，则渲染基本信息界面
    if request.method == 'GET':
        context = {
            'user':user
        }
        return render_template('news/user_base_info.html', context=context)

    #3.接受参数
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')

    #4.校验参数
    if not all([nick_name, gender]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    #5更改用户数据
    user.nick_name = nick_name
    user.gender = gender
    user.signature = signature

    #6.同步到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='更新数据失败')

    #7.更改状态保持中的session
    session['nick_name'] = nick_name

    #8.返回响应
    return jsonify(errno=response_code.RET.OK, errmsg='更新成功')


@profile_blue.route('/user_info')
@user_login_data
def user_info():
    '''
    
    :return: 
    '''
    #1.判断是否登录，若未登录，重定向到首页
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2.渲染用户界面
    context = {
        'user':user.to_dict() if user else None
    }

    return render_template('news/user.html', context=context)
