from . import passport_blue
from info.utils.captcha.captcha import captcha
from flask import request, jsonify, make_response, abort, current_app
from info import response_code, redis_store, constants


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


