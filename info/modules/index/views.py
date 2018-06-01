from . import index_blue
from flask import render_template, current_app, session, jsonify,request
from info.models import User, News
from info import constants, response_code


@index_blue.route('/news_list')
def index_news_list():
    '''
    1,接受参数（当前页，每页多少条，新闻分类
    :return: 
    '''
    # http://127.0.0.1:5000/news_list?cid=1&page=1&per_page=10
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_pape = request.args.get('per_pape', '10')

    try:
        cid = int(cid)
        page = int(page)
        per_pape = int(per_pape)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.PARAMERR, errmsg='参数错误')

    try:
        if cid == 1:
            paginate = News.query.order_by(News.create_time.desc()).paginate(page, per_pape, False)
        else:
            paginate = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page, per_pape, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=response_code.RET.DBERR, errmsg='查询新闻数据失败')

    #构造新闻响应数据
    new_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.pages

    news_dict_list = []
    for news in new_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        'news_dict_list': news_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }
    return jsonify(errno=response_code.RET.OK, errmsg='OK', data=data)


@index_blue.route('/')
def index():
    '''
    1,查询用户登录状态
    2，点击排行数据的显示
    :return: 
    '''
    user_id = session.get('user_id', None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
    news_click = None
    try:
        news_click = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    content = {
        'user':user,
        'news_click':news_click
    }
    return render_template('news/index.html', content=content)


@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')