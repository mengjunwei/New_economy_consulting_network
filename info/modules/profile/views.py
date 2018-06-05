from . import profile_blue
from info.utils.common import user_login_data
from flask import render_template, g, jsonify, current_app, redirect, url_for, request, session
from info import response_code, db, constants
from info.utils.file_storage import upload_file
from info.models import Category, News


@profile_blue.route('/news_release', methods=['POST', 'GET'])
@user_login_data
def user_news_release():
    '''
    1.判断是否登录，若未登录，重定向到首页
    2若请求方式为get请求，则渲染模板
    3.若为post请求，则接受参数
    3.1校验参数
    3.2将图片上传至七牛云
    3.3创建新闻模型对象
    3.4同步至数据库中
    :return: 返回响应结果
    '''
    # 1.判断是否登录，若未登录，重定向到首页
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2若请求方式为get请求，则渲染模板
    if request.method == 'GET':
        category = []
        try:
            category = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        category.pop(0)
        context = {
            'categorys':category
        }
        return render_template('news/user_news_release.html', context=context)

    #3.若为post请求，则接受参数
    if request.method == 'POST':
        title = request.form.get('title')
        source = user.nick_name
        category_id = request.form.get('category_id')
        digest = request.form.get('digest')
        index_image = request.files.get('index_image')
        content = request.form.get('content')

        #3.1校验参数
        if not all([title, category_id, digest, index_image, content]):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')
        try:
            index_image_data = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='读取图片失败')

        #3.2将图片上传至七牛云
        try:
            key = upload_file(index_image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=response_code.RET.THIRDERR, errmsg='上传至云服务错误')

        #3.3创建新闻模型对象
        news = News()
        news.title = title
        news.category_id = category_id
        news.digest = digest
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.content = content
        news.source = source
        news.status = 1

        #3.4同步至数据库中
        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=response_code.RET.DBERR, errmsg='保存新闻失败')

        #3.5返回响应结果
        return jsonify(errno=response_code.RET.OK, errmsg='上传新闻成功')


@profile_blue.route('/collection_info')
@user_login_data
def collection_info():
    '''
    1.判断是否登录，若未登录，重定向到首页
    2.接受参数
    3.校验参数
    4.根据查找页进行数据的分页查找
    5.返回数据
    6.渲染模板
    :return: 
    '''
    #1.判断是否登录，若未登录，重定向到首页
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    #2接受参数
    page = request.args.get('p', 1)

    #3校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    current_page = 1
    total_page = 1
    collections = []
    #4.根据查找页进行数据的分页查找
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        collections = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    #5.返回数据
    collections_dict_list = []
    for collection in collections:
        collections_dict_list.append(collection.to_basic_dict())
    context = {
        'current_page':current_page,
        'total_page':total_page,
        'collections':collections_dict_list
    }

    #6渲染模板
    return render_template('news/user_collection.html', context=context)


@profile_blue.route('/pass_info', methods=['POST', 'GET'])
@user_login_data
def pass_info():
    '''
    1.判断是否登录，若未登录，重定向到首页
    2.若请求方法是get，则渲染基本信息界面
    3.若请求方法为post，接受参数
    3.1校验参数
    3.2检验密码是否正确
    3.3将新密码同步到数据库
    :return: 返回响应
    '''
    # 1.判断是否登录，若未登录，重定向到首页
    user = g.user
    if not user:
        return redirect(url_for('index.index'))

    # 2.若请求方法是get，则渲染基本信息界面
    if request.method == 'GET':
        context = {
            'user': user
        }
        return render_template('news/user_pass_info.html', context=context)

    # 3.若请求方法为post，接受参数
    if request.method == 'POST':
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')

        #3.1校验参数
        if not all([old_password, new_password]):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='缺少参数')

        #3.2检验密码是否正确
        if not user.check_passowrd(old_password):
            return jsonify(errno=response_code.RET.PARAMERR, errmsg='密码或账号输入错误')

        #3.3将新密码同步到数据库
        user.password = new_password
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=response_code.RET.DBERR, errmsg='保存密码失败')

        #3.4返回响应
        return jsonify(errno=response_code.RET.OK, errmsg='修改密码成功')


@profile_blue.route('/pic_info', methods=['POST', 'GET'])
@user_login_data
def pic_info():
    '''
    1.判断是否登录，若未登录，重定向到首页
    2.若请求方法是get，则渲染基本信息界面
    3.若请求方法为post，接受参数
    #4.校验参数
    5.上传至七牛云
    6.更新头像路径
    7.同步到数据库
    :return: 返回响应
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
