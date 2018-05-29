from . import passport_blue
from info.utils.captcha.captcha import captcha
from flask import request, jsonify, make_response, abort, current_app, session
from info import response_code, redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
import re, random, datetime


@passport_blue.route('/logout')
def logout():
    '''
    1,删除session中的数据
    :return: 
    '''
    try:
        session.pop('user_id', None)
        session.pop('nick_name', None)
        session.pop('mobile', None)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='删除session数据失败')

    return jsonify(errno=response_code.RET.OK, errmsg='退出登录成功')


@passport_blue.route('/login', methods=['POST'])
def login():
    '''
    1,接受参数（手机号，密码明文）
    2，判断手机号，密码是否为空
    3，验证手机号格式是否正确
    4，查询数据库，根据手机号
    5,手机号存在，查询密码是否一致
    6.将登录时间同步至mysql数据库
    7.将登录状态redis数据库，
    :return: 响应返回数据
    '''
    # 1,接受参数（手机号，密码）
    json_dict = request.json
    mobile = json_dict.get('mobile')
    password = json_dict.get('password')

    #2，判断手机号，密码是否为空
    if not all([mobile, password]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数缺少')

    # 3，验证手机号格式是否正确
    if not re.match(r'^1[345678]\d{9}$', mobile):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='手机号格式错误')

    #4查询数据库，根据手机号
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询用户数据失败')
    if not user:
        return jsonify(errno=response_code.RET.DATAERR, errmsg='手机或密码错误')

    #手机号存在，查询密码是否一致
    if not user.check_passowrd(password):
        return jsonify(errno=response_code.RET.DATAERR, errmsg='手机或密码错误')

    #更新mysql数据库中登录时间，
    user.last_login = datetime.datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='更新登录时间失败')

    #  将登录状态redis数据库
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = mobile

    #响应登录结果
    return jsonify(errno=response_code.RET.OK, errmsg='登录成功')


@passport_blue.route('/register', methods=['POST'])
def register():
    '''
    1,接受参数（手机号，短信验证码，密码）
    2，判断参数是否为空
    3，验证手机号格式是否正确
    4，根据手机号查询短信验证码
    5.判断短信验证码是否一致
    6.创建user对象，添加到数据库中
    7，状态保持，注册即登录
    :return: 返回响应
    '''
    #接受参数（手机号，短信验证码，密码）
    json_dict = request.json
    mobile = json_dict.get('mobile')
    smscode_client = json_dict.get('smscode')
    password = json_dict.get('password')

    # 2，判断参数是否为空
    if not all([mobile, smscode_client, password]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    # 3，验证手机号格式是否正确
    if not re.match(r'^1[345678]\d{9}$', mobile):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='手机号格式错误')

    #4，根据手机号查询短信验证码
    try:
        smscode_server = redis_store.get('sms:' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询短信验证码失败')
    if not smscode_server:
        return jsonify(errno=response_code.RET.NODATA, errmsg='短信验证码过期')

    #5.判断短信验证码是否一致
    if smscode_server != smscode_client:
        return jsonify(errno=response_code.RET.DATAERR, errmsg='验证码输入有误')

    #创建user对象，添加到数据库中
    user = User()
    user.mobile = int(mobile)
    user.nick_name = mobile
    user.password = password
    user.last_login = datetime.datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=response_code.RET.DBERR, errmsg='保存数据库失败')

    #7，状态保持，注册即登录
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile

    #8响应
    return jsonify(errno=response_code.RET.OK, errmsg='注册成功')


@passport_blue.route('/sms_code', methods=['POST'])
def get_sms_code():
    '''
    1.接受参数（UUID，图片验证码，手机号）
    2.判断手机号，图片验证码，UUID是否为空
    3.验证手机号码是否违规
    4.根据UUID查询数据库中的图片内容
    5.判断图片验证码是否 相等
    6.发送短信验证码请求
    7.将短信验证码存入数据库中
    :return: 响应结果
    '''
    # 1.接受参数（UUID，图片验证码，手机号）
    json_dict = request.json
    mobile = json_dict.get('mobile')
    image_code_client = json_dict.get('image_code')
    image_code_id = json_dict.get('image_code_id')

    # 2.判断手机号，图片验证码，UUID是否为空
    if not all([mobile, image_code_client, image_code_id]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    #3验证手机号码是否违规
    if not re.match(r'^1[345678]\d{9}$', mobile):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='手机号格式错误')

    #4.根据UUID查询数据库中的图片内容
    try:
        image_code_server = redis_store.get('imageCodeId:' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询图片验证码失败')
    if not image_code_server:
        return jsonify(errno=response_code.RET.NODATA, errmsg='图片验证码过期')

    #5.判断图片验证码是否 相等
    if image_code_client.lower() != image_code_server.lower():
        return jsonify(errno=response_code.RET.DATAERR, errmsg='图片验证输入错误')

    #发送短信验证码请求
    smscode = '%06d' % random.randint(0,999999)
    current_app.logger.error(smscode)
    # result = CCP().send_template_sms(mobile, [smscode, 5], 1)
    # if result != 0:
    #     return jsonify(errno=response_code.RET.THIRDERR, errmsg='短信验证码发送失败')

    #将短信验证码存入数据库中
    try:
        redis_store.set('sms:' + mobile, smscode, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='短信验证码存储失败')

    #响应结果
    return jsonify(errno=response_code.RET.OK, errmsg='短信验证码发送成功')


@passport_blue.route('/image_code')
def get_image_code():
    '''
    1.接受请求，
    2.判断UUID是否为空
    3.若不为空，生成图片验证码
    4.将生成的图片信息存储在redis数据库中
    5.返回响应
    :return: 
    '''
    imageCodeId = request.args.get('imageCodeId')
    if not imageCodeId:
        abort(403)
    name, text, image = captcha.generate_captcha()
    try:
        redis_store.set('imageCodeId:' + imageCodeId, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpg'
    return image


