from . import news_blue
from info.utils.common import user_login_data
from flask import render_template, g, current_app, jsonify, request
from info.models import News
from info import constants, response_code, db


@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    '''
    1，查看用户是否登录
    2,接受参数，判断参数是否合法
    3，根据news_id 查找news对象
    4,查询该用户收藏的新闻列表
    5收藏的增加与取消
    6同步到数据库中
    7返回响应
    :return: 
    '''
    # 1，查看用户是否登录
    user = g.user

    #2,接受参数，判断参数是否合法
    json_dict = request.json
    news_id = json_dict.get('news_id')
    action = json_dict.get('action')
    if not all([news_id, action]):
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')
    if action not in ['cancel_collect', 'collect']:
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    #3，根据news_id 查找news对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻对象错误')
    if not news:
        return jsonify(errno=response_code.RET.NODATA, errmsg='无此新闻')

    #4,查询该用户收藏的新闻列表
    try:
        user_news_list = user.collection_news
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询收藏的新闻列表失败')

    #5收藏的增加与取消
    if action == 'collect':
        if news not in user_news_list:
            user_news_list.append(news)
    else:
        if news in user_news_list:
            user_news_list.remove(news)

    #6同步到数据库中
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='同步收藏失败')

    #7返回响应
    return jsonify(errno=response_code.RET.OK, errmsg='操作成功')


@news_blue.route('/news_detal/<int:news_id>')
@user_login_data
def news_detal(news_id):
    '''
    1，查看用户是否登录
    2，点击排行的显示
    3，根据news_id查询新闻
    4，新闻点击量加1
    :param news_id: 
    :return: 
    '''
    #1，查看用户是否登录
    user = g.user

    #2，点击排行的显示
    news_clicks = []
    try:
        news_clicks = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)


    #3，根据news_id查询新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻数据错误')

    #4，新闻点击量加1
    news.clicks += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='跟新新闻点击量失败')

    #5.判断该新闻是否被该登录用户收藏，以便界面显示

    is_collect = False
    if news in user.collection_news:
        is_collect = True

    context = {
        'user':user,
        'news':news.to_dict(),
        'news_clicks':news_clicks,
        'is_collect':is_collect
    }
    return render_template('news/detail.html', context=context)